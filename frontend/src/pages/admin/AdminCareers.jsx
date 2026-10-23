import { useState } from 'react';
import { Compass, Pencil, Plus, Trash2, X } from 'lucide-react';
import { adminApi, profileApi } from '../../services/api';
import { useAsync, useDocumentTitle } from '../../hooks/useAsync';
import { useToast } from '../../context/ToastContext';
import { ConfirmDialog, EmptyState, ErrorState, Modal, PageHeader, Skeleton, Spinner } from '../../components/ui';

const IMPORTANCE = { 3: 'Core', 2: 'Important', 1: 'Nice to have' };

function CareerForm({ career, skillOptions, onClose, onSaved }) {
  const toast = useToast();
  const [form, setForm] = useState({
    career_name: career?.career_name || '', description: career?.description || '', interest_area: career?.interest_area || '',
    skills: career?.skills.map((s) => ({ skill_name: s.skill_name, importance: s.importance })) || [],
  });
  const [skill, setSkill] = useState({ skill_name: '', importance: 2 });
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const interests = useAsync(() => profileApi.interests(), []);

  const addSkill = () => {
    const name = skill.skill_name.trim();
    if (!name) return;
    if (form.skills.some((s) => s.skill_name.toLowerCase() === name.toLowerCase())) { setError('Skill already added'); return; }
    setForm({ ...form, skills: [...form.skills, { skill_name: name, importance: Number(skill.importance) }] });
    setSkill({ skill_name: '', importance: 2 });
    setError('');
  };

  const submit = async (e) => {
    e.preventDefault();
    if (!form.career_name.trim() || !form.description.trim()) { setError('Name and description are required'); return; }
    if (form.skills.length === 0) { setError('Add at least one skill'); return; }
    setBusy(true);
    try {
      if (career) await adminApi.updateCareer(career.career_id, form);
      else await adminApi.createCareer(form);
      toast.success(career ? 'Career path updated' : 'Career path created');
      onSaved();
      onClose();
    } catch (err) { setError(err.message); } finally { setBusy(false); }
  };

  return (
    <Modal title={career ? 'Edit career path' : 'New career path'} onClose={onClose}>
      <form onSubmit={submit} noValidate>
        <div className="field"><label htmlFor="cn">Career name</label>
          <input id="cn" className="input" maxLength={120} value={form.career_name} onChange={(e) => setForm({ ...form, career_name: e.target.value })} /></div>
        <div className="field"><label htmlFor="cd">Description</label>
          <textarea id="cd" className="textarea" maxLength={2000} value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} /></div>
        <div className="field"><label htmlFor="ci">Interest area</label>
          <select id="ci" className="select" value={form.interest_area} onChange={(e) => setForm({ ...form, interest_area: e.target.value })}>
            <option value="">None</option>
            {interests.data?.groups.map((g) => (
              <optgroup key={g.group} label={g.group}>{g.interests.map((i) => <option key={i}>{i}</option>)}</optgroup>
            ))}
          </select></div>
        <fieldset className="field" style={{ border: 0, padding: 0 }}>
          <legend className="label">Required skills</legend>
          <ul className="chips list-plain" style={{ margin: '6px 0 10px' }}>
            {form.skills.map((s) => (
              <li key={s.skill_name} className="chip">{s.skill_name} · {IMPORTANCE[s.importance]}
                <button type="button" aria-label={`Remove ${s.skill_name}`} onClick={() => setForm({ ...form, skills: form.skills.filter((x) => x !== s) })}><X size={13} /></button>
              </li>
            ))}
          </ul>
          <div className="row" style={{ flexWrap: 'nowrap' }}>
            <label htmlFor="sk" className="sr-only">Skill name</label>
            <input id="sk" className="input" list="career-skill-options" placeholder="Skill" value={skill.skill_name}
              onChange={(e) => setSkill({ ...skill, skill_name: e.target.value })}
              onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); addSkill(); } }} />
            <datalist id="career-skill-options">{skillOptions.map((s) => <option key={s} value={s} />)}</datalist>
            <label htmlFor="imp" className="sr-only">Importance</label>
            <select id="imp" className="select" style={{ width: 'auto' }} value={skill.importance} onChange={(e) => setSkill({ ...skill, importance: e.target.value })}>
              {[3, 2, 1].map((i) => <option key={i} value={i}>{IMPORTANCE[i]}</option>)}
            </select>
            <button type="button" className="btn btn-secondary" onClick={addSkill} aria-label="Add skill"><Plus size={16} /></button>
          </div>
        </fieldset>
        {error && <p className="field-error" role="alert">{error}</p>}
        <div className="modal-actions">
          <button type="button" className="btn btn-secondary" onClick={onClose}>Cancel</button>
          <button type="submit" className="btn btn-primary" disabled={busy}>{busy && <Spinner />} Save</button>
        </div>
      </form>
    </Modal>
  );
}

