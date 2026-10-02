-- =====================================================================
-- JobSense - MySQL 8 schema
-- Run against an empty database:
--   CREATE DATABASE jobsense CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
--   mysql -u <user> -p jobsense < database/schema.sql
-- The script is idempotent for a fresh install (drops tables in dependency order).
-- =====================================================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS career_recommendations;
DROP TABLE IF EXISTS career_skills;
DROP TABLE IF EXISTS career_paths;
DROP TABLE IF EXISTS learning_resources;
DROP TABLE IF EXISTS applications;
DROP TABLE IF EXISTS saved_jobs;
DROP TABLE IF EXISTS job_matches;
DROP TABLE IF EXISTS jobs;
DROP TABLE IF EXISTS candidate_skills;
DROP TABLE IF EXISTS resumes;
DROP TABLE IF EXISTS user_interests;
DROP TABLE IF EXISTS user_profiles;
DROP TABLE IF EXISTS user_sessions;
DROP TABLE IF EXISTS skill_taxonomy;
DROP TABLE IF EXISTS users;

SET FOREIGN_KEY_CHECKS = 1;

-- ---------------------------------------------------------------------
-- 1. USERS
-- ---------------------------------------------------------------------
CREATE TABLE users (
    user_id        INT UNSIGNED NOT NULL AUTO_INCREMENT,
    name           VARCHAR(120) NOT NULL,
    email          VARCHAR(255) NOT NULL,
    password_hash  VARCHAR(255) NOT NULL,
    role           ENUM('candidate', 'admin') NOT NULL DEFAULT 'candidate',
    is_active      TINYINT(1) NOT NULL DEFAULT 1,
    created_at     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id),
    UNIQUE KEY uq_users_email (email),
    KEY idx_users_role (role)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Server-side sessions: only a SHA-256 hash of the bearer token is stored.
