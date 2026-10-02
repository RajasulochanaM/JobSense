import { useState } from 'react';
import { applicationsApi } from '../services/api';
import { useToast } from '../context/ToastContext';
import { APPLICATION_STATUSES } from '../utils/format';
import { Modal, Spinner } from './ui';

const today = () => new Date().toISOString().slice(0, 10);

/** Create (job given) or edit (application given) an application record. */
export default function ApplicationModal({ job, application, onClose, onSaved }) {
  const toast = useToast();
  const editing = Boolean(application);
  const [form, setForm] = useState({
    status: application?.status || 'Applied',
    applied_date: application?.applied_date || today(),
    notes: application?.notes || '',
  });
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    if (form.applied_date && form.applied_date > today()) {
      setError('Applied date cannot be in the future');
      return;
    }
    setBusy(true);
    setError('');
    try {
      const payload = { ...form, applied_date: form.applied_date || null };
      const saved = editing
        ? await applicationsApi.update(application.application_id, payload)
        : await applicationsApi.create({ ...payload, job_id: job.job_id });
      toast.success(editing ? 'Application updated' : 'Application tracking started');
      onSaved?.(saved);
      onClose();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  const title = editing ? 'Update application' : 'Track application';
  return (
    <Modal title={title} onClose={onClose}>
      <p className="small muted" style={{ marginTop: -8 }}>{(job || application).title} · {(job || application).company}</p>
      <form onSubmit={submit} noValidate>
        <div className="field">
          <label htmlFor="app-status">Status</label>
          <select id="app-status" className="select" value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })}>
            {APPLICATION_STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>
        <div className="field">
          <label htmlFor="app-date">Applied date</label>
          <input id="app-date" type="date" className="input" max={today()} value={form.applied_date || ''}
            onChange={(e) => setForm({ ...form, applied_date: e.target.value })} aria-invalid={Boolean(error)} />
        </div>
        <div className="field">
          <label htmlFor="app-notes">Notes</label>
          <textarea id="app-notes" className="textarea" maxLength={2000} value={form.notes}
            placeholder="Recruiter name, interview dates, follow-ups…" onChange={(e) => setForm({ ...form, notes: e.target.value })} />
        </div>
        {error && <p className="field-error" role="alert">{error}</p>}
        <div className="modal-actions">
          <button type="button" className="btn btn-secondary" onClick={onClose}>Cancel</button>
          <button type="submit" className="btn btn-primary" disabled={busy}>{busy && <Spinner />} Save</button>
        </div>
      </form>
    </Modal>
  );
}
