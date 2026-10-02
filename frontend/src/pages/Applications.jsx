import { useState } from 'react';
import { Link } from 'react-router-dom';
import { ClipboardList, Pencil, Trash2 } from 'lucide-react';
import { applicationsApi } from '../services/api';
import { useAsync, useDocumentTitle } from '../hooks/useAsync';
import { useToast } from '../context/ToastContext';
import ApplicationModal from '../components/ApplicationModal';
import { ConfirmDialog, EmptyState, ErrorState, PageHeader, Skeleton } from '../components/ui';
import { APPLICATION_STATUSES, formatDate } from '../utils/format';

export default function Applications() {
  useDocumentTitle('Applications');
  const toast = useToast();
  const [filter, setFilter] = useState('');
  const { data, loading, error, reload, setData } = useAsync(() => applicationsApi.list(filter ? { status: filter } : {}), [filter]);
  const [editing, setEditing] = useState(null);
  const [removing, setRemoving] = useState(null);
  const [busy, setBusy] = useState(false);

  const changeStatus = async (app, status) => {
    try {
      const updated = await applicationsApi.update(app.application_id, { status });
      setData((d) => ({ ...d, items: d.items.map((a) => (a.application_id === app.application_id ? updated : a)) }));
      toast.success(`Status updated to ${status}`);
    } catch (err) {
      toast.error(err.message);
    }
  };

  const doRemove = async () => {
    setBusy(true);
    try {
      await applicationsApi.remove(removing.application_id);
      setData((d) => ({ ...d, items: d.items.filter((a) => a.application_id !== removing.application_id) }));
      toast.info('Application removed');
      setRemoving(null);
    } catch (err) {
      toast.error(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div>
      <PageHeader title="Applications" description="Track where you have applied and update each application as it progresses." />
      <div className="toggle-group" role="group" aria-label="Filter by status" style={{ marginBottom: '1rem' }}>
        {['', ...APPLICATION_STATUSES].map((s) => (
          <button key={s || 'all'} type="button" className="toggle-chip" aria-pressed={filter === s} onClick={() => setFilter(s)}>{s || 'All'}</button>
        ))}
      </div>

      {loading && !data ? <Skeleton count={2} /> : error ? <ErrorState error={error} onRetry={reload} /> : data.items.length === 0 ? (
        <EmptyState icon={ClipboardList} title={filter ? `No applications with status “${filter}”` : 'No applications tracked yet'}
          action={!filter && <Link className="btn btn-primary" to="/saved">Go to saved jobs</Link>}>
          Open a job and choose “Track application” to add it here.
        </EmptyState>
      ) : (
        <div className="table-wrap">
          <table className="table table-responsive">
            <thead>
              <tr><th scope="col">Job</th><th scope="col">Company</th><th scope="col">Status</th><th scope="col">Applied</th><th scope="col">Notes</th><th scope="col">Updated</th><th scope="col"><span className="sr-only">Actions</span></th></tr>
            </thead>
            <tbody>
              {data.items.map((a) => (
                <tr key={a.application_id}>
                  <td data-label="Job"><Link to={`/jobs/${a.job_id}`}>{a.title}</Link></td>
                  <td data-label="Company">{a.company}</td>
                  <td data-label="Status">
                    <label className="sr-only" htmlFor={`st-${a.application_id}`}>Status for {a.title}</label>
                    <select id={`st-${a.application_id}`} className="select" style={{ minHeight: 32, width: 'auto' }}
                      value={a.status} onChange={(e) => changeStatus(a, e.target.value)}>
                      {APPLICATION_STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
                    </select>
                  </td>
                  <td data-label="Applied" className="nowrap">{formatDate(a.applied_date)}</td>
                  <td data-label="Notes" className="small muted" style={{ maxWidth: 240 }}>{a.notes || '—'}</td>
                  <td data-label="Updated" className="nowrap small">{formatDate(a.updated_at)}</td>
                  <td data-label="Actions">
                    <div className="row" style={{ flexWrap: 'nowrap' }}>
                      <button type="button" className="btn btn-ghost btn-icon" onClick={() => setEditing(a)} aria-label={`Edit application for ${a.title}`}><Pencil size={15} /></button>
                      <button type="button" className="btn btn-ghost btn-icon" onClick={() => setRemoving(a)} aria-label={`Remove application for ${a.title}`}><Trash2 size={15} /></button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {editing && <ApplicationModal application={editing} onClose={() => setEditing(null)}
        onSaved={(u) => setData((d) => ({ ...d, items: d.items.map((a) => (a.application_id === u.application_id ? u : a)) }))} />}
      {removing && <ConfirmDialog title="Remove application?" danger confirmLabel="Remove" busy={busy}
        message={`Stop tracking your application for “${removing.title}”?`} onCancel={() => setRemoving(null)} onConfirm={doRemove} />}
    </div>
  );
}
