import { Link } from 'react-router-dom';
import { Bookmark, BookmarkCheck, Building2, ExternalLink, MapPin, Wifi } from 'lucide-react';
import { MockBadge, ScoreBadge, SkillChips } from './ui';
import { timeAgo } from '../utils/format';
import './JobCard.css';

export default function JobCard({ job, onToggleSave, saving = false, showSnippet = true }) {
  const m = job.match;
  return (
    <article className="card job-card" aria-labelledby={`job-${job.job_id}-title`}>
      <div className="job-card-main">
        <div className="job-card-head">
          <div style={{ minWidth: 0 }}>
            <h3 id={`job-${job.job_id}-title`} className="job-title">
              <Link to={`/jobs/${job.job_id}`}>{job.title}</Link>
            </h3>
            <div className="job-meta">
              <span><Building2 size={14} aria-hidden="true" /> {job.company}</span>
              {job.location && <span><MapPin size={14} aria-hidden="true" /> {job.location}</span>}
              {job.remote && <span><Wifi size={14} aria-hidden="true" /> Remote</span>}
            </div>
          </div>
          {m && <ScoreBadge score={m.final_score} />}
        </div>

        <div className="row small" style={{ marginTop: 8 }}>
          {job.employment_type && <span className="badge">{job.employment_type}</span>}
          {job.posted_at && <span className="muted">Posted {timeAgo(job.posted_at)}</span>}
          {job.is_mock ? <MockBadge /> : job.publisher && <span className="muted">via {job.publisher}</span>}
        </div>

        {showSnippet && job.snippet && <p className="job-snippet">{job.snippet}…</p>}

        {m ? (
          <div className="job-skills">
            <div className="small muted">
              Text similarity {m.text_similarity.toFixed(0)}% · Skill match {m.skill_match === null ? 'N/A' : `${m.skill_match.toFixed(0)}%`}
            </div>
            <div className="job-skill-row"><span className="small">Matched</span><SkillChips skills={m.matched_skills} variant="matched" limit={5} /></div>
            <div className="job-skill-row"><span className="small">Missing</span><SkillChips skills={m.missing_skills} variant="missing" limit={5} emptyText="No missing skills identified" /></div>
          </div>
        ) : (
          job.required_skills?.length > 0 && <div className="job-skills"><SkillChips skills={job.required_skills} limit={6} /></div>
        )}
      </div>

      <div className="job-card-actions">
        <Link className="btn btn-sm btn-primary" to={`/jobs/${job.job_id}`}>Details</Link>
        {onToggleSave && (
          <button type="button" className="btn btn-sm btn-secondary" onClick={() => onToggleSave(job)} disabled={saving}
            aria-pressed={job.is_saved} aria-label={job.is_saved ? `Unsave ${job.title}` : `Save ${job.title}`}>
            {job.is_saved ? <BookmarkCheck size={15} aria-hidden="true" /> : <Bookmark size={15} aria-hidden="true" />}
            {job.is_saved ? 'Saved' : 'Save'}
          </button>
        )}
        {job.job_url && (
          <a className="btn btn-sm btn-ghost" href={job.job_url} target="_blank" rel="noopener noreferrer">
            View job <ExternalLink size={14} aria-hidden="true" /><span className="sr-only">(opens in a new tab)</span>
          </a>
        )}
      </div>
    </article>
  );
}
