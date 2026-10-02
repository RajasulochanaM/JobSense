/* Small, reusable presentational components. */
import { useEffect, useRef } from 'react';
import { AlertCircle, Inbox, RefreshCw, X } from 'lucide-react';
import { pct, scoreBand } from '../utils/format';

export function PageHeader({ title, description, actions }) {
  return (
    <header className="page-header">
      <div>
        <h1>{title}</h1>
        {description && <p>{description}</p>}
      </div>
      {actions && <div className="row">{actions}</div>}
    </header>
  );
}

export function Spinner({ dark = false, label = 'Loading' }) {
  return <span className={`spinner ${dark ? 'spinner-dark' : ''}`} role="status" aria-label={label} />;
}

export function Skeleton({ lines = 3, card = false, count = 1 }) {
  return (
    <div aria-busy="true" aria-label="Loading content">
      {Array.from({ length: count }).map((_, i) => (card
        ? <div key={i} className="skeleton skeleton-card" style={{ marginBottom: 12 }} />
        : (
          <div key={i} className="card" style={{ marginBottom: 12 }}>
            {Array.from({ length: lines }).map((__, j) => (
              <div key={j} className="skeleton skeleton-line" style={{ width: `${90 - j * 15}%` }} />
            ))}
          </div>
        )))}
    </div>
  );
}

export function EmptyState({ icon: Icon = Inbox, title, children, action }) {
  return (
    <div className="empty">
      <div className="empty-icon"><Icon size={22} aria-hidden="true" /></div>
      <h3>{title}</h3>
      {children && <p>{children}</p>}
      {action}
    </div>
  );
}

export function ErrorState({ error, onRetry, title = 'Something went wrong' }) {
  return (
    <div className="alert alert-error" role="alert">
      <AlertCircle size={18} aria-hidden="true" />
      <div style={{ flex: 1 }}>
        <strong>{title}</strong>
        <div>{error?.message || 'Please try again.'}</div>
      </div>
      {onRetry && (
        <button type="button" className="btn btn-sm btn-secondary" onClick={() => onRetry()}>
          <RefreshCw size={14} aria-hidden="true" /> Retry
        </button>
      )}
    </div>
  );
}

export function Alert({ type = 'info', icon: Icon, children }) {
  return (
    <div className={`alert alert-${type}`} role={type === 'error' ? 'alert' : undefined}>
      {Icon && <Icon size={18} aria-hidden="true" />}
      <div>{children}</div>
    </div>
  );
}

export function ScoreBadge({ score, label = 'Match' }) {
  const band = scoreBand(score);
  return (
    <div className={`score score-${band.key}`} title={band.label} aria-label={`${label} score ${pct(score)} - ${band.label}`}>
      <span className="score-value">{pct(score)}</span>
      <span className="score-label">{label}</span>
    </div>
  );
}

export function Meter({ value, variant = '', label }) {
  const v = Math.max(0, Math.min(100, Number(value) || 0));
  return (
    <div className={`meter ${variant ? `meter-${variant}` : ''}`} role="meter" aria-valuemin={0} aria-valuemax={100}
      aria-valuenow={Math.round(v)} aria-label={label}>
      <span style={{ width: `${v}%` }} />
    </div>
  );
}

export function MetricRow({ label, value, variant }) {
  return (
    <div className="metric-row">
      <span className="muted">{label}</span>
      <Meter value={value ?? 0} variant={variant} label={label} />
      <strong>{value === null || value === undefined ? 'N/A' : pct(value)}</strong>
    </div>
  );
}

/** Matched skills get a check mark and missing skills a hollow circle, so status never relies on colour alone. */
export function SkillChips({ skills = [], variant = 'default', limit, emptyText = 'None' }) {
  if (!skills.length) return <span className="muted small">{emptyText}</span>;
  const shown = limit ? skills.slice(0, limit) : skills;
  const rest = skills.length - shown.length;
  const mark = variant === 'matched' ? '✓ ' : variant === 'missing' ? '○ ' : '';
  return (
    <ul className="chips list-plain" aria-label={variant === 'matched' ? 'Matched skills' : variant === 'missing' ? 'Missing skills' : 'Skills'}>
      {shown.map((s) => (
        <li key={typeof s === 'string' ? s : s.skill} className={`chip chip-${variant}`}>
          <span aria-hidden="true">{mark}</span>{typeof s === 'string' ? s : s.skill}
        </li>
      ))}
      {rest > 0 && <li className="chip">+{rest} more</li>}
    </ul>
  );
}

export function StatCard({ icon: Icon, label, value, sub }) {
  return (
    <div className="card stat-card">
      <div className="stat-label">{Icon && <Icon size={16} aria-hidden="true" />}{label}</div>
      <div className="stat-value">{value}</div>
      {sub && <div className="stat-sub">{sub}</div>}
    </div>
  );
}

export function Modal({ title, onClose, children, footer }) {
  const ref = useRef(null);
  useEffect(() => {
    const prev = document.activeElement;
    ref.current?.querySelector('input, select, textarea, button')?.focus();
    const onKey = (e) => { if (e.key === 'Escape') onClose(); };
    document.addEventListener('keydown', onKey);
    return () => { document.removeEventListener('keydown', onKey); prev?.focus?.(); };
  }, [onClose]);
  return (
    <div className="modal-backdrop" onMouseDown={(e) => { if (e.target === e.currentTarget) onClose(); }}>
      <div className="modal" role="dialog" aria-modal="true" aria-labelledby="modal-title" ref={ref}>
        <div className="modal-header">
          <h2 id="modal-title">{title}</h2>
          <button type="button" className="btn btn-ghost btn-icon" onClick={onClose} aria-label="Close dialog"><X size={18} /></button>
        </div>
        {children}
        {footer && <div className="modal-actions">{footer}</div>}
      </div>
    </div>
  );
}

export function ConfirmDialog({ title, message, confirmLabel = 'Confirm', danger = false, busy, onConfirm, onCancel }) {
  return (
    <Modal title={title} onClose={onCancel} footer={(
      <>
        <button type="button" className="btn btn-secondary" onClick={onCancel}>Cancel</button>
        <button type="button" className={`btn ${danger ? 'btn-danger' : 'btn-primary'}`} onClick={onConfirm} disabled={busy}>
          {busy ? <Spinner dark={danger} /> : null}{confirmLabel}
        </button>
      </>
    )}>
      <p>{message}</p>
    </Modal>
  );
}

export function Pagination({ offset, limit, total, onChange }) {
  if (total <= limit) return null;
  const page = Math.floor(offset / limit) + 1;
  const pages = Math.ceil(total / limit);
  return (
    <nav className="pagination" aria-label="Pagination">
      <button type="button" className="btn btn-secondary btn-sm" disabled={page <= 1} onClick={() => onChange(offset - limit)}>Previous</button>
      <span className="small muted">Page {page} of {pages}</span>
      <button type="button" className="btn btn-secondary btn-sm" disabled={page >= pages} onClick={() => onChange(offset + limit)}>Next</button>
    </nav>
  );
}

export function MockBadge() {
  return <span className="badge badge-mock" title="Generated sample data for development - not a real job">Sample listing</span>;
}
