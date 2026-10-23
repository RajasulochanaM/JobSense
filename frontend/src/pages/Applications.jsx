import { Fragment, useState } from 'react';
import { Link } from 'react-router-dom';
import { BellRing, ClipboardList, History, Pencil, Trash2 } from 'lucide-react';
import { applicationsApi } from '../services/api';
import { useAsync, useDocumentTitle } from '../hooks/useAsync';
import { useToast } from '../context/ToastContext';
import ApplicationModal from '../components/ApplicationModal';
import { Alert, ConfirmDialog, EmptyState, ErrorState, PageHeader, Skeleton } from '../components/ui';
import { APPLICATION_STATUSES, formatDate } from '../utils/format';

/** One readable line per history event. */
export function describeEvent(e) {
  if (e.event_type === 'posting_opened') return 'Opened the job posting';
  if (e.event_type === 'created') {
    return e.source === 'auto'
      ? 'Tracking started automatically when you opened the job posting'
      : `Tracking started as ${e.to_status}`;
  }
  return `Status changed from ${e.from_status || '—'} to ${e.to_status}`;
}

const dateTime = (value) => formatDate(value, { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' });

export default function Applications() {
  useDocumentTitle('Applications');
  const toast = useToast();
  const [filter, setFilter] = useState('');
  const { data, loading, error, reload, setData } = useAsync(() => applicationsApi.list(filter ? { status: filter } : {}), [filter]);
  const [editing, setEditing] = useState(null);
  const [removing, setRemoving] = useState(null);
  const [expanded, setExpanded] = useState(null);
  const [busy, setBusy] = useState(false);

  const replaceItem = (updated) => setData((d) => {
    const items = d.items.map((a) => (a.application_id === updated.application_id ? updated : a));
    return { ...d, items, reminders: items.filter((a) => a.reminder).length };
  });

  const changeStatus = async (app, status) => {
    try {
      replaceItem(await applicationsApi.update(app.application_id, { status }));
      toast.success(`Status updated to ${status}`);
    } catch (err) {
      toast.error(err.message);
    }
  };

  const doRemove = async () => {
    setBusy(true);
    try {
      await applicationsApi.remove(removing.application_id);
      setData((d) => {
        const items = d.items.filter((a) => a.application_id !== removing.application_id);
        return { ...d, items, reminders: items.filter((a) => a.reminder).length };
      });
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
      <PageHeader title="Applications" description="Jobs are tracked automatically when you open a posting. Confirm each step here as it progresses." />
      <div className="toggle-group" role="group" aria-label="Filter by status" style={{ marginBottom: '1rem' }}>
        {['', ...APPLICATION_STATUSES].map((s) => (
          <button key={s || 'all'} type="button" className="toggle-chip" aria-pressed={filter === s} onClick={() => setFilter(s)}>{s || 'All'}</button>
        ))}
      </div>

      {data?.reminders > 0 && (
        <div style={{ marginBottom: '1rem' }}>
          <Alert type="info" icon={BellRing}>
            <strong>{data.reminders} application{data.reminders === 1 ? ' needs' : 's need'} your attention.</strong> See the suggestions below each status.
          </Alert>
        </div>
      )}

      {loading && !data ? <Skeleton count={2} /> : error ? <ErrorState error={error} onRetry={reload} /> : data.items.length === 0 ? (
        <EmptyState icon={ClipboardList} title={filter ? `No applications with status “${filter}”` : 'No applications tracked yet'}
          action={!filter && <Link className="btn btn-primary" to="/saved">Go to saved jobs</Link>}>
          Open a job posting, or choose “Track application” on a job, to add it here.
        </EmptyState>
      ) : (
        <div className="table-wrap">
          <table className="table table-responsive">
            <thead>
              <tr><th scope="col">Job</th><th scope="col">Company</th><th scope="col">Status</th><th scope="col">Applied</th><th scope="col">Notes</th><th scope="col">Updated</th><th scope="col"><span className="sr-only">Actions</span></th></tr>
            </thead>
            <tbody>
              {data.items.map((a) => (
                <Fragment key={a.application_id}>
                  <tr>
                    <td data-label="Job"><Link to={`/jobs/${a.job_id}`}>{a.title}</Link></td>
                    <td data-label="Company">{a.company}</td>
                    <td data-label="Status">
                      <div>
                        <label className="sr-only" htmlFor={`st-${a.application_id}`}>Status for {a.title}</label>
                        <select id={`st-${a.application_id}`} className="select" style={{ minHeight: 32, width: 'auto' }}
                          value={a.status} onChange={(e) => changeStatus(a, e.target.value)}>
                          {APPLICATION_STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
                        </select>
                        {a.reminder && (
                          <div className="reminder small">
                            <BellRing size={13} aria-hidden="true" /> {a.reminder.message}
                            {a.reminder.type === 'confirm_applied' && (
                              <button type="button" className="btn btn-sm btn-primary" style={{ marginTop: 6 }}
                                onClick={() => changeStatus(a, 'Applied')}>Yes, I applied</button>
                            )}
                          </div>
                        )}
                      </div>
                    </td>
                    <td data-label="Applied" className="nowrap">{formatDate(a.applied_date)}</td>
                    <td data-label="Notes" className="small muted" style={{ maxWidth: 240 }}>{a.notes || '—'}</td>
                    <td data-label="Updated" className="nowrap small">{formatDate(a.updated_at)}</td>
                    <td data-label="Actions">
                      <div className="row" style={{ flexWrap: 'nowrap' }}>
                        <button type="button" className="btn btn-ghost btn-icon" aria-expanded={expanded === a.application_id}
                          onClick={() => setExpanded(expanded === a.application_id ? null : a.application_id)}
                          aria-label={`History of application for ${a.title}`}><History size={15} /></button>
                        <button type="button" className="btn btn-ghost btn-icon" onClick={() => setEditing(a)} aria-label={`Edit application for ${a.title}`}><Pencil size={15} /></button>
                        <button type="button" className="btn btn-ghost btn-icon" onClick={() => setRemoving(a)} aria-label={`Remove application for ${a.title}`}><Trash2 size={15} /></button>
                      </div>
                    </td>
                  </tr>
                  {expanded === a.application_id && (
                    <tr className="timeline-row">
                      <td colSpan={7}>
                        {a.events.length === 0 ? <span className="small muted">No history recorded for this application yet.</span> : (
                          <ol className="timeline" aria-label={`History of application for ${a.title}`}>
                            {a.events.map((e) => (
                              <li key={e.event_id}>
                                <span className="timeline-date">{dateTime(e.created_at)}</span>
                                <span>{describeEvent(e)}</span>
                                {e.source === 'auto' && <span className="badge">Automatic</span>}
                              </li>
                            ))}
                          </ol>
                        )}
                      </td>
                    </tr>
                  )}
                </Fragment>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {editing && <ApplicationModal application={editing} onClose={() => setEditing(null)} onSaved={replaceItem} />}
      {removing && <ConfirmDialog title="Remove application?" danger confirmLabel="Remove" busy={busy}
        message={`Stop tracking your application for “${removing.title}”?`} onCancel={() => setRemoving(null)} onConfirm={doRemove} />}
    </div>
  );
}
