import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Briefcase, Trash2 } from 'lucide-react';
import { adminApi } from '../../services/api';
import { useAsync, useDebounce, useDocumentTitle } from '../../hooks/useAsync';
import { useToast } from '../../context/ToastContext';
import { ConfirmDialog, EmptyState, ErrorState, MockBadge, PageHeader, Pagination, Skeleton } from '../../components/ui';
import { formatDate } from '../../utils/format';

const LIMIT = 20;

export default function AdminJobs() {
  useDocumentTitle('Jobs');
  const toast = useToast();
  const [q, setQ] = useState('');
  const [source, setSource] = useState('');
  const [offset, setOffset] = useState(0);
  const dq = useDebounce(q, 350);
  const { data, loading, error, reload } = useAsync(() => adminApi.jobs({ q: dq, source, limit: LIMIT, offset }), [dq, source, offset]);
  const [confirm, setConfirm] = useState(null);
  const [busy, setBusy] = useState(false);

  const run = async () => {
    setBusy(true);
    try {
      if (confirm === 'mock') {
        const r = await adminApi.deleteMockJobs();
        toast.success(`Deleted ${r.deleted} mock jobs`);
      } else {
        await adminApi.deleteJob(confirm.job_id);
        toast.success('Job deleted');
      }
      setConfirm(null);
      setOffset(0);
      reload({ silent: true });
    } catch (err) { toast.error(err.message); } finally { setBusy(false); }
  };

  return (
    <div>
      <PageHeader title="Jobs" description="Jobs stored from the job provider. Jobs are never seeded manually."
        actions={<button type="button" className="btn btn-danger" onClick={() => setConfirm('mock')}>Delete all mock jobs</button>} />
      <div className="card row" style={{ alignItems: 'flex-end', marginBottom: '1rem' }}>
        <div className="field" style={{ marginBottom: 0, flex: '2 1 240px' }}>
          <label htmlFor="jq">Search title, company or skill</label>
          <input id="jq" className="input" value={q} onChange={(e) => { setQ(e.target.value); setOffset(0); }} />
        </div>
        <div className="field" style={{ marginBottom: 0, flex: '1 1 150px' }}>
          <label htmlFor="js">Source</label>
          <select id="js" className="select" value={source} onChange={(e) => { setSource(e.target.value); setOffset(0); }}>
            <option value="">All sources</option><option value="jsearch">JSearch</option><option value="mock">Mock (samples)</option>
          </select>
        </div>
      </div>
      {loading && !data ? <Skeleton /> : error ? <ErrorState error={error} onRetry={reload} /> : data.items.length === 0 ? (
        <EmptyState icon={Briefcase} title="No jobs stored">Jobs are stored when candidates search.</EmptyState>
      ) : (
        <>
          <p className="small muted">{data.total} jobs</p>
          <div className="table-wrap">
            <table className="table table-responsive">
              <thead><tr><th scope="col">Title</th><th scope="col">Company</th><th scope="col">Location</th><th scope="col">Source</th><th scope="col">Skills</th><th scope="col">Fetched</th><th scope="col"><span className="sr-only">Actions</span></th></tr></thead>
              <tbody>
                {data.items.map((j) => (
                  <tr key={j.job_id}>
                    <td data-label="Title"><Link to={`/jobs/${j.job_id}`}>{j.title}</Link></td>
                    <td data-label="Company" className="small">{j.company}</td>
                    <td data-label="Location" className="small">{j.location || '—'}</td>
                    <td data-label="Source">{j.is_mock ? <MockBadge /> : <span className="badge">{j.source}</span>}</td>
                    <td data-label="Skills">{j.required_skills.length}</td>
                    <td data-label="Fetched" className="nowrap small">{formatDate(j.fetched_at)}</td>
                    <td data-label="Actions">
                      <button type="button" className="btn btn-ghost btn-icon" onClick={() => setConfirm(j)} aria-label={`Delete ${j.title}`}><Trash2 size={15} /></button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Pagination offset={offset} limit={LIMIT} total={data.total} onChange={setOffset} />
        </>
      )}
      {confirm && <ConfirmDialog title={confirm === 'mock' ? 'Delete all mock jobs?' : 'Delete job?'} danger confirmLabel="Delete" busy={busy}
        onCancel={() => setConfirm(null)} onConfirm={run}
        message={confirm === 'mock' ? 'All sample jobs, and matches/saves/applications that reference them, will be removed.'
          : `“${confirm.title}” and all matches, saves and applications referencing it will be removed.`} />}
    </div>
  );
}
