# ML / NLP methodology

JobSense deliberately uses **classical, explainable NLP**: spaCy preprocessing, a skill
taxonomy, **TF-IDF + cosine similarity**, and **explicit skill matching**. No LLMs,
embeddings or vector databases are used anywhere in the scoring path, so every score can
be traced back to concrete terms and skills.

All ML code lives in `backend/app/ml/`, separated from HTTP routes:

| Module | Class / function | Responsibility |
|---|---|---|
| `preprocessing/resume_parser.py` | `extract_text`, `parse_sections` | pypdf / python-docx text extraction; education, experience, years |
| `preprocessing/text_preprocessor.py` | `TextPreprocessor` | normalisation, tokenisation, noise removal, lemmatisation |
| `skill_extraction/taxonomy.py` | `SKILLS`, `canonical_skill` | skill dictionary: 137 skills, aliases, ambiguity flags, implications |
| `skill_extraction/skill_extractor.py` | `SkillExtractor` | spaCy `PhraseMatcher` skill extraction |
| `tfidf/vectorizer.py` | `build_vectorizer`, `vectorize` | scikit-learn `TfidfVectorizer` configuration |
| `similarity/text_similarity.py` | `TextSimilarityCalculator` | cosine similarity (0-100%) and shared-term explanation |
| `matching/skill_matcher.py` | `SkillMatcher` | matched / missing skills, skill-match % |
| `matching/job_match_scorer.py` | `JobMatchScorer`, `combine_scores` | weighted final score, ranking |
| `career/career_recommender.py` | `CareerRecommender` | career skill alignment + reasons |
| `resume_processor.py` | `ResumeProcessor` | orchestrates the resume pipeline |

## 1. Resume pipeline

```
Resume file (PDF / DOCX)
  -> text extraction          pypdf (PDF), python-docx (paragraphs + tables)
  -> section parsing          headings -> education / experience; years of experience
  -> skill extraction         spaCy PhraseMatcher over the skill taxonomy
  -> text normalisation       NFKC, remove URLs / emails / phone numbers / bullets
  -> tokenisation             spaCy tokenizer (en_core_web_sm)
  -> noise removal            stop words, punctuation, numbers, 1-char tokens, generic resume words
  -> lemmatisation            "developed" -> "develop", "APIs" -> "api"
  -> normalised token string  stored once in RESUMES.processed_text
```

The resume is processed **once** at upload; results (text, processed text, skills,
education, experience) are persisted so NLP never re-runs for matching.

Experience years: an explicit "N years of experience" statement wins; otherwise date
ranges inside the Experience section ("Jan 2019 - Dec 2020", "2021 - Present") are summed,
counting months inclusively.

## 2. Skill extraction and normalisation

The taxonomy maps surface forms to one canonical name:

| Found in text | Canonical skill |
|---|---|
| ReactJS, React.js, react js | React |
| NodeJS, node js | Node.js |
| JS (in a technical context) | JavaScript |
| Python3, python 3 | Python |
| k8s, helm | Kubernetes |
| CI/CD, GitHub Actions, continuous integration | CI/CD |

**False-positive control.** Aliases that are ordinary English words (`react`, `go`,
`rest`, `excel`, `spring`, `express`, single letters `C` / `R`) are marked *ambiguous*.
They are accepted only when another unambiguous skill occurs within 8 tokens (for
example, inside a skills list). So "we **react** quickly" or "the **rest** of the team"
extract nothing, while "Languages: **Go**, Python, Java" extracts Go. Single-letter and
mixed-case ambiguous aliases (`C`, `R`, `Go`, `ML`) are also matched case-sensitively.
Overlapping matches keep the longest span ("React Native" beats "React").

**Implied skills.** Some skills logically cover others (MySQL -> SQL, TypeScript ->
JavaScript, Flask -> Python). During matching only, the candidate's skills are expanded
with these implications, so a candidate with MySQL is not reported as "missing SQL".

**Soft skills** (communication, problem solving, teamwork) are still extracted from
resumes, but they are *excluded from a job's required skills*. They appear in almost every
job ad and are rarely written verbatim on resumes, so including them would lower every
skill-match score without saying anything about technical fit.

## 3. TF-IDF + cosine similarity (text similarity)

For each candidate/job pair:

1. take the preprocessed resume text and the preprocessed job description
   (the job is preprocessed once when it is first stored)
2. fit `sklearn.feature_extraction.text.TfidfVectorizer` on the two documents
3. compute `sklearn.metrics.pairwise.cosine_similarity` between the two vectors
4. report it as a percentage: `0.82 -> 82%`

Vectorizer settings (`tfidf/vectorizer.py`):

| Setting | Value | Why |
|---|---|---|
| tokenizer | whitespace split | text is already tokenised/lemmatised by spaCy |
| ngram_range | (1, 1) | multi-word skills are already single tokens (see below); in evaluation, bigrams diluted overlap |
| sublinear_tf | True | `1 + log(tf)` stops a repeated word dominating |
| smooth_idf, norm | True, L2 | standard TF-IDF; cosine = dot product of L2-normalised vectors |

