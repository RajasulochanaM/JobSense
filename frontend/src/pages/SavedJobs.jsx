import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Bookmark, ClipboardList, ExternalLink, Trash2 } from 'lucide-react';
import { savedApi } from '../services/api';
import { useAsync, useDocumentTitle } from '../hooks/useAsync';
import { useToast } from '../context/ToastContext';
import ApplicationModal from '../components/ApplicationModal';
import { EmptyState, ErrorState, MockBadge, PageHeader, ScoreBadge, Skeleton, SkillChips } from '../components/ui';
import { formatDate } from '../utils/format';

export default function SavedJobs() {
  useDocumentTitle('Saved Jobs');
  const toast = useToast();
  const { data, loading, error, reload, setData } = useAsync(() => savedApi.list(), []);
  const [tracking, setTracking] = useState(null);

  const unsave = async (job) => {
    try {
      await savedApi.unsave(job.job_id);
      setData((d) => ({ ...d, items: d.items.filter((j) => j.job_id !== job.job_id) }));
      toast.info('Removed from saved jobs');
    } catch (err) {
      toast.error(err.message);
    }
  };

  return (
    <div>
      <PageHeader title="Saved Jobs" description="Jobs you bookmarked. Start tracking an application when you apply." />
      {loading && !data ? <Skeleton count={3} /> : error ? <ErrorState error={error} onRetry={reload} /> : data.items.length === 0 ? (
        <EmptyState icon={Bookmark} title="No saved jobs yet" action={<Link className="btn btn-primary" to="/jobs">Find jobs</Link>}>
          Save interesting jobs from search results or your matches to review them later.
        </EmptyState>
      ) : (
        <div className="stack">
          {data.items.map((job) => (
            <article key={job.saved_id} className="card">
              <div className="row-between" style={{ alignItems: 'flex-start' }}>
                <div style={{ minWidth: 0 }}>
                  <h3 style={{ marginBottom: 2 }}><Link to={`/jobs/${job.job_id}`}>{job.title}</Link></h3>
                  <div className="small muted">
                    {job.company}{job.location ? ` · ${job.location}` : ''}{job.remote ? ' · Remote' : ''} · Saved {formatDate(job.saved_at)}
                  </div>
                  <div className="row" style={{ marginTop: 6 }}>
                    {job.is_mock && <MockBadge />}
                    {job.application_status && <span className="badge badge-burgundy">Application: {job.application_status}</span>}
                  </div>
                  {job.match && (
                    <div style={{ marginTop: 10 }}>
                      <SkillChips skills={job.match.missing_skills} variant="missing" limit={5} emptyText="No missing skills identified" />
                    </div>
                  )}
                </div>
                {job.match && <ScoreBadge score={job.match.final_score} />}
              </div>
              <div className="row" style={{ marginTop: 12, paddingTop: 12, borderTop: '1px solid var(--border)' }}>
                {job.job_url && (
                  <a className="btn btn-sm btn-primary" href={job.job_url} target="_blank" rel="noopener noreferrer">
                    Open job <ExternalLink size={14} aria-hidden="true" /><span className="sr-only">(opens in a new tab)</span>
                  </a>
                )}
                {job.application_id ? (
                  <Link className="btn btn-sm btn-secondary" to="/applications">View application</Link>
                ) : (
                  <button type="button" className="btn btn-sm btn-highlight" onClick={() => setTracking(job)}>
                    <ClipboardList size={14} aria-hidden="true" /> Start tracking
                  </button>
                )}
                <button type="button" className="btn btn-sm btn-danger" onClick={() => unsave(job)} aria-label={`Unsave ${job.title}`}>
                  <Trash2 size={14} aria-hidden="true" /> Unsave
                </button>
              </div>
            </article>
          ))}
        </div>
      )}
      {tracking && <ApplicationModal job={tracking} onClose={() => setTracking(null)} onSaved={() => reload({ silent: true })} />}
    </div>
  );
}
