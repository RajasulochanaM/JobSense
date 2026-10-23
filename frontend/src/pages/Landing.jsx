import { Link } from 'react-router-dom';
import { ArrowRight, BookOpen, Compass, FileSearch, GitCompareArrows, Sparkles, Target, Upload } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useDocumentTitle } from '../hooks/useAsync';
import './Landing.css';

const STATS = [
  { value: '15', label: 'Career roles compared' },
  { value: '40 / 60', label: 'Text vs skill weighting' },
  { value: 'PDF · DOCX', label: 'Resume formats' },
  { value: '100%', label: 'Explainable scores' },
];

const FEATURES = [
  { icon: GitCompareArrows, title: 'Intelligent job matching', text: 'Every job gets an explainable score built from TF-IDF text similarity and an explicit skill match.', big: true },
  { icon: Target, title: 'Skill-gap analysis', text: 'See exactly which required skills you have and which are missing.' },
  { icon: FileSearch, title: 'Resume analysis', text: 'Skills, education and experience extracted once and kept in your profile.' },
  { icon: Compass, title: 'Career paths', text: 'Compare your profile with 15 roles and see why each one fits.' },
  { icon: BookOpen, title: 'Learning resources', text: 'Missing skills link to official docs and trusted references.' },
  { icon: Upload, title: 'Application tracking', text: 'Save jobs and follow each application from Applied to Offer.', wide: true },
];

const STEPS = [
  { title: 'Upload your resume', text: 'Drop a PDF or DOCX. Text is extracted with pypdf / python-docx in seconds.', visual: 'upload' },
  { title: 'Skills are extracted', text: 'spaCy-based NLP finds and normalises your skills, so ReactJS becomes React.', visual: 'skills' },
  { title: 'Jobs are compared', text: 'TF-IDF vectors and cosine similarity rank real job descriptions against your profile.', visual: 'match' },
  { title: 'Close the gaps', text: 'Missing skills come with learning resources so you know what to study next.', visual: 'learn' },
];

function StepVisual({ kind }) {
  if (kind === 'upload') {
    return (
      <div className="lp-visual lp-drop">
        <Upload size={28} aria-hidden="true" />
        <span>resume.pdf</span>
        <div className="lp-bar"><span style={{ width: '100%' }} /></div>
      </div>
    );
  }
  if (kind === 'skills') {
    return (
      <div className="lp-visual lp-chipcloud">
        {['React', 'JavaScript', 'Python', 'SQL', 'Node.js', 'Docker', 'Git'].map((s) => <span key={s} className="lp-chip">{s}</span>)}
      </div>
    );
  }
  if (kind === 'match') {
    return (
      <div className="lp-visual lp-ranks">
        {[['React Developer', 79], ['Full-stack Engineer', 71], ['Frontend Intern', 64]].map(([t, v]) => (
          <div key={t} className="lp-rank"><span>{t}</span><div className="lp-bar"><span style={{ width: `${v}%` }} /></div><b>{v}%</b></div>
        ))}
      </div>
    );
  }
  return (
    <div className="lp-visual lp-chipcloud">
      <span className="lp-chip lp-chip-missing">○ TypeScript</span>
      <span className="lp-chip lp-chip-missing">○ AWS</span>
      <span className="lp-learn"><BookOpen size={14} aria-hidden="true" /> typescriptlang.org/docs</span>
    </div>
  );
}