**Skill-phrase protection.** Before vectorising, every skill phrase found by the
extractor becomes one token (`Node.js` -> `skill_nodedotjs`, `REST APIs` ->
`skill_restapis`, `C++` -> `skill_cplusplus`). Without this, the tokenizer would split
"node.js" and drop "C++" and "C#" as punctuation.

**Why fit per pair?** Fitting on exactly the two documents makes each score
deterministic: the same resume and job always give the same similarity, regardless of
which other jobs were in the search results. The consequence is that typical resume-vs-
job similarities are modest (roughly 10-40%), because resumes and job ads use different
vocabulary. That is expected, and it is why explicit skill matching carries more weight.

The job-details page also lists the **terms shared with your resume**: the terms with
the highest product of TF-IDF weights, which explains where the similarity comes from.

## 4. Explicit skill matching

```
candidate: React, JavaScript, Node.js, MySQL
job:       React, JavaScript, Node.js, TypeScript, AWS
matched:   React, JavaScript, Node.js
missing:   TypeScript, AWS
skill_match = matched_required_skills / total_required_skills x 100 = 3 / 5 x 100 = 60%
```

If no required skills can be identified in a job description, `skill_match` is `NULL`
(shown as "N/A") and the final score falls back to text similarity alone. The UI states
this explicitly.

## 5. Final match score

```
Final Score = w1 x Text Similarity + w2 x Skill Match
```

| Variable | Env var | Initial value |
|---|---|---|
| w1 | `TEXT_SIMILARITY_WEIGHT` | 0.40 |
| w2 | `SKILL_MATCH_WEIGHT` | 0.60 |

These are **initial implementation values**, chosen because explicit skill overlap is a
stronger and more interpretable signal than raw vocabulary overlap. They can be tuned
during evaluation without code changes. Weights are normalised to sum to 1 and the result
is clamped, so `0 <= final score <= 100` always holds.

Example: text similarity 82%, skill match 75% -> `0.4 x 82 + 0.6 x 75 = 77.8%`.

Stored per match in `JOB_MATCHES`: text_similarity, skill_match, final_score,
matched_skills, missing_skills.

The UI never calls a match "perfect" or "guaranteed". Bands are descriptive: 70% and
above is "strong alignment", 40-69% "partial alignment", and below 40% "low alignment".

## 6. Job recommendation

```
candidate profile -> resume skills (+ manually added skills)
  -> retrieve jobs (search results, profile-based provider fetch, stored job pool)
  -> text similarity -> skill match -> final score -> rank (desc) -> JOB_MATCHES
```

Matches are cached and recomputed only when needed: new jobs are scored on first sight,
and uploading or deleting a resume or editing skills clears the user's cached matches.
"Refresh recommendations" can fetch new jobs from the provider using the candidate's top
career path and top skill, plus their preferred location.

## 7. Career path recommendation

Each career has required skills with an importance weight (3 core, 2 important, 1 nice to
have).

```
skill_alignment = sum(importance of matched skills) / sum(importance of all skills) x 100
text_similarity = TF-IDF cosine(resume, career name + description + skills) x 100
interest_match  = 100 if career.interest_area is one of the user's interests, else 0
                  (counts ONLY when skill_alignment > 0)

match_score = 0.75 x skill_alignment + 0.15 x text_similarity + 0.10 x interest_match
```

Weights: `CAREER_SKILL_WEIGHT`, `CAREER_TEXT_WEIGHT`, `CAREER_INTEREST_WEIGHT`.
Interests are a secondary signal and can never outweigh actual skill evidence: a career
with zero matching skills gets nothing from interests. Each recommendation stores
human-readable **reasons** (core skills already held, weighted alignment, text similarity,
interest match, experience, education relevance, core skills to develop next), and the UI
presents results as *potential* career paths, not the "best" career.

## 8. Learning resources

Missing skills (for a job or a career) are looked up in `LEARNING_RESOURCES`, which holds
147 curated links, mostly official documentation (MDN, react.dev, docs.python.org,
dev.mysql.com, docs.docker.com, kubernetes.io, AWS docs and similar). Nothing is scraped.
Admins can add, edit and remove resources.

## 9. Evaluation notes and limitations

* Dictionary-based extraction only finds skills in the taxonomy. Admins can extend
  careers and resources, and developers can add skills to `taxonomy.py`, then regenerate
  `seed.sql`.
* Scanned (image-only) PDFs contain no text and are rejected with a clear message. OCR is
  out of scope.
* Section parsing is heuristic. Education and experience detection is best-effort and
  never blocks processing.
* TF-IDF captures lexical, not semantic, similarity ("frontend" vs "UI engineer").
  This is a documented trade-off for explainability.
