import { Link, useParams } from 'react-router-dom';
import { ArrowLeft, Search } from 'lucide-react';
import { careersApi } from '../services/api';
import { useAsync, useDocumentTitle } from '../hooks/useAsync';
import SkillGap from '../components/SkillGap';
import { ErrorState, MetricRow, Skeleton } from '../components/ui';

const IMPORTANCE = { 3: 'Core', 2: 'Important', 1: 'Nice to have' };

export default function CareerDetails() {
  const { careerId } = useParams();
  const { data, loading, error, reload } = useAsync(() => careersApi.get(careerId), [careerId]);
  useDocumentTitle(data?.career?.career_name || 'Career path');

  if (loading && !data) return <Skeleton count={3} />;
  if (error) return <ErrorState error={error} onRetry={reload} />;

  const { career, recommendation: rec, learning_resources: resources } = data;
  const importanceOf = Object.fromEntries(career.skills.map((s) => [s.skill_name, s.importance]));

  return (
    <div>
      <Link to="/careers" className="small row" style={{ marginBottom: 12 }}><ArrowLeft size={15} aria-hidden="true" /> All career paths</Link>
      <header className="card">
        <div className="row-between">
          <h1 style={{ margin: 0 }}>{career.career_name}</h1>
          {career.interest_area && <span className="badge badge-burgundy">{career.interest_area}</span>}
        </div>
        <p className="muted" style={{ marginTop: 8 }}>{career.description}</p>
        <Link className="btn btn-secondary btn-sm" to={`/jobs?q=${encodeURIComponent(career.career_name)}`}>
          <Search size={14} aria-hidden="true" /> Search {career.career_name} jobs
        </Link>
      </header>

      <div className="grid grid-2" style={{ marginTop: '1rem', alignItems: 'start' }}>
        <section className="card" aria-labelledby="why-title">
          <h2 id="why-title">Why this career aligns</h2>
          {rec ? (
            <>
              <MetricRow label="Overall alignment" value={rec.match_score} variant="success" />
              <MetricRow label="Skill alignment" value={rec.skill_alignment} variant="butter" />
              <MetricRow label="Text similarity" value={rec.text_similarity} />
              <ul className="small" style={{ marginTop: 14 }}>
                {rec.reasons.map((r) => <li key={r}>{r}</li>)}
              </ul>
            </>
          ) : <p className="small muted">Upload a resume to see your alignment with this role.</p>}
        </section>

        <section className="card" aria-labelledby="req-title">
          <h2 id="req-title">Skills for this role</h2>
          <div className="table-wrap" style={{ border: 0 }}>
            <table className="table">
              <thead><tr><th scope="col">Skill</th><th scope="col">Importance</th><th scope="col">You</th></tr></thead>
              <tbody>
                {career.skills.map((s) => {
                  const have = rec?.matched_skills.some((m) => m.skill === s.skill_name);
                  return (
                    <tr key={s.skill_name}>
                      <td>{s.skill_name}</td>
                      <td className="small">{IMPORTANCE[s.importance]}</td>
                      <td className="small" style={{ color: have ? 'var(--success)' : 'var(--text-2)' }}>{have ? '✓ Have' : '○ Missing'}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </section>
      </div>

      {rec && (
        <section className="card" style={{ marginTop: '1rem' }} aria-labelledby="gap-title">
          <h2 id="gap-title">Skill gap &amp; learning resources</h2>
          <p className="small muted">Missing skills are ordered by importance ({rec.missing_skills.filter((m) => importanceOf[m.skill] === 3).length} core).</p>
          <SkillGap matched={rec.matched_skills} missing={rec.missing_skills} resources={resources} />
        </section>
      )}
    </div>
  );
}
