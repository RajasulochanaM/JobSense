import { Link } from 'react-router-dom';
import { useDocumentTitle } from '../hooks/useAsync';

const FAQ = [
  {
    q: 'How do I get job recommendations?',
    a: <>Upload a PDF or DOCX resume on the <Link to="/resume">Resume</Link> page. JobSense extracts your skills and shows recommended jobs right below your resume analysis. Use <em>Refresh recommendations</em> to fetch new jobs for your profile.</>,
  },
  {
    q: 'What does the match score mean?',
    a: 'It combines how many of a job\'s required skills appear in your profile with how similar your resume text is to the job description. It is a guide to alignment, not a guarantee of selection.',
  },
  {
    q: 'Why are some of my skills missing?',
    a: <>Skill extraction relies on a known skill list and readable text. Scanned, image-only PDFs cannot be read. You can add any missing skills manually on your <Link to="/profile">Profile</Link>.</>,
  },
  {
    q: 'How do I filter jobs by experience?',
    a: <>On <Link to="/jobs">Find Jobs</Link>, choose your years of experience (0-50). Jobs that ask for more experience than you selected are hidden.</>,
  },
  {
    q: 'Can I change my profile picture?',
    a: 'Yes. On your Profile, upload a photo or keep a simple initials avatar and pick its colour.',
  },
  {
    q: 'How do I delete my resume?',
    a: 'Open the Resume page and use the delete button next to the file. Its extracted skills are removed and your matches are recalculated.',
  },
];

export default function Help() {
  useDocumentTitle('Help');
  return (
    <div className="doc-page">
      <h1>Help</h1>
      <p className="muted">Answers to common questions about using JobSense.</p>
      {FAQ.map(({ q, a }) => (
        <details key={q}>
          <summary>{q}</summary>
          <p>{a}</p>
        </details>
      ))}
    </div>
  );
}