CREATE TABLE user_sessions (
    session_id     INT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id        INT UNSIGNED NOT NULL,
    token_hash     CHAR(64) NOT NULL,
    created_at     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at     DATETIME NOT NULL,
    PRIMARY KEY (session_id),
    UNIQUE KEY uq_sessions_token (token_hash),
    KEY idx_sessions_user (user_id),
    KEY idx_sessions_expires (expires_at),
    CONSTRAINT fk_sessions_user FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Candidate profile details (1:1 with users)
CREATE TABLE user_profiles (
    user_id              INT UNSIGNED NOT NULL,
    headline             VARCHAR(160) NULL,
    experience_years     DECIMAL(4,1) NULL,
    experience_summary   TEXT NULL,
    education            TEXT NULL,
    location             VARCHAR(120) NULL,
    preferred_locations  VARCHAR(500) NULL,
    remote_preference    ENUM('any', 'remote', 'hybrid', 'onsite') NOT NULL DEFAULT 'any',
    social_links         TEXT NULL,          -- JSON object: {"linkedin": "https://...", ...}
    avatar_image         MEDIUMTEXT NULL,    -- small data:image/... URL (resized client-side)
    avatar_color         VARCHAR(20) NULL,   -- colour key for the initials avatar
    updated_at           TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id),
    CONSTRAINT fk_profiles_user FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Candidate interests (secondary career-recommendation signal)
CREATE TABLE user_interests (
    interest_id  INT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id      INT UNSIGNED NOT NULL,
    interest     VARCHAR(60) NOT NULL,
    created_at   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (interest_id),
    UNIQUE KEY uq_user_interest (user_id, interest),
    CONSTRAINT fk_interests_user FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- Skill taxonomy (reference data used by the skill extractor / skills API)
-- ---------------------------------------------------------------------
CREATE TABLE skill_taxonomy (
    taxonomy_id  INT UNSIGNED NOT NULL AUTO_INCREMENT,
    skill_name   VARCHAR(80) NOT NULL,
    category     VARCHAR(60) NOT NULL,
    aliases      TEXT NULL,
    PRIMARY KEY (taxonomy_id),
    UNIQUE KEY uq_taxonomy_skill (skill_name),
    KEY idx_taxonomy_category (category)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- 2. RESUMES
-- ---------------------------------------------------------------------
CREATE TABLE resumes (
    resume_id          INT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id            INT UNSIGNED NOT NULL,
    file_name          VARCHAR(255) NOT NULL,          -- original (display) name, sanitised
    file_type          ENUM('pdf', 'docx') NOT NULL,
    file_path          VARCHAR(255) NOT NULL,          -- server-generated storage name
    file_size          INT UNSIGNED NOT NULL DEFAULT 0,
    extracted_text     MEDIUMTEXT NULL,
    processed_text     MEDIUMTEXT NULL,                -- NLP-normalised text used for TF-IDF
    education          TEXT NULL,                      -- JSON array of detected education lines
    experience         TEXT NULL,                      -- JSON array of detected experience lines
    experience_years   DECIMAL(4,1) NULL,
    status             ENUM('uploaded', 'processing', 'processed', 'failed') NOT NULL DEFAULT 'uploaded',
    error_message      VARCHAR(255) NULL,
    is_active          TINYINT(1) NOT NULL DEFAULT 1,
    uploaded_at        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    processed_at       DATETIME NULL,
    PRIMARY KEY (resume_id),
    KEY idx_resumes_user (user_id, is_active),
    CONSTRAINT fk_resumes_user FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- 3. CANDIDATE_SKILLS
-- ---------------------------------------------------------------------
CREATE TABLE candidate_skills (
    skill_id               INT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id                INT UNSIGNED NOT NULL,
    skill_name             VARCHAR(80) NOT NULL,       -- display name
    normalized_skill_name  VARCHAR(80) NOT NULL,       -- lower-case canonical key
    source                 ENUM('resume', 'manual') NOT NULL DEFAULT 'resume',
    created_at             TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (skill_id),
    UNIQUE KEY uq_candidate_skill (user_id, normalized_skill_name),
    KEY idx_candidate_skills_name (normalized_skill_name),
    CONSTRAINT fk_candidate_skills_user FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- 4. JOBS
-- ---------------------------------------------------------------------
CREATE TABLE jobs (
    job_id            INT UNSIGNED NOT NULL AUTO_INCREMENT,
    external_job_id   VARCHAR(255) NOT NULL,
    title             VARCHAR(255) NOT NULL,
    company           VARCHAR(255) NOT NULL,
    location          VARCHAR(255) NULL,
    country           VARCHAR(8) NULL,
    description       MEDIUMTEXT NULL,
    processed_text    MEDIUMTEXT NULL,                 -- NLP-normalised description (computed once at ingest)
    job_url           VARCHAR(1000) NULL,
    job_url_hash      CHAR(64) NULL,                   -- SHA-256 of job_url for de-duplication
    employment_type   VARCHAR(60) NULL,
    remote            TINYINT(1) NOT NULL DEFAULT 0,
    required_skills   TEXT NULL,                       -- JSON array of normalised skills
    min_experience_years DECIMAL(4,1) NULL,
    source            VARCHAR(40) NOT NULL,            -- 'jsearch' | 'mock' | 'admin'
    publisher         VARCHAR(120) NULL,
    posted_at         DATETIME NULL,
    fetched_at        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (job_id),
    UNIQUE KEY uq_jobs_external (source, external_job_id),
    KEY idx_jobs_url_hash (job_url_hash),
    KEY idx_jobs_posted (posted_at),
    KEY idx_jobs_fetched (fetched_at),
    KEY idx_jobs_source (source)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- 5. JOB_MATCHES
-- ---------------------------------------------------------------------
CREATE TABLE job_matches (
    match_id          INT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id           INT UNSIGNED NOT NULL,
    job_id            INT UNSIGNED NOT NULL,
    text_similarity   DECIMAL(5,2) NOT NULL,           -- 0-100 (TF-IDF cosine similarity x 100)
    skill_match       DECIMAL(5,2) NULL,               -- 0-100, NULL when job lists no skills
    final_score       DECIMAL(5,2) NOT NULL,           -- 0-100
    matched_skills    TEXT NULL,                       -- JSON array
    missing_skills    TEXT NULL,                       -- JSON array
    calculated_at     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (match_id),
    UNIQUE KEY uq_match_user_job (user_id, job_id),
    KEY idx_matches_user_score (user_id, final_score),
    CONSTRAINT fk_matches_user FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE,
    CONSTRAINT fk_matches_job FOREIGN KEY (job_id) REFERENCES jobs (job_id) ON DELETE CASCADE,
    CONSTRAINT chk_match_final CHECK (final_score BETWEEN 0 AND 100)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- 6. SAVED_JOBS
-- ---------------------------------------------------------------------
CREATE TABLE saved_jobs (
    saved_id   INT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id    INT UNSIGNED NOT NULL,
    job_id     INT UNSIGNED NOT NULL,
    saved_at   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (saved_id),
    UNIQUE KEY uq_saved_user_job (user_id, job_id),
    CONSTRAINT fk_saved_user FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE,
    CONSTRAINT fk_saved_job FOREIGN KEY (job_id) REFERENCES jobs (job_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- 7. APPLICATIONS
-- ---------------------------------------------------------------------
CREATE TABLE applications (
    application_id  INT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id         INT UNSIGNED NOT NULL,
    job_id          INT UNSIGNED NOT NULL,
    status          ENUM('Saved', 'Applied', 'Interview', 'Offer', 'Rejected', 'Withdrawn') NOT NULL DEFAULT 'Saved',
    applied_date    DATE NULL,
    notes           TEXT NULL,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (application_id),
    UNIQUE KEY uq_application_user_job (user_id, job_id),
    KEY idx_applications_status (status),
    CONSTRAINT fk_applications_user FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE,
    CONSTRAINT fk_applications_job FOREIGN KEY (job_id) REFERENCES jobs (job_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- 8. CAREER_PATHS
-- ---------------------------------------------------------------------
CREATE TABLE career_paths (
    career_id      INT UNSIGNED NOT NULL AUTO_INCREMENT,
    career_name    VARCHAR(120) NOT NULL,
    description    TEXT NOT NULL,
    interest_area  VARCHAR(60) NULL,                   -- links to a candidate interest
    created_at     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (career_id),
    UNIQUE KEY uq_career_name (career_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- 9. CAREER_SKILLS
-- importance: 3 = core, 2 = important, 1 = nice to have
-- ---------------------------------------------------------------------
CREATE TABLE career_skills (
    career_skill_id  INT UNSIGNED NOT NULL AUTO_INCREMENT,
    career_id        INT UNSIGNED NOT NULL,
    skill_name       VARCHAR(80) NOT NULL,
    importance       TINYINT UNSIGNED NOT NULL DEFAULT 2,
    PRIMARY KEY (career_skill_id),
    UNIQUE KEY uq_career_skill (career_id, skill_name),
    KEY idx_career_skills_name (skill_name),
    CONSTRAINT fk_career_skills_career FOREIGN KEY (career_id) REFERENCES career_paths (career_id) ON DELETE CASCADE,
    CONSTRAINT chk_career_skill_importance CHECK (importance BETWEEN 1 AND 3)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- 10. CAREER_RECOMMENDATIONS
-- ---------------------------------------------------------------------
CREATE TABLE career_recommendations (
    recommendation_id  INT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id            INT UNSIGNED NOT NULL,
    career_id          INT UNSIGNED NOT NULL,
    match_score        DECIMAL(5,2) NOT NULL,
    skill_alignment    DECIMAL(5,2) NOT NULL,
    text_similarity    DECIMAL(5,2) NOT NULL DEFAULT 0,
    interest_match     TINYINT(1) NOT NULL DEFAULT 0,
    matched_skills     TEXT NULL,                      -- JSON array
    missing_skills     TEXT NULL,                      -- JSON array
    reasons            TEXT NULL,                      -- JSON array of explanation strings
    calculated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (recommendation_id),
    UNIQUE KEY uq_career_rec_user (user_id, career_id),
    KEY idx_career_rec_score (user_id, match_score),
    CONSTRAINT fk_career_rec_user FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE,
    CONSTRAINT fk_career_rec_career FOREIGN KEY (career_id) REFERENCES career_paths (career_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- 11. LEARNING_RESOURCES
-- ---------------------------------------------------------------------
CREATE TABLE learning_resources (
    resource_id    INT UNSIGNED NOT NULL AUTO_INCREMENT,
    skill_name     VARCHAR(80) NOT NULL,
    resource_name  VARCHAR(200) NOT NULL,
    resource_url   VARCHAR(500) NOT NULL,
    description    VARCHAR(500) NULL,
    resource_type  ENUM('documentation', 'tutorial', 'course', 'reference', 'guide') NOT NULL DEFAULT 'documentation',
    created_at     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (resource_id),
    UNIQUE KEY uq_resource_skill_url (skill_name, resource_url(255)),
    KEY idx_resources_skill (skill_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
