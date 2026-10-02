import { useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { ArrowLeft, Bookmark, BookmarkCheck, Building2, ClipboardList, ExternalLink, Info, MapPin, Wifi } from 'lucide-react';
import { jobsApi } from '../services/api';
import { useAsync, useDocumentTitle } from '../hooks/useAsync';
import { useSaveJob } from '../hooks/useSaveJob';
import ApplicationModal from '../components/ApplicationModal';
import SkillGap from '../components/SkillGap';
import { Alert, ErrorState, MetricRow, MockBadge, ScoreBadge, Skeleton, SkillChips } from '../components/ui';
import { formatDate, pct } from '../utils/format';
import './JobDetails.css';

export default function JobDetails() {
  const { jobId } = useParams();
  const { data, loading, error, reload, setData } = useAsync(() => jobsApi.get(jobId), [jobId]);
  const navigate = useNavigate();
  const [showApply, setShowApply] = useState(false);
  const { toggle, pending } = useSaveJob((_, saved) => setData((d) => ({ ...d, job: { ...d.job, is_saved: saved } })));
  useDocumentTitle(data?.job?.title || 'Job details');

  if (loading && !data) return <Skeleton count={3} lines={5} />;
  if (error) return <ErrorState error={error} onRetry={reload} title="Could not load this job" />;

  const { job, explanation, application, profile_ready: profileReady } = data;
  const m = job.match;

  return (
    <div>
      <button type="button" className="btn btn-ghost btn-sm" style={{ marginBottom: 12 }} onClick={() => navigate(-1)}>
        <ArrowLeft size={15} aria-hidden="true" /> Back
      </button>

      <header className="card job-hero">
        <div style={{ minWidth: 0 }}>
          <h1>{job.title}</h1>
          <div className="job-meta-lg">
            <span><Building2 size={16} aria-hidden="true" /> {job.company}</span>
            {job.location && <span><MapPin size={16} aria-hidden="true" /> {job.location}</span>}
            <span><Wifi size={16} aria-hidden="true" /> {job.remote ? 'Remote' : 'On-site / not specified'}</span>
          </div>
          <div className="row small" style={{ marginTop: 10 }}>
            {job.employment_type && <span className="badge">{job.employment_type}</span>}
            {job.min_experience_years !== null && job.min_experience_years !== undefined && <span className="badge">{job.min_experience_years}+ yrs</span>}
            {job.posted_at && <span className="muted">Posted {formatDate(job.posted_at)}</span>}
            {job.is_mock ? <MockBadge /> : <span className="muted">Source: {job.publisher || job.source}</span>}
          </div>
          <div className="row" style={{ marginTop: 16 }}>
            <button type="button" className="btn btn-secondary" onClick={() => toggle(job)} disabled={pending === job.job_id} aria-pressed={job.is_saved}>
              {job.is_saved ? <BookmarkCheck size={16} aria-hidden="true" /> : <Bookmark size={16} aria-hidden="true" />}
              {job.is_saved ? 'Saved' : 'Save job'}
            </button>
            {job.job_url ? (
              <a className="btn btn-primary" href={job.job_url} target="_blank" rel="noopener noreferrer">
                Apply / Visit job <ExternalLink size={15} aria-hidden="true" /><span className="sr-only">(opens in a new tab)</span>
              </a>
            ) : (
              <span className="small muted">No external posting (sample listing)</span>
            )}
            {application ? (
              <Link className="btn btn-highlight" to="/applications"><ClipboardList size={16} aria-hidden="true" /> Tracking: {application.status}</Link>
            ) : (
              <button type="button" className="btn btn-highlight" onClick={() => setShowApply(true)}>
                <ClipboardList size={16} aria-hidden="true" /> Track application
              </button>
            )}
          </div>
        </div>
        {m && <ScoreBadge score={m.final_score} />}
      </header>

      {job.is_mock && (
        <div style={{ marginTop: '1rem' }}>
          <Alert type="warning" icon={Info}>This is a generated sample listing for development and testing. It is not a real job posting.</Alert>
        </div>
      )}

      <div className="job-detail-grid">
        <div className="stack">
          <section className="card" aria-labelledby="desc-title">
            <h2 id="desc-title">Job description</h2>
            <div className="job-description">{job.description || 'No description provided.'}</div>
          </section>
        </div>

        <aside className="stack" aria-label="Match analysis">
          <section className="card" aria-labelledby="score-title">
            <h2 id="score-title">Why this score?</h2>
            {!profileReady ? (
              <p className="small muted"><Link to="/resume">Upload your resume</Link> to see how this job matches your profile.</p>
            ) : m ? (
              <>
                <MetricRow label="Text similarity" value={m.text_similarity} />
                <MetricRow label="Skill match" value={m.skill_match} variant="butter" />
                <MetricRow label="Final match" value={m.final_score} variant="success" />
                <hr className="divider" />
                <p className="small"><strong>Formula:</strong> {explanation.formula}</p>
                {m.skill_data_available && (
                  <p className="small muted">
                    Final = {explanation.weights.text_similarity} × {pct(m.text_similarity, 1)} + {explanation.weights.skill_match} × {pct(m.skill_match, 1)} = <strong>{pct(m.final_score, 1)}</strong>
                  </p>
                )}
                <p className="small muted">{explanation.text_similarity_method}. {explanation.skill_match_method}.</p>
                {explanation.top_shared_terms.length > 0 && (
                  <>
                    <p className="small" style={{ marginBottom: 6 }}><strong>Terms shared with your resume</strong></p>
                    <SkillChips skills={explanation.top_shared_terms} />
                  </>
                )}
              </>
            ) : <p className="small muted">Score not available.</p>}
          </section>

          <section className="card" aria-labelledby="req-title">
            <h2 id="req-title">Required skills</h2>
            <SkillChips skills={job.required_skills} emptyText="No specific skills could be identified in this description." />
          </section>
        </aside>
      </div>

      {m && (
        <section className="card" style={{ marginTop: '1rem' }} aria-labelledby="gap-title">
          <h2 id="gap-title">Skill gap analysis</h2>
          <SkillGap matched={m.matched_skills} missing={m.missing_skills} resources={data.learning_resources} />
        </section>
      )}

      {showApply && <ApplicationModal job={job} onClose={() => setShowApply(false)}
        onSaved={(a) => setData((d) => ({ ...d, application: { application_id: a.application_id, status: a.status } }))} />}
    </div>
  );
}
