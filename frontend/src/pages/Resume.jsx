import { useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { CheckCircle2, FileText, Loader2, Trash2, Upload, AlertCircle } from 'lucide-react';
import { resumeApi } from '../services/api';
import { useAsync, useDocumentTitle } from '../hooks/useAsync';
import { useToast } from '../context/ToastContext';
import { Alert, ConfirmDialog, EmptyState, ErrorState, PageHeader, Skeleton, SkillChips } from '../components/ui';
import RecommendedJobs from '../components/RecommendedJobs';
import { formatBytes, formatDate } from '../utils/format';
import './Resume.css';

const MAX_MB = 5;
const STAGES = [
  { key: 'uploaded', label: 'Resume uploaded' },
  { key: 'extracting_text', label: 'Extracting text' },
  { key: 'analyzing_skills', label: 'Analyzing skills' },
  { key: 'profile_updated', label: 'Profile updated' },
];

export function validateResumeFile(file) {
  if (!file) return 'Please choose a file';
  const ext = file.name.split('.').pop().toLowerCase();
  if (!['pdf', 'docx'].includes(ext)) return 'Only PDF and DOCX files are supported';
  if (file.size > MAX_MB * 1024 * 1024) return `File is larger than ${MAX_MB} MB`;
  if (file.size === 0) return 'The file is empty';
  return null;
}

function ProcessingSteps({ stage, failed }) {
  const current = STAGES.findIndex((s) => s.key === stage);
  return (
    <ol className="processing-steps" aria-label="Processing progress">
      {STAGES.map((s, i) => {
        const done = i < current || (i === current && stage === 'profile_updated');
        const active = i === current && !done;
        return (
          <li key={s.key} className={done ? 'done' : active ? (failed ? 'failed' : 'active') : ''}>
            <span className="step-icon" aria-hidden="true">
              {done ? <CheckCircle2 size={18} /> : active ? (failed ? <AlertCircle size={18} /> : <Loader2 size={18} className="spin" />) : <span className="dot" />}
            </span>
            {s.label}
            <span className="sr-only">{done ? ' - done' : active ? (failed ? ' - failed' : ' - in progress') : ''}</span>
          </li>
        );
      })}
    </ol>
  );
}

export default function Resume() {
  useDocumentTitle('Resume & Matches');
  const toast = useToast();
  const inputRef = useRef(null);
  const [dragOver, setDragOver] = useState(false);
  const [stage, setStage] = useState(null);
  const [uploadError, setUploadError] = useState('');
  const [result, setResult] = useState(null);
  const [confirm, setConfirm] = useState(null);
  const [deleting, setDeleting] = useState(false);

  const list = useAsync(() => resumeApi.list(), []);
  const active = list.data?.items.find((r) => r.is_active && r.status === 'processed');
  const activeDetail = useAsync(() => (active ? resumeApi.get(active.resume_id) : Promise.resolve(null)), [active?.resume_id]);
  const busy = stage && stage !== 'profile_updated' && !uploadError;

  const handleFile = async (file) => {
    const problem = validateResumeFile(file);
    setUploadError(problem || '');
    setResult(null);
    if (problem) return;
    setStage('uploaded');
    try {
      const data = await resumeApi.upload(file, (evt) => {
        // The server extracts text and analyses skills once the upload completes.
        if (evt.total && evt.loaded >= evt.total) setStage('analyzing_skills');
      });
      setStage('profile_updated');
      setResult(data);
      toast.success(`Resume analysed - ${data.skills.length} skills found`);
      list.reload({ silent: true });
    } catch (err) {
      setUploadError(err.message);
    } finally {
      if (inputRef.current) inputRef.current.value = '';
    }
  };

  const onDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    if (!busy) handleFile(e.dataTransfer.files?.[0]);
  };

  const doDelete = async () => {
    setDeleting(true);
    try {
      await resumeApi.remove(confirm.resume_id);
      toast.success('Resume deleted');
      setConfirm(null);
      setResult(null);
      setStage(null);
      list.reload({ silent: true });
    } catch (err) {
      toast.error(err.message);
    } finally {
      setDeleting(false);
    }
  };

  const detail = result?.resume || activeDetail.data;
  const skills = result?.skills;

  return (
    <div>
      <PageHeader title="Resume & Matches" description="Upload a PDF or DOCX resume. JobSense extracts its skills, stores them in your profile and recommends jobs that fit." />

      <div className="resume-grid">
        <section className="card" aria-labelledby="upload-title">
          <h2 id="upload-title">{active ? 'Replace resume' : 'Upload resume'}</h2>
          <div
            className={`dropzone ${dragOver ? 'over' : ''} ${busy ? 'busy' : ''}`}
            onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={onDrop}
          >
            <Upload size={28} aria-hidden="true" />
            <p><strong>Drag and drop</strong> your resume here, or</p>
            <label className={`btn btn-primary ${busy ? 'disabled' : ''}`}>
              Choose file
              <input ref={inputRef} type="file" className="sr-only" disabled={busy}
                accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                onChange={(e) => handleFile(e.target.files?.[0])} />
            </label>
            <p className="small muted">PDF or DOCX, up to {MAX_MB} MB. Scanned image-only PDFs cannot be read.</p>
          </div>

          {stage && <ProcessingSteps stage={stage} failed={Boolean(uploadError)} />}
          {uploadError && <Alert type="error" icon={AlertCircle}>{uploadError}</Alert>}
          {result && (
            <Alert type="success" icon={CheckCircle2}>
              Your profile has been updated. See your <a href="#recommended">recommended jobs</a> below, or <Link to="/careers">explore career paths</Link>.
            </Alert>
          )}
        </section>

        <section className="card" aria-labelledby="history-title">
          <h2 id="history-title">Uploaded resumes</h2>
          {list.loading && !list.data ? <Skeleton lines={2} /> : list.error ? <ErrorState error={list.error} onRetry={list.reload} /> : (
            list.data.items.length === 0 ? <p className="muted small">No resumes uploaded yet.</p> : (
              <ul className="list-plain list-divided">
                {list.data.items.map((r) => (
                  <li key={r.resume_id} className="row-between">
                    <div style={{ minWidth: 0 }}>
                      <div className="row"><FileText size={16} aria-hidden="true" /><strong className="truncate">{r.file_name}</strong>
                        {r.is_active && <span className="badge badge-success">Active</span>}
                        {r.status === 'failed' && <span className="badge badge-error">Failed</span>}
                      </div>
                      <div className="small muted">{formatDate(r.uploaded_at)} · {r.file_type.toUpperCase()} · {formatBytes(r.file_size)}</div>
                      {r.error_message && <div className="small field-error">{r.error_message}</div>}
                    </div>
                    <button type="button" className="btn btn-sm btn-danger" onClick={() => setConfirm(r)} aria-label={`Delete ${r.file_name}`}>
                      <Trash2 size={14} aria-hidden="true" />
                    </button>
                  </li>
                ))}
              </ul>
            )
          )}
        </section>
      </div>

      <section className="card" style={{ marginTop: '1rem' }} aria-labelledby="analysis-title">
        <h2 id="analysis-title">Resume analysis</h2>
        {!detail ? (
          activeDetail.loading ? <Skeleton lines={3} /> : (
            <EmptyState icon={FileText} title="No resume analysed yet">Upload your resume to see the extracted skills and text.</EmptyState>
          )
        ) : (
          <div className="stack">
            <div className="row small muted">
              <span><strong className="text">{detail.file_name}</strong></span>
              <span>Uploaded {formatDate(detail.uploaded_at)}</span>
              <span className="badge badge-success">Processed</span>
              {detail.experience_years !== null && detail.experience_years !== undefined && <span>≈ {detail.experience_years} years experience detected</span>}
            </div>
            <div>
              <h3>Extracted skills</h3>
              {skills ? <SkillChips skills={skills} variant="highlight" emptyText="No known skills were detected." />
                : <p className="small muted">See your full skill list on the <Link to="/profile">Profile</Link> page.</p>}
            </div>
            {detail.education?.length > 0 && (
              <div><h3>Education (detected)</h3><ul className="small">{detail.education.map((e) => <li key={e}>{e}</li>)}</ul></div>
            )}
            {detail.experience?.length > 0 && (
              <div><h3>Experience (detected)</h3><ul className="small">{detail.experience.slice(0, 6).map((e) => <li key={e}>{e}</li>)}</ul></div>
            )}
            {detail.text_preview && (
              <details>
                <summary><strong>Extracted text preview</strong> <span className="small muted">({detail.text_length.toLocaleString()} characters)</span></summary>
                <pre className="text-preview">{detail.text_preview}{detail.text_length > detail.text_preview.length ? '\n…' : ''}</pre>
              </details>
            )}
          </div>
        )}
      </section>

      <RecommendedJobs resumeKey={active?.resume_id ?? 'none'} />

      {confirm && (
        <ConfirmDialog title="Delete resume?" danger confirmLabel="Delete" busy={deleting} onCancel={() => setConfirm(null)} onConfirm={doDelete}
          message={`"${confirm.file_name}" and its extracted data will be removed.${confirm.is_active ? ' Skills from this resume will be removed from your profile and matches will be recalculated.' : ''}`} />
      )}
    </div>
  );
}