export default function AdminCareers() {
  useDocumentTitle('Career management');
  const toast = useToast();
  const { data, loading, error, reload } = useAsync(() => adminApi.careers(), []);
  const taxonomy = useAsync(() => profileApi.taxonomy(), []);
  const [editing, setEditing] = useState(null);
  const [deleting, setDeleting] = useState(null);
  const [busy, setBusy] = useState(false);
  const skillOptions = taxonomy.data?.categories.flatMap((c) => c.skills) || [];

  const doDelete = async () => {
    setBusy(true);
    try {
      await adminApi.deleteCareer(deleting.career_id);
      toast.success('Career path deleted');
      setDeleting(null);
      reload({ silent: true });
    } catch (err) { toast.error(err.message); } finally { setBusy(false); }
  };

  return (
    <div>
      <PageHeader title="Career paths" description="Career roles and their required skills used for career recommendations."
        actions={<button type="button" className="btn btn-primary" onClick={() => setEditing('new')}><Plus size={16} aria-hidden="true" /> New career path</button>} />
      {loading && !data ? <Skeleton count={3} /> : error ? <ErrorState error={error} onRetry={reload} /> : data.items.length === 0 ? (
        <EmptyState icon={Compass} title="No career paths" />
      ) : (
        <div className="grid grid-2">
          {data.items.map((c) => (
            <article key={c.career_id} className="card">
              <div className="row-between">
                <h2 style={{ margin: 0 }}>{c.career_name}</h2>
                <div className="row" style={{ flexWrap: 'nowrap' }}>
                  <button type="button" className="btn btn-ghost btn-icon" onClick={() => setEditing(c)} aria-label={`Edit ${c.career_name}`}><Pencil size={15} /></button>
                  <button type="button" className="btn btn-ghost btn-icon" onClick={() => setDeleting(c)} aria-label={`Delete ${c.career_name}`}><Trash2 size={15} /></button>
                </div>
              </div>
              {c.interest_area && <span className="badge badge-burgundy">{c.interest_area}</span>}
              <p className="small muted" style={{ marginTop: 8 }}>{c.description}</p>
              <ul className="chips list-plain">
                {c.skills.map((s) => <li key={s.skill_name} className={`chip ${s.importance === 3 ? 'chip-highlight' : ''}`}>{s.skill_name}{s.importance === 3 ? ' · core' : ''}</li>)}
              </ul>
            </article>
          ))}
        </div>
      )}
      {editing && <CareerForm career={editing === 'new' ? null : editing} skillOptions={skillOptions} onClose={() => setEditing(null)} onSaved={() => reload({ silent: true })} />}
      {deleting && <ConfirmDialog title="Delete career path?" danger confirmLabel="Delete" busy={busy} onCancel={() => setDeleting(null)} onConfirm={doDelete}
        message={`“${deleting.career_name}”, its skills and all candidate recommendations for it will be removed.`} />}
    </div>
  );
}
