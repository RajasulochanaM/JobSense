import { useState } from 'react';
import { BookOpen, ExternalLink, Pencil, Plus, Trash2 } from 'lucide-react';
import { adminApi, learningApi } from '../../services/api';
import { useAsync, useDebounce, useDocumentTitle } from '../../hooks/useAsync';
import { useToast } from '../../context/ToastContext';
import { ConfirmDialog, EmptyState, ErrorState, Modal, PageHeader, Skeleton, Spinner } from '../../components/ui';

const TYPES = ['documentation', 'guide', 'tutorial', 'reference', 'course'];
const EMPTY = { skill_name: '', resource_name: '', resource_url: '', description: '', resource_type: 'documentation' };

function ResourceForm({ resource, onClose, onSaved }) {
  const toast = useToast();
  const [form, setForm] = useState(resource ? { ...EMPTY, ...resource, description: resource.description || '' } : EMPTY);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  const submit = async (e) => {
    e.preventDefault();
    if (!form.skill_name.trim() || !form.resource_name.trim()) { setError('Skill and resource name are required'); return; }
    if (!/^https?:\/\/\S+\.\S+/.test(form.resource_url)) { setError('Enter a valid http(s) URL'); return; }
    setBusy(true);
    try {
      if (resource) await adminApi.updateResource(resource.resource_id, form);
      else await adminApi.createResource(form);
      toast.success(resource ? 'Resource updated' : 'Resource created');
      onSaved();
      onClose();
    } catch (err) { setError(err.message); } finally { setBusy(false); }
  };

  return (
    <Modal title={resource ? 'Edit learning resource' : 'New learning resource'} onClose={onClose}>
      <form onSubmit={submit} noValidate>
        <div className="grid grid-2">
          <div className="field"><label htmlFor="rs">Skill</label><input id="rs" className="input" value={form.skill_name} onChange={set('skill_name')} maxLength={80} /></div>
          <div className="field"><label htmlFor="rt">Type</label>
            <select id="rt" className="select" value={form.resource_type} onChange={set('resource_type')}>{TYPES.map((t) => <option key={t}>{t}</option>)}</select></div>
        </div>
        <div className="field"><label htmlFor="rn">Resource name</label><input id="rn" className="input" value={form.resource_name} onChange={set('resource_name')} maxLength={200} /></div>
        <div className="field"><label htmlFor="ru">URL</label><input id="ru" type="url" className="input" placeholder="https://" value={form.resource_url} onChange={set('resource_url')} maxLength={500} /></div>
        <div className="field"><label htmlFor="rd">Description</label><textarea id="rd" className="textarea" style={{ minHeight: 70 }} value={form.description} onChange={set('description')} maxLength={500} /></div>
        {error && <p className="field-error" role="alert">{error}</p>}
        <div className="modal-actions">
          <button type="button" className="btn btn-secondary" onClick={onClose}>Cancel</button>
          <button type="submit" className="btn btn-primary" disabled={busy}>{busy && <Spinner />} Save</button>
        </div>
      </form>
    </Modal>
  );
}

export default function AdminResources() {
  useDocumentTitle('Learning resources');
  const toast = useToast();
  const [q, setQ] = useState('');
  const dq = useDebounce(q, 300);
  const { data, loading, error, reload } = useAsync(() => learningApi.list({ q: dq, limit: 500 }), [dq]);
  const [editing, setEditing] = useState(null);
  const [deleting, setDeleting] = useState(null);
  const [busy, setBusy] = useState(false);

  const doDelete = async () => {
    setBusy(true);
    try {
      await adminApi.deleteResource(deleting.resource_id);
      toast.success('Resource deleted');
      setDeleting(null);
      reload({ silent: true });
    } catch (err) { toast.error(err.message); } finally { setBusy(false); }
  };

  return (
    <div>
      <PageHeader title="Learning resources" description="Official documentation and trusted references recommended for missing skills."
        actions={<button type="button" className="btn btn-primary" onClick={() => setEditing('new')}><Plus size={16} aria-hidden="true" /> New resource</button>} />
      <div className="card" style={{ marginBottom: '1rem' }}>
        <div className="field" style={{ marginBottom: 0 }}>
          <label htmlFor="rq">Search by skill or name</label>
          <input id="rq" className="input" value={q} onChange={(e) => setQ(e.target.value)} />
        </div>
      </div>
      {loading && !data ? <Skeleton /> : error ? <ErrorState error={error} onRetry={reload} /> : data.items.length === 0 ? (
        <EmptyState icon={BookOpen} title="No resources found" />
      ) : (
        <div className="table-wrap">
          <table className="table table-responsive">
            <thead><tr><th scope="col">Skill</th><th scope="col">Resource</th><th scope="col">Type</th><th scope="col"><span className="sr-only">Actions</span></th></tr></thead>
            <tbody>
              {data.items.map((r) => (
                <tr key={r.resource_id}>
                  <td data-label="Skill"><strong>{r.skill_name}</strong></td>
                  <td data-label="Resource">
                    <a href={r.resource_url} target="_blank" rel="noopener noreferrer">{r.resource_name} <ExternalLink size={12} aria-hidden="true" /><span className="sr-only">(opens in a new tab)</span></a>
                    <div className="small muted">{r.description}</div>
                  </td>
                  <td data-label="Type"><span className="badge">{r.resource_type}</span></td>
                  <td data-label="Actions">
                    <div className="row" style={{ flexWrap: 'nowrap' }}>
                      <button type="button" className="btn btn-ghost btn-icon" onClick={() => setEditing(r)} aria-label={`Edit ${r.resource_name}`}><Pencil size={15} /></button>
                      <button type="button" className="btn btn-ghost btn-icon" onClick={() => setDeleting(r)} aria-label={`Delete ${r.resource_name}`}><Trash2 size={15} /></button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {editing && <ResourceForm resource={editing === 'new' ? null : editing} onClose={() => setEditing(null)} onSaved={() => reload({ silent: true })} />}
      {deleting && <ConfirmDialog title="Delete resource?" danger confirmLabel="Delete" busy={busy} onCancel={() => setDeleting(null)} onConfirm={doDelete}
        message={`Remove “${deleting.resource_name}” (${deleting.skill_name})?`} />}
    </div>
  );
}
