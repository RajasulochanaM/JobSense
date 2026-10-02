import { useCallback, useEffect, useRef, useState } from 'react';
import { useLocation } from 'react-router-dom';
import { RefreshCw, Sparkles } from 'lucide-react';
import { matchesApi } from '../services/api';
import { useAsync } from '../hooks/useAsync';
import { useSaveJob } from '../hooks/useSaveJob';
import { useToast } from '../context/ToastContext';
import JobCard from './JobCard';
import { EmptyState, ErrorState, Pagination, Skeleton, Spinner } from './ui';

const LIMIT = 10;

/**
 * Jobs ranked against the candidate's resume (formerly the "My Matches" page).
 * `resumeKey` changes when the active resume changes so the list reloads.
 */
export default function RecommendedJobs({ resumeKey }) {
  const toast = useToast();
  const location = useLocation();
  const sectionRef = useRef(null);
  const [sort, setSort] = useState('score');
  const [offset, setOffset] = useState(0);
  const [refreshing, setRefreshing] = useState(false);
  const { data, loading, error, reload, setData } = useAsync(
    () => matchesApi.list({ sort, limit: LIMIT, offset }), [sort, offset, resumeKey]);

  // Deep links such as /resume#recommended (and the old /matches route) land on this section.
  useEffect(() => {
    if (location.hash === '#recommended' && data) sectionRef.current?.scrollIntoView({ block: 'start' });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location.hash, Boolean(data)]);

  const onSaved = useCallback((jobId, saved) => setData((d) => ({
    ...d, items: d.items.map((j) => (j.job_id === jobId ? { ...j, is_saved: saved } : j)),
  })), [setData]);
  const { toggle, pending } = useSaveJob(onSaved);

  const refresh = async () => {
    setRefreshing(true);
    try {
      const { data: r, message } = await matchesApi.refresh(true);
      r.fetch_error ? toast.error(message) : toast.success(`${message}${r.fetched_jobs ? ` · ${r.fetched_jobs} jobs fetched for your profile` : ''}`);
      setOffset(0);
      await reload();
    } catch (err) {
      toast.error(err.message);
    } finally {
      setRefreshing(false);
    }
  };

  const profileReady = data?.profile_ready;

  return (
    <section id="recommended" ref={sectionRef} className="card" style={{ marginTop: '1rem', scrollMarginTop: 80 }}
      aria-labelledby="recommended-title">
      <div className="row-between" style={{ marginBottom: '0.75rem' }}>
        <div>
          <h2 id="recommended-title" style={{ marginBottom: 2 }}>Recommended jobs</h2>
          <p className="small muted" style={{ margin: 0 }}>
            Jobs ranked by how closely they align with your resume. Scores are explainable, not guarantees.
          </p>
        </div>
        {profileReady && (
          <div className="row">
            <label className="sr-only" htmlFor="match-sort">Sort recommended jobs</label>
            <select id="match-sort" className="select" style={{ width: 'auto' }} value={sort}
              onChange={(e) => { setSort(e.target.value); setOffset(0); }}>
              <option value="score">Highest match score</option>
              <option value="newest">Newest</option>
            </select>
            <button type="button" className="btn btn-primary" onClick={refresh} disabled={refreshing}>
              {refreshing ? <Spinner /> : <RefreshCw size={16} aria-hidden="true" />} Refresh recommendations
            </button>
          </div>
        )}
      </div>

      {loading && !data ? <Skeleton count={3} lines={4} /> : error ? <ErrorState error={error} onRetry={reload} /> : !profileReady ? (
        <EmptyState icon={Sparkles} title="Upload your resume to get recommendations">
          JobSense needs your skills and resume text to calculate match scores.
        </EmptyState>
      ) : data.items.length === 0 ? (
        <EmptyState icon={Sparkles} title="No matches yet"
          action={<button type="button" className="btn btn-primary" onClick={refresh} disabled={refreshing}>Find jobs for my profile</button>}>
          Search for jobs, or let JobSense fetch jobs based on your top skills and career alignment.
        </EmptyState>
      ) : (
        <>
          <p className="small muted">{data.total} scored jobs</p>
          <div className="stack">
            {data.items.map((job) => <JobCard key={job.job_id} job={job} onToggleSave={toggle} saving={pending === job.job_id} showSnippet={false} />)}
          </div>
          <Pagination offset={offset} limit={LIMIT} total={data.total}
            onChange={(o) => { setOffset(o); sectionRef.current?.scrollIntoView({ block: 'start' }); }} />
        </>
      )}
    </section>
  );
}
