import { useCallback, useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { Info, Search, SearchX } from 'lucide-react';
import { jobsApi } from '../services/api';
import { useDebounce, useDocumentTitle } from '../hooks/useAsync';
import { useSaveJob } from '../hooks/useSaveJob';
import JobCard from '../components/JobCard';
import { Alert, EmptyState, ErrorState, PageHeader, Pagination, Skeleton, Spinner } from '../components/ui';
import { EMPLOYMENT_TYPES, EXPERIENCE_YEARS } from '../utils/format';

const SUGGESTIONS = ['Software Engineer in Chennai', 'React Developer in Bengaluru', 'Python Developer in Hyderabad',
  'Full Stack Developer in Mumbai'];
const PAGE_SIZE = 10;

export default function Jobs() {
  useDocumentTitle('Find Jobs');
  const [params, setParams] = useSearchParams();
  const [tab, setTab] = useState(params.get('tab') === 'browse' ? 'browse' : 'search');
  const [form, setForm] = useState({
    query: params.get('q') || '', location: params.get('location') || '', remote: false,
    employment_type: '', experience_years: '', sort: 'score',
  });
  const [results, setResults] = useState(null);   // live search results
  const [meta, setMeta] = useState({ page: 1, hasMore: false, isMock: false });
  const [searching, setSearching] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState(null);
  const [formError, setFormError] = useState('');

  // Browse tab: jobs already stored in JobSense, filtered as you type (debounced).
  const [browse, setBrowse] = useState({ q: '', location: '', remote: false, offset: 0 });
  const debouncedQ = useDebounce(browse.q, 400);
  const debouncedLoc = useDebounce(browse.location, 400);
  const [stored, setStored] = useState({ data: null, loading: false, error: null });

  const updateJob = useCallback((jobId, saved) => {
    const patch = (items) => items?.map((j) => (j.job_id === jobId ? { ...j, is_saved: saved } : j));
    setResults(patch);
    setStored((s) => (s.data ? { ...s, data: { ...s.data, items: patch(s.data.items) } } : s));
  }, []);
  const { toggle, pending } = useSaveJob(updateJob);

  const runSearch = async (page = 1, override) => {
    const f = override || form;
    if (!f.query.trim()) { setFormError('Enter a job title or keyword'); return; }
    setFormError('');
    setError(null);
    page === 1 ? setSearching(true) : setLoadingMore(true);
    try {
      const { data } = await jobsApi.search({ ...f, page });
      setResults((prev) => (page === 1 ? data.items : [...(prev || []), ...data.items.filter((j) => !prev?.some((p) => p.job_id === j.job_id))]));
      setMeta({ page, hasMore: data.has_more && data.items.length > 0, isMock: data.is_mock });
      if (page === 1) setParams({ q: f.query, ...(f.location ? { location: f.location } : {}) }, { replace: true });
    } catch (err) {
      setError(err);
    } finally {
      setSearching(false);
      setLoadingMore(false);
    }
  };

  useEffect(() => {
    if (params.get('q') && tab === 'search' && results === null) runSearch(1);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (tab !== 'browse') return;
    let cancelled = false;
    setStored((s) => ({ ...s, loading: true, error: null }));
    jobsApi.list({ q: debouncedQ, location: debouncedLoc, remote: browse.remote || undefined, limit: PAGE_SIZE, offset: browse.offset })
      .then((data) => { if (!cancelled) setStored({ data, loading: false, error: null }); })
      .catch((err) => { if (!cancelled) setStored({ data: null, loading: false, error: err }); });
    return () => { cancelled = true; };
  }, [tab, debouncedQ, debouncedLoc, browse.remote, browse.offset]);

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.type === 'checkbox' ? e.target.checked : e.target.value }));

  return (
    <div>
      <PageHeader title="Find Jobs" description="Search current openings and see how each one aligns with your resume." />

      <div className="tabs" role="tablist" aria-label="Job sources">
        <button type="button" role="tab" className="tab" aria-selected={tab === 'search'} onClick={() => setTab('search')}>Search live jobs</button>
        <button type="button" role="tab" className="tab" aria-selected={tab === 'browse'} onClick={() => setTab('browse')}>Browse stored jobs</button>
      </div>

      {tab === 'search' ? (
        <>
          <form className="card" onSubmit={(e) => { e.preventDefault(); runSearch(1); }} noValidate aria-label="Job search">
            <div className="grid grid-3">
              <div className="field" style={{ marginBottom: 0 }}>
                <label htmlFor="q">Job title or keyword</label>
                <input id="q" className="input" placeholder="e.g. React Developer" value={form.query} onChange={set('query')}
                  aria-invalid={Boolean(formError)} aria-describedby={formError ? 'q-error' : undefined} />
                {formError && <span id="q-error" className="field-error">{formError}</span>}
              </div>
              <div className="field" style={{ marginBottom: 0 }}>
                <label htmlFor="loc">Location</label>
                <input id="loc" className="input" placeholder="e.g. Chennai" value={form.location} onChange={set('location')} />
              </div>
              <div className="field" style={{ marginBottom: 0 }}>
                <label htmlFor="etype">Job type</label>
                <select id="etype" className="select" value={form.employment_type} onChange={set('employment_type')}>
                  {EMPLOYMENT_TYPES.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
                </select>
              </div>
              <div className="field" style={{ marginBottom: 0 }}>
                <label htmlFor="exp">Your experience</label>
                <select id="exp" className="select" value={form.experience_years} onChange={set('experience_years')}
                  aria-describedby="exp-hint">
                  {EXPERIENCE_YEARS.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
                </select>
                <span id="exp-hint" className="hint">Hides jobs asking for more experience.</span>
              </div>
              <div className="field" style={{ marginBottom: 0 }}>
                <label htmlFor="sort">Sort results by</label>
                <select id="sort" className="select" value={form.sort} onChange={set('sort')}>
                  <option value="score">Match score</option>
                  <option value="relevance">Search relevance</option>
                </select>
              </div>
              <div className="field" style={{ marginBottom: 0, justifyContent: 'flex-end' }}>
                <label className="checkbox"><input type="checkbox" checked={form.remote} onChange={set('remote')} /> Remote only</label>
              </div>
            </div>
            <div className="row" style={{ marginTop: '1rem' }}>
              <button type="submit" className="btn btn-primary" disabled={searching}>
                {searching ? <Spinner /> : <Search size={16} aria-hidden="true" />} Search jobs
              </button>
              <span className="small muted">Try:</span>
              {SUGGESTIONS.map((s) => {
                const [query, location] = s.split(' in ');
                return (
                  <button key={s} type="button" className="toggle-chip" onClick={() => {
                    const next = { ...form, query, location };
                    setForm(next);
                    runSearch(1, next);
                  }}>{s}</button>
                );
              })}
            </div>
          </form>

          <div style={{ marginTop: '1rem' }} aria-live="polite">
            {meta.isMock && results && (
              <Alert type="warning" icon={Info}>
                <strong>Development mode:</strong> these are clearly-labelled sample listings from the mock provider, not real jobs.
                Configure <code>JSEARCH_API_KEY</code> on the server to search live openings.
              </Alert>
            )}
            {error && <div style={{ marginTop: 12 }}><ErrorState error={error} onRetry={() => runSearch(1)} title="Job search failed" /></div>}
            {searching ? <div style={{ marginTop: 12 }}><Skeleton count={3} lines={4} /></div> : results === null ? (
              !error && <EmptyState icon={Search} title="Search for jobs">Enter a job title and location, e.g. “Python Developer” in “Hyderabad”.</EmptyState>
            ) : results.length === 0 ? (
              <EmptyState icon={SearchX} title="No jobs found">Try a broader keyword, another city, or turn off the remote filter.</EmptyState>
            ) : (
              <>
                <p className="small muted" style={{ margin: '12px 0' }}>
                  {results.length} jobs · scores compare each job with your resume.
                  {!results.some((j) => j.match) && <> <Link to="/resume">Upload a resume</Link> to see match scores.</>}
                </p>
                <div className="stack">
                  {results.map((job) => <JobCard key={job.job_id} job={job} onToggleSave={toggle} saving={pending === job.job_id} />)}
                </div>
                {meta.hasMore && (
                  <div className="pagination">
                    <button type="button" className="btn btn-secondary" onClick={() => runSearch(meta.page + 1)} disabled={loadingMore}>
                      {loadingMore && <Spinner dark />} Load more
                    </button>
                  </div>
                )}
              </>
            )}
          </div>
        </>
      ) : (
        <>
          <div className="card row" style={{ alignItems: 'flex-end' }}>
            <div className="field" style={{ marginBottom: 0, flex: '2 1 220px' }}>
              <label htmlFor="bq">Filter by title, company or skill</label>
              <input id="bq" className="input" value={browse.q} onChange={(e) => setBrowse({ ...browse, q: e.target.value, offset: 0 })} />
            </div>
            <div className="field" style={{ marginBottom: 0, flex: '1 1 160px' }}>
              <label htmlFor="bl">Location</label>
              <input id="bl" className="input" value={browse.location} onChange={(e) => setBrowse({ ...browse, location: e.target.value, offset: 0 })} />
            </div>
            <label className="checkbox" style={{ paddingBottom: 10 }}>
              <input type="checkbox" checked={browse.remote} onChange={(e) => setBrowse({ ...browse, remote: e.target.checked, offset: 0 })} /> Remote only
            </label>
          </div>
          <div style={{ marginTop: '1rem' }}>
            {stored.loading && !stored.data ? <Skeleton count={3} lines={4} /> : stored.error ? <ErrorState error={stored.error} /> : (
              stored.data?.items.length === 0 ? (
                <EmptyState icon={SearchX} title="No stored jobs match">Jobs appear here after they have been found through a search.</EmptyState>
              ) : stored.data && (
                <>
                  <p className="small muted">{stored.data.total} stored jobs</p>
                  <div className="stack">
                    {stored.data.items.map((job) => <JobCard key={job.job_id} job={job} onToggleSave={toggle} saving={pending === job.job_id} />)}
                  </div>
                  <Pagination offset={browse.offset} limit={PAGE_SIZE} total={stored.data.total}
                    onChange={(offset) => { setBrowse({ ...browse, offset }); window.scrollTo(0, 0); }} />
                </>
              )
            )}
          </div>
        </>
      )}
    </div>
  );
}
