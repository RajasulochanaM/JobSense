import { Link } from 'react-router-dom';
import { BookOpen, Compass, FileSearch, GitCompareArrows, Target, Upload } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useDocumentTitle } from '../hooks/useAsync';
import './Landing.css';

const STEPS = [
  { title: 'Upload your resume', text: 'PDF or DOCX. Text is extracted with pypdf / python-docx.' },
  { title: 'Skills are extracted', text: 'spaCy-based NLP normalises your skills (ReactJS → React).' },
  { title: 'Jobs are compared', text: 'TF-IDF + cosine similarity and explicit skill matching.' },
  { title: 'Close the gaps', text: 'See missing skills and official learning resources.' },
];

const FEATURES = [
  { icon: FileSearch, title: 'Resume analysis', text: 'Extracts skills, education and experience from your resume, once, and keeps the results in your profile.' },
  { icon: GitCompareArrows, title: 'Intelligent job matching', text: 'Every job gets an explainable score: text similarity, skill match and the weighted final score.' },
  { icon: Target, title: 'Skill-gap analysis', text: 'For each job, see exactly which required skills you already have and which are missing.' },
  { icon: Compass, title: 'Career paths', text: 'Compare your profile with 15 career roles and inspect why each one aligns with your skills.' },
  { icon: BookOpen, title: 'Learning resources', text: 'Missing skills link to official documentation and trusted references, not ads.' },
  { icon: Upload, title: 'Application tracking', text: 'Save jobs and track each application from Applied to Offer in one place.' },
];

export default function Landing() {
  useDocumentTitle('');
  const { user } = useAuth();
  const start = user ? '/resume' : '/register';
  const explore = user ? '/jobs' : '/login';
  return (
    <div className="landing">
      <section className="hero">
        <div className="hero-inner">
          <div className="hero-copy">
            <p className="eyebrow">JobSense · Resume &amp; job matching</p>
            <h1>
              Understand your resume.<br />
              Discover relevant opportunities.<br />
              <span className="hl">Build the skills for your next career move.</span>
            </h1>
            <p className="lead">
              JobSense compares your resume with real job descriptions using NLP, TF-IDF and cosine similarity,
              then shows you matched skills, missing skills and where to learn them.
            </p>
            <div className="row">
              <Link to={start} className="btn btn-primary btn-lg">Analyze My Resume</Link>
              <Link to={explore} className="btn btn-secondary btn-lg">Explore Jobs</Link>
            </div>
            <p className="small muted" style={{ marginTop: 14 }}>
              Scores describe how well your profile aligns with a job. They are not a prediction of hiring outcomes.
            </p>
          </div>

          <div className="hero-visual" aria-hidden="true">
            <div className="mock-card">
              <div className="row-between"><strong>React Developer</strong><span className="mock-score">79%</span></div>
              <div className="small muted">Chennai · Full-time</div>
              <div className="mock-metric"><span>Text similarity</span><div className="meter"><span style={{ width: '82%' }} /></div><b>82%</b></div>
              <div className="mock-metric"><span>Skill match</span><div className="meter meter-butter"><span style={{ width: '75%' }} /></div><b>75%</b></div>
              <div className="chips" style={{ marginTop: 10 }}>
                <span className="chip chip-matched">✓ React</span><span className="chip chip-matched">✓ JavaScript</span>
                <span className="chip chip-matched">✓ Node.js</span><span className="chip chip-missing">○ TypeScript</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="section" aria-labelledby="how-title">
        <h2 id="how-title" className="section-title">How JobSense works</h2>
        <ol className="steps">
          {STEPS.map((s, i) => (
            <li key={s.title} className="step">
              <span className="step-num" aria-hidden="true">{i + 1}</span>
              <h3>{s.title}</h3>
              <p className="muted small">{s.text}</p>
            </li>
          ))}
        </ol>
      </section>

      <section className="section" aria-labelledby="features-title">
        <h2 id="features-title" className="section-title">What you get</h2>
        <div className="grid grid-3">
          {FEATURES.map(({ icon: Icon, title, text }) => (
            <div key={title} className="card feature">
              <span className="feature-icon"><Icon size={20} aria-hidden="true" /></span>
              <h3>{title}</h3>
              <p className="muted small">{text}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="section formula card card-highlight" aria-labelledby="method-title">
        <h2 id="method-title">A transparent, explainable score</h2>
        <p><code>Final Score = 0.40 × Text Similarity + 0.60 × Skill Match</code></p>
        <p className="muted small">Weights are configurable and documented. No black-box AI: every score can be traced to TF-IDF vectors and a list of skills.</p>
        <Link to={start} className="btn btn-primary">Get started</Link>
      </section>
    </div>
  );
}
