export function formatDate(value, opts = { day: 'numeric', month: 'short', year: 'numeric' }) {
  if (!value) return '—';
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return '—';
  return d.toLocaleDateString('en-IN', opts);
}

export function timeAgo(value) {
  if (!value) return '';
  const d = new Date(value);
  const diff = (Date.now() - d.getTime()) / 1000;
  if (Number.isNaN(diff)) return '';
  if (diff < 3600) return 'just now';
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  if (diff < 86400 * 30) return `${Math.floor(diff / 86400)}d ago`;
  return formatDate(value);
}

export function pct(value, digits = 0) {
  if (value === null || value === undefined) return '—';
  return `${Number(value).toFixed(digits)}%`;
}

/** Descriptive (never absolute) label for a match score. */
export function scoreBand(score) {
  if (score === null || score === undefined) return { key: 'none', label: 'Not scored' };
  if (score >= 70) return { key: 'high', label: 'Strong alignment' };
  if (score >= 40) return { key: 'mid', label: 'Partial alignment' };
  return { key: 'low', label: 'Low alignment' };
}

export function formatBytes(bytes) {
  if (!bytes) return '0 KB';
  if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

export function initials(name = '') {
  return name.split(/\s+/).filter(Boolean).slice(0, 2).map((p) => p[0].toUpperCase()).join('') || 'U';
}

export const APPLICATION_STATUSES = ['Saved', 'Applied', 'Interview', 'Offer', 'Rejected', 'Withdrawn'];

export const EMPLOYMENT_TYPES = [
  { value: '', label: 'Any type' },
  { value: 'FULLTIME', label: 'Full-time' },
  { value: 'PARTTIME', label: 'Part-time' },
  { value: 'CONTRACTOR', label: 'Contract' },
  { value: 'INTERN', label: 'Internship' },
];

export const MAX_EXPERIENCE_YEARS = 50;

/** "Any experience", then 0 (fresher) to 50 years. Values are sent to the API as experience_years. */
export const EXPERIENCE_YEARS = [
  { value: '', label: 'Any experience' },
  ...Array.from({ length: MAX_EXPERIENCE_YEARS + 1 }, (_, y) => ({
    value: String(y),
    label: y === 0 ? '0 years (Fresher)' : `${y} year${y === 1 ? '' : 's'}`,
  })),
];