export default function Landing() {
  useDocumentTitle('');
  const { user } = useAuth();
  const start = user ? '/resume' : '/register';
  const explore = user ? '/jobs' : '/login';
  return (
    <div className="lp">
      <section className="lp-hero">
        <div className="lp-glow" aria-hidden="true" />
        <div className="lp-wrap lp-hero-inner">
          <p className="lp-pill"><Sparkles size={14} aria-hidden="true" /> NLP-powered resume &amp; job matching</p>
          <h1>Understand your resume. <span className="lp-grad">Land the job that fits you.</span></h1>
          <p className="lp-lead">
            JobSense compares your resume with real job descriptions using NLP, TF-IDF and cosine similarity,
            then shows your matched skills, missing skills and where to learn them.
          </p>
          <div className="lp-ctas">
            <Link to={start} className="btn btn-lg lp-btn-primary">Analyze My Resume <ArrowRight size={18} aria-hidden="true" /></Link>
            <Link to={explore} className="btn btn-lg lp-btn-ghost">Explore Jobs</Link>
          </div>

          <div className="lp-dash" aria-hidden="true">
            <div className="lp-dash-top"><span /><span /><span /><em>jobsense · matches</em></div>
            <div className="lp-dash-body">
              <div className="lp-score">
                <div className="lp-ring" style={{ '--p': 79 }}><b>79%</b></div>
                <div>
                  <strong>React Developer</strong>
                  <div className="lp-muted">Chennai · Full-time</div>
                </div>
              </div>
              <div className="lp-metrics">
                <div className="lp-metric"><span>Text similarity</span><div className="lp-bar"><span style={{ width: '82%' }} /></div><b>82%</b></div>
                <div className="lp-metric"><span>Skill match</span><div className="lp-bar lp-bar-gold"><span style={{ width: '75%' }} /></div><b>75%</b></div>
                <div className="lp-chipcloud">
                  <span className="lp-chip lp-chip-ok">✓ React</span><span className="lp-chip lp-chip-ok">✓ JavaScript</span>
                  <span className="lp-chip lp-chip-ok">✓ Node.js</span><span className="lp-chip lp-chip-missing">○ TypeScript</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="lp-stats" aria-label="JobSense at a glance">
        <div className="lp-wrap lp-stats-inner">
          {STATS.map((s) => (
            <div key={s.label} className="lp-stat"><b>{s.value}</b><span>{s.label}</span></div>
          ))}
        </div>
      </section>

      <section className="lp-section" aria-labelledby="features-title">
        <div className="lp-wrap">
          <p className="lp-kicker">Features</p>
          <h2 id="features-title" className="lp-h2">Everything you need for your next move</h2>
          <div className="lp-bento">
            {FEATURES.map(({ icon: Icon, title, text, big, wide }) => (
              <div key={title} className={`lp-tile${big ? ' lp-tile-big' : ''}${wide ? ' lp-tile-wide' : ''}`}>
                <span className="lp-icon"><Icon size={20} aria-hidden="true" /></span>
                <h3>{title}</h3>
                <p>{text}</p>
                {big && (
                  <code className="lp-formula">Final Score = 0.40 × Text Similarity + 0.60 × Skill Match</code>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="lp-section" aria-labelledby="how-title">
        <div className="lp-wrap">
          <p className="lp-kicker">How it works</p>
          <h2 id="how-title" className="lp-h2">From resume to roadmap in four steps</h2>
          <ol className="lp-steps">
            {STEPS.map((s, i) => (
              <li key={s.title} className="lp-step">
                <div className="lp-step-copy">
                  <span className="lp-step-num">{String(i + 1).padStart(2, '0')}</span>
                  <h3>{s.title}</h3>
                  <p>{s.text}</p>
                </div>
                <StepVisual kind={s.visual} />
              </li>
            ))}
          </ol>
        </div>
      </section>

      <section className="lp-wrap">
        <div className="lp-cta">
          <h2>Ready to see where you stand?</h2>
          <p>Upload your resume and get explainable job matches in under a minute. No black-box AI: every score traces back to TF-IDF vectors and a list of skills.</p>
          <Link to={start} className="btn btn-lg lp-btn-dark">Get started <ArrowRight size={18} aria-hidden="true" /></Link>
          <p className="lp-note">Scores describe how well your profile aligns with a job. They are not a prediction of hiring outcomes.</p>
        </div>
      </section>
    </div>
  );
}
