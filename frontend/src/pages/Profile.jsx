import { useEffect, useMemo, useRef, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { Camera, CheckCircle2, Plus, Trash2, X } from 'lucide-react';
import { profileApi } from '../services/api';
import { useAsync, useDocumentTitle } from '../hooks/useAsync';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import Avatar from '../components/Avatar';
import { Alert, ErrorState, Meter, PageHeader, Skeleton, Spinner } from '../components/ui';

const REMOTE_LABELS = { any: 'No preference', remote: 'Remote', hybrid: 'Hybrid', onsite: 'On-site' };
const SOCIALS = {
  linkedin: { label: 'LinkedIn', placeholder: 'https://linkedin.com/in/your-name' },
  github: { label: 'GitHub', placeholder: 'https://github.com/username' },
  portfolio: { label: 'Portfolio / website', placeholder: 'https://your-site.com' },
  twitter: { label: 'X (Twitter)', placeholder: 'https://x.com/username' },
  stackoverflow: { label: 'Stack Overflow', placeholder: 'https://stackoverflow.com/users/…' },
  behance: { label: 'Behance / Dribbble', placeholder: 'https://behance.net/username' },
};
const MAX_INTERESTS = 25;
const MAX_PHOTO_MB = 10;

/** Centre-crop and downscale a photo to a small square JPEG data URL before upload. */
async function resizeImage(file, size = 256) {
  const url = URL.createObjectURL(file);
  try {
    const img = await new Promise((resolve, reject) => {
      const el = new Image();
      el.onload = () => resolve(el);
      el.onerror = () => reject(new Error('That file could not be read as an image'));
      el.src = url;
    });
    const side = Math.min(img.naturalWidth, img.naturalHeight);
    const canvas = document.createElement('canvas');
    canvas.width = size;
    canvas.height = size;
    canvas.getContext('2d').drawImage(img, (img.naturalWidth - side) / 2, (img.naturalHeight - side) / 2, side, side, 0, 0, size, size);
    return canvas.toDataURL('image/jpeg', 0.85);
  } finally {
    URL.revokeObjectURL(url);
  }
}

function PhotoCard({ data, onChange }) {
  const toast = useToast();
  const inputRef = useRef(null);
  const [busy, setBusy] = useState(false);
  const user = { name: data.user.name, avatar_image: data.profile.avatar_image, avatar_color: data.profile.avatar_color };

  const run = async (fn, message) => {
    setBusy(true);
    try {
      onChange(await fn());
      if (message) toast.success(message);
    } catch (err) {
      toast.error(err.message);
    } finally {
      setBusy(false);
      if (inputRef.current) inputRef.current.value = '';
    }
  };

  const onFile = (file) => {
    if (!file) return;
    if (!file.type.startsWith('image/')) { toast.error('Please choose an image file'); return; }
    if (file.size > MAX_PHOTO_MB * 1024 * 1024) { toast.error(`Image must be under ${MAX_PHOTO_MB} MB`); return; }
    run(async () => profileApi.uploadAvatar(await resizeImage(file)), 'Profile picture updated');
  };

  return (
    <section className="card" aria-labelledby="photo-title">
      <h2 id="photo-title">Profile picture</h2>
      <div className="row" style={{ gap: '1rem', flexWrap: 'nowrap' }}>
        <Avatar user={user} size={72} className="avatar-lg" />
        <div className="stack" style={{ minWidth: 0 }}>
          <div className="row">
            <label className={`btn btn-secondary btn-sm ${busy ? 'disabled' : ''}`}>
              {busy ? <Spinner dark /> : <Camera size={15} aria-hidden="true" />} {user.avatar_image ? 'Change photo' : 'Upload photo'}
              <input ref={inputRef} type="file" accept="image/png,image/jpeg,image/webp" className="sr-only" disabled={busy}
                onChange={(e) => onFile(e.target.files?.[0])} />
            </label>
            {user.avatar_image && (
              <button type="button" className="btn btn-ghost btn-sm" disabled={busy}
                onClick={() => run(() => profileApi.removeAvatar(), 'Photo removed - using your avatar')}>
                <Trash2 size={15} aria-hidden="true" /> Use avatar
              </button>
            )}
          </div>
          <p className="small muted" style={{ margin: 0 }}>PNG, JPEG or WebP. Or skip the photo and keep an initials avatar.</p>
        </div>
      </div>
      {!user.avatar_image && (
        <fieldset className="field" style={{ border: 0, padding: 0, margin: '0.9rem 0 0' }}>
          <legend className="label" style={{ marginBottom: 6 }}>Avatar colour</legend>
          <div className="toggle-group">
            {data.options.avatar_colors.map((c) => (
              <button key={c} type="button" className={`avatar-swatch avatar-${c}`} aria-label={c} disabled={busy}
                aria-pressed={(user.avatar_color || 'burgundy') === c}
                onClick={() => run(() => profileApi.update({ avatar_color: c }))} />
            ))}
          </div>
        </fieldset>
      )}
    </section>
  );
}

function InterestPicker({ groups, value, onChange }) {
  const [query, setQuery] = useState('');
  const all = useMemo(() => groups.flatMap((g) => g.interests), [groups]);
  const selected = new Set(value.map((i) => i.toLowerCase()));
  const q = query.trim().toLowerCase();
  const full = value.length >= MAX_INTERESTS;

  const toggle = (interest) => onChange(selected.has(interest.toLowerCase())
    ? value.filter((i) => i.toLowerCase() !== interest.toLowerCase())
    : full ? value : [...value, interest]);

  const addCustom = () => {
    const text = query.trim().replace(/\s+/g, ' ');
    if (!text || full) return;
    const known = all.find((i) => i.toLowerCase() === text.toLowerCase());
    if (!selected.has(text.toLowerCase())) onChange([...value, known || text]);
    setQuery('');
  };

  const filtered = groups
    .map((g) => ({ ...g, interests: g.interests.filter((i) => !q || i.toLowerCase().includes(q)) }))
    .filter((g) => g.interests.length);
  const exact = all.some((i) => i.toLowerCase() === q);

  return (
    <fieldset className="field" style={{ border: 0, padding: 0 }}>
      <legend className="label" style={{ marginBottom: 6 }}>Interests <span className="muted">({value.length}/{MAX_INTERESTS})</span></legend>
      {value.length > 0 && (
        <ul className="chips list-plain" aria-label="Selected interests" style={{ marginBottom: 10 }}>
          {value.map((i) => (
            <li key={i} className="chip chip-highlight">
              {i}<button type="button" onClick={() => toggle(i)} aria-label={`Remove ${i}`}><X size={13} /></button>
            </li>
          ))}
        </ul>
      )}
      <div className="row" style={{ flexWrap: 'nowrap', marginBottom: 10 }}>
        <label htmlFor="interest-q" className="sr-only">Search or add an interest</label>
        <input id="interest-q" className="input" placeholder="Search or add your own, e.g. Electrical, Medical" value={query}
          maxLength={60} onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); addCustom(); } }} />
        <button type="button" className="btn btn-secondary" onClick={addCustom} disabled={!q || full || selected.has(q)}
          aria-label="Add interest"><Plus size={16} /></button>
      </div>
      <div className="interest-groups">
        {filtered.map((g) => (
          <details key={g.group} open={Boolean(q) || g.interests.some((i) => selected.has(i.toLowerCase())) || undefined}>
            <summary>{g.group}</summary>
            <div className="toggle-group">
              {g.interests.map((i) => {
                const on = selected.has(i.toLowerCase());
                return (
                  <button key={i} type="button" className="toggle-chip" aria-pressed={on} disabled={!on && full} onClick={() => toggle(i)}>
                    {on && <span aria-hidden="true">✓</span>}{i}
                  </button>
                );
              })}
            </div>
          </details>
        ))}
        {q && !exact && (
          <p className="small muted" style={{ margin: '6px 0 0' }}>Press Enter to add “{query.trim()}” as a custom interest.</p>
        )}
      </div>
      <span className="hint">A secondary signal for career recommendations - your skills always carry more weight.</span>
    </fieldset>
  );
}

