import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { AlertCircle, Download } from 'lucide-react';
import { resumeApi } from '../services/api';
import { useDocumentTitle } from '../hooks/useAsync';
import { Alert, Skeleton } from '../components/ui';
import { formatBytes } from '../utils/format';
import './ResumeView.css';

/**
 * Full-tab view of one uploaded resume, opened from the Resume & Matches page in a new browser tab.
 * PDFs are shown in the browser's PDF viewer; DOCX (which browsers can't render) shows its extracted text.
 */
export default function ResumeView() {
  const { resumeId } = useParams();
  const [meta, setMeta] = useState(null);
  const [url, setUrl] = useState(null);
  const [error, setError] = useState('');
  useDocumentTitle(meta ? meta.file_name : 'Resume');

  useEffect(() => {
    let objectUrl = null;
    let cancelled = false;
    Promise.all([resumeApi.get(resumeId), resumeApi.file(resumeId)])
      .then(([info, blob]) => {
        if (cancelled) return;
        objectUrl = URL.createObjectURL(blob);
        setMeta(info);
        setUrl(objectUrl);
      })
      .catch((err) => { if (!cancelled) setError(err.message || 'Could not load the resume'); });
    return () => {
      cancelled = true;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [resumeId]);

  if (error) {
    return <main className="resume-view-msg"><Alert type="error" icon={AlertCircle}>{error}</Alert></main>;
  }
  if (!meta || !url) {
    return <main className="resume-view-msg"><Skeleton lines={8} /></main>;
  }

  const isPdf = meta.file_type === 'pdf';
  return (
    <main className={`resume-view ${isPdf ? 'pdf' : 'docx'}`}>
      <header className="resume-view-bar">
        <div className="resume-view-name">
          <strong>{meta.file_name}</strong>
          <span>{meta.file_type.toUpperCase()} · {formatBytes(meta.file_size)}</span>
        </div>
        <a className="btn btn-sm btn-secondary" href={url} download={meta.file_name}>
          <Download size={14} aria-hidden="true" /> Download
        </a>
      </header>
      {isPdf ? (
        <iframe className="resume-view-frame" src={url} title={meta.file_name} />
      ) : (
        <article className="resume-view-doc">
          <p className="small muted">Word documents can't be displayed by the browser, so the text extracted from this resume is shown below. Use Download to open the original file.</p>
          {meta.text_preview
            ? <pre>{meta.text_preview}</pre>
            : <p>No text could be extracted from this document.</p>}
        </article>
      )}
    </main>
  );
}
