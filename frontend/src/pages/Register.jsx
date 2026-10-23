import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { AlertCircle } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useDocumentTitle } from '../hooks/useAsync';
import { Alert, Spinner } from '../components/ui';

export function validateRegister({ name, email, password, password_confirmation }) {
  const errors = {};
  if (name.trim().length < 2) errors.name = 'Please enter your name';
  if (!/^\S+@\S+\.\S+$/.test(email.trim())) errors.email = 'Enter a valid email address';
  if (password.length < 8) errors.password = 'At least 8 characters';
  else if (!/[A-Za-z]/.test(password) || !/\d/.test(password)) errors.password = 'Use both letters and numbers';
  if (password_confirmation !== password) errors.password_confirmation = 'Passwords do not match';
  return errors;
}

const FIELDS = [
  { name: 'name', label: 'Full name', type: 'text', autoComplete: 'name' },
  { name: 'email', label: 'Email', type: 'email', autoComplete: 'email' },
  { name: 'password', label: 'Password', type: 'password', autoComplete: 'new-password', hint: 'At least 8 characters, with letters and numbers.' },
  { name: 'password_confirmation', label: 'Confirm password', type: 'password', autoComplete: 'new-password' },
];

export default function Register() {
  useDocumentTitle('Create account');
  const { register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ name: '', email: '', password: '', password_confirmation: '' });
  const [errors, setErrors] = useState({});
  const [serverError, setServerError] = useState('');
  const [busy, setBusy] = useState(false);

  const onSubmit = async (e) => {
    e.preventDefault();
    const v = validateRegister(form);
    setErrors(v);
    setServerError('');
    if (Object.keys(v).length) return;
    setBusy(true);
    try {
      await register({ ...form, name: form.name.trim(), email: form.email.trim() });
      navigate('/profile?welcome=1', { replace: true });
    } catch (err) {
      setServerError(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="card auth-card">
        <h1>Create your account</h1>
        <p className="muted">Analyse your resume and discover relevant roles.</p>
        {serverError && <Alert type="error" icon={AlertCircle}>{serverError}</Alert>}
        <form onSubmit={onSubmit} noValidate style={{ marginTop: 16 }}>
          {FIELDS.map((f) => (
            <div className="field" key={f.name}>
              <label htmlFor={f.name}>{f.label}</label>
              <input id={f.name} name={f.name} type={f.type} className="input" autoComplete={f.autoComplete}
                value={form[f.name]} onChange={(e) => setForm((s) => ({ ...s, [f.name]: e.target.value }))}
                aria-invalid={Boolean(errors[f.name])}
                aria-describedby={errors[f.name] ? `${f.name}-error` : f.hint ? `${f.name}-hint` : undefined} />
              {errors[f.name]
                ? <span id={`${f.name}-error`} className="field-error">{errors[f.name]}</span>
                : f.hint && <span id={`${f.name}-hint`} className="hint">{f.hint}</span>}
            </div>
          ))}
          <button type="submit" className="btn btn-primary btn-block" disabled={busy}>
            {busy && <Spinner />} Create account
          </button>
        </form>
        <p className="small muted" style={{ marginTop: 16, marginBottom: 0 }}>
          Already registered? <Link to="/login">Log in</Link>
        </p>
      </div>
    </div>
  );
}