export default function Profile() {
  useDocumentTitle('Profile');
  const [params] = useSearchParams();
  const toast = useToast();
  const { updateUser } = useAuth();
  const { data, loading, error, reload, setData } = useAsync(() => profileApi.get(), []);
  const taxonomy = useAsync(() => profileApi.taxonomy(), []);
  const [form, setForm] = useState(null);
  const [errors, setErrors] = useState({});
  const [saving, setSaving] = useState(false);
  const [newSkill, setNewSkill] = useState('');
  const [skillBusy, setSkillBusy] = useState(false);

  // Initialise the form once; later data updates (avatar, skills) must not discard unsaved edits.
  useEffect(() => {
    if (!data || form) return;
    setForm({
      name: data.user.name,
      headline: data.profile.headline || '',
      experience_years: data.profile.experience_years ?? '',
      experience_summary: data.profile.experience_summary || '',
      education: data.profile.education || '',
      location: data.profile.location || '',
      preferred_locations: data.profile.preferred_locations || '',
      remote_preference: data.profile.remote_preference || 'any',
      social_links: Object.fromEntries(data.options.social_links.map((k) => [k, data.profile.social_links?.[k] || ''])),
      interests: data.interests,
    });
  }, [data, form]);

  if (loading && !data) return <Skeleton count={3} />;
  if (error) return <ErrorState error={error} onRetry={reload} />;
  if (!form) return null;

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));
  const setSocial = (k) => (e) => setForm((f) => ({ ...f, social_links: { ...f.social_links, [k]: e.target.value } }));

  const onAvatarChange = (updated) => {
    setData(updated);
    updateUser({ avatar_image: updated.profile.avatar_image, avatar_color: updated.profile.avatar_color });
  };

  const save = async (e) => {
    e.preventDefault();
    const v = {};
    if (form.name.trim().length < 2) v.name = 'Please enter your name';
    if (form.experience_years !== '' && (Number.isNaN(Number(form.experience_years)) || Number(form.experience_years) < 0 || Number(form.experience_years) > 60)) {
      v.experience_years = 'Enter a number between 0 and 60';
    }
    setErrors(v);
    if (Object.keys(v).length) return;
    setSaving(true);
    try {
      const updated = await profileApi.update({ ...form, experience_years: form.experience_years === '' ? null : Number(form.experience_years) });
      setData(updated);
      setForm((f) => ({
        ...f,
        interests: updated.interests,
        social_links: Object.fromEntries(updated.options.social_links.map((k) => [k, updated.profile.social_links?.[k] || ''])),
      }));
      updateUser({ name: updated.user.name });
      toast.success('Profile saved');
    } catch (err) {
      if (err.details) setErrors(Object.fromEntries(Object.keys(err.details).map((k) => [k, err.message])));
      toast.error(err.message);
    } finally {
      setSaving(false);
    }
  };

  const addSkill = async (e) => {
    e.preventDefault();
    if (!newSkill.trim()) return;
    setSkillBusy(true);
    try {
      const res = await profileApi.addSkill(newSkill.trim());
      setData((d) => ({ ...d, skills: res.items }));
      setNewSkill('');
      toast.success('Skill added - matches will be recalculated');
    } catch (err) {
      toast.error(err.message);
    } finally {
      setSkillBusy(false);
    }
  };

  const removeSkill = async (skill) => {
    try {
      const res = await profileApi.removeSkill(skill.skill_id);
      setData((d) => ({ ...d, skills: res.items }));
    } catch (err) {
      toast.error(err.message);
    }
  };

  const allSkills = taxonomy.data?.categories.flatMap((c) => c.skills) || [];

  return (
    <div>
      <PageHeader title="Profile" description="Details used for career recommendations and job searches." />
      {params.get('welcome') && (
        <div style={{ marginBottom: '1rem' }}>
          <Alert type="success" icon={CheckCircle2}>
            Welcome to JobSense! Complete your profile below, then <Link to="/resume">upload your resume</Link> to get personalised matches.
          </Alert>
        </div>
      )}

      <div className="split-2-1">
        <form className="card" onSubmit={save} noValidate aria-labelledby="details-title">
          <h2 id="details-title">Your details</h2>
          <div className="grid grid-2">
            <div className="field">
              <label htmlFor="name">Name</label>
              <input id="name" className="input" value={form.name} onChange={set('name')} aria-invalid={Boolean(errors.name)} maxLength={120} />
              {errors.name && <span className="field-error">{errors.name}</span>}
            </div>
            <div className="field">
              <label htmlFor="email">Email</label>
              <input id="email" className="input" value={data.user.email} disabled readOnly />
              <span className="hint">Email and role cannot be changed here.</span>
            </div>
            <div className="field">
              <label htmlFor="headline">Headline</label>
              <input id="headline" className="input" placeholder="e.g. Frontend developer" value={form.headline} onChange={set('headline')} maxLength={160} />
            </div>
            <div className="field">
              <label htmlFor="exp">Experience (years)</label>
              <input id="exp" className="input" inputMode="decimal" value={form.experience_years} onChange={set('experience_years')}
                aria-invalid={Boolean(errors.experience_years)} />
              {errors.experience_years && <span className="field-error">{errors.experience_years}</span>}
            </div>
          </div>
          <div className="field">
            <label htmlFor="expsum">Experience summary</label>
            <textarea id="expsum" className="textarea" value={form.experience_summary} onChange={set('experience_summary')} maxLength={4000} />
          </div>
          <div className="field">
            <label htmlFor="edu">Education</label>
            <textarea id="edu" className="textarea" style={{ minHeight: 70 }} placeholder="e.g. B.Tech Computer Science, Anna University (2022)" value={form.education} onChange={set('education')} maxLength={4000} />
          </div>
          <div className="grid grid-2">
            <div className="field">
              <label htmlFor="loc">Current location</label>
              <input id="loc" className="input" placeholder="e.g. Chennai" value={form.location} onChange={set('location')} maxLength={120} />
            </div>
            <div className="field">
              <label htmlFor="ploc">Preferred locations</label>
              <input id="ploc" className="input" placeholder="e.g. Bengaluru, Hyderabad" value={form.preferred_locations} onChange={set('preferred_locations')} maxLength={500} />
              <span className="hint">Comma separated. Used when fetching jobs for your profile.</span>
            </div>
          </div>
          <div className="field">
            <label htmlFor="remote">Remote preference</label>
            <select id="remote" className="select" value={form.remote_preference} onChange={set('remote_preference')}>
              {data.options.remote_preferences.map((r) => <option key={r} value={r}>{REMOTE_LABELS[r]}</option>)}
            </select>
          </div>

          <fieldset className="field" style={{ border: 0, padding: 0 }}>
            <legend className="label" style={{ marginBottom: 6 }}>Social links</legend>
            <div className="grid grid-2">
              {data.options.social_links.map((k) => (
                <div className="field" key={k} style={{ marginBottom: 0 }}>
                  <label htmlFor={`social-${k}`}>{SOCIALS[k]?.label || k}</label>
                  <input id={`social-${k}`} type="url" className="input" placeholder={SOCIALS[k]?.placeholder}
                    value={form.social_links[k]} onChange={setSocial(k)} maxLength={255} aria-invalid={Boolean(errors[k])} />
                  {errors[k] && <span className="field-error">{errors[k]}</span>}
                </div>
              ))}
            </div>
          </fieldset>

          <InterestPicker groups={data.options.interest_groups} value={form.interests}
            onChange={(interests) => setForm((f) => ({ ...f, interests }))} />
          <button type="submit" className="btn btn-primary" disabled={saving}>{saving && <Spinner />} Save profile</button>
        </form>

        <div className="stack">
          <PhotoCard data={data} onChange={onAvatarChange} />

          <section className="card" aria-labelledby="complete-title">
            <h2 id="complete-title">Profile completeness</h2>
            <p className="small muted">{data.completeness.percent}% complete</p>
            <Meter value={data.completeness.percent} label="Profile completeness" />
          </section>

          <section className="card" aria-labelledby="skills-title">
            <h2 id="skills-title">Skills</h2>
            <p className="small muted">Skills from your resume, plus any you add manually.</p>
            <ul className="chips list-plain" aria-label="Your skills">
              {data.skills.map((s) => (
                <li key={s.skill_id} className={`chip ${s.source === 'manual' ? 'chip-highlight' : ''}`}>
                  {s.skill_name}
                  <button type="button" onClick={() => removeSkill(s)} aria-label={`Remove ${s.skill_name}`}><X size={13} /></button>
                </li>
              ))}
              {data.skills.length === 0 && <li className="small muted">No skills yet.</li>}
            </ul>
            <form onSubmit={addSkill} className="row" style={{ marginTop: 12, flexWrap: 'nowrap' }}>
              <label htmlFor="new-skill" className="sr-only">Add a skill</label>
              <input id="new-skill" className="input" list="skill-options" placeholder="Add a skill" value={newSkill}
                onChange={(e) => setNewSkill(e.target.value)} maxLength={80} />
              <datalist id="skill-options">{allSkills.map((s) => <option key={s} value={s} />)}</datalist>
              <button type="submit" className="btn btn-secondary" disabled={skillBusy} aria-label="Add skill"><Plus size={16} /></button>
            </form>
            {!data.has_resume && <p className="small" style={{ marginTop: 10 }}><Link to="/resume">Upload a resume</Link> to extract skills automatically.</p>}
          </section>
        </div>
      </div>
    </div>
  );
}
