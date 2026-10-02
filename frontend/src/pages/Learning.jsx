import { useMemo, useState } from 'react';
import { BookOpen, ExternalLink } from 'lucide-react';
import { learningApi, profileApi } from '../services/api';
import { useAsync, useDebounce, useDocumentTitle } from '../hooks/useAsync';
import { EmptyState, ErrorState, PageHeader, Skeleton, SkillChips } from '../components/ui';

export default function Learning() {
  useDocumentTitle('Skills & Learning');
  const [search, setSearch] = useState('');
  const [onlyGaps, setOnlyGaps] = useState(true);
  const q = useDebounce(search, 300);

  const dashboard = useAsync(() => profileApi.dashboard(), []);
  const skills = useAsync(() => profileApi.skills(), []);
  const resources = useAsync(() => learningApi.list({ q, limit: 500 }), [q]);

  const gaps = useMemo(() => (dashboard.data?.skill_gaps || []).map((g) => g.skill), [dashboard.data]);
  const careerGaps = useMemo(() => {
    const set = new Set();
    (dashboard.data?.careers || []).forEach((c) => c.missing_skills.filter((m) => m.importance >= 2).forEach((m) => set.add(m.skill)));
    return [...set];
  }, [dashboard.data]);
  const focus = useMemo(() => [...new Set([...gaps, ...careerGaps])], [gaps, careerGaps]);

  const grouped = useMemo(() => {
    const out = {};
    (resources.data?.items || []).forEach((r) => { (out[r.skill_name] ||= []).push(r); });
    let entries = Object.entries(out);
    if (onlyGaps && focus.length && !q) entries = entries.filter(([skill]) => focus.includes(skill));
    return entries.sort(([a], [b]) => {
      const ia = focus.indexOf(a); const ib = focus.indexOf(b);
      if (ia !== -1 || ib !== -1) return (ia === -1 ? 999 : ia) - (ib === -1 ? 999 : ib);
      return a.localeCompare(b);
    });
  }, [resources.data, onlyGaps, focus, q]);

  return (
    <div>
      <PageHeader title="Skills & Learning" description="Your skills, the gaps that appear most in your matches, and official resources to close them." />

      <div className="grid grid-2" style={{ marginBottom: '1rem', alignItems: 'start' }}>
        <section className="card" aria-labelledby="my-skills">
          <h2 id="my-skills">Your skills</h2>
          {skills.loading && !skills.data ? <Skeleton lines={2} /> : skills.error ? <ErrorState error={skills.error} /> : (
            <SkillChips skills={skills.data.items.map((s) => s.skill_name)} variant="highlight" emptyText="No skills yet - upload your resume or add skills in your profile." />
          )}
        </section>
        <section className="card" aria-labelledby="gap-skills">
          <h2 id="gap-skills">Skills to develop</h2>
          {dashboard.loading && !dashboard.data ? <Skeleton lines={2} /> : (
            <>
              <p className="small muted" style={{ marginBottom: 6 }}>Most frequent gaps in your job matches</p>
              <SkillChips skills={gaps} variant="missing" emptyText="Search jobs to identify gaps." />
              <p className="small muted" style={{ margin: '12px 0 6px' }}>Gaps in your top career paths</p>
              <SkillChips skills={careerGaps} variant="missing" emptyText="None identified yet." />
            </>
          )}
        </section>
      </div>

      <div className="card row" style={{ alignItems: 'flex-end', marginBottom: '1rem' }}>
        <div className="field" style={{ marginBottom: 0, flex: '1 1 260px' }}>
          <label htmlFor="res-q">Search resources by skill</label>
          <input id="res-q" className="input" placeholder="e.g. Docker, TypeScript" value={search} onChange={(e) => setSearch(e.target.value)} />
        </div>
        {focus.length > 0 && !q && (
          <label className="checkbox" style={{ paddingBottom: 10 }}>
            <input type="checkbox" checked={onlyGaps} onChange={(e) => setOnlyGaps(e.target.checked)} /> Only my skill gaps
          </label>
        )}
      </div>

      {resources.loading && !resources.data ? <Skeleton count={3} /> : resources.error ? <ErrorState error={resources.error} onRetry={resources.reload} /> : grouped.length === 0 ? (
        <EmptyState icon={BookOpen} title="No resources found">Try another skill name.</EmptyState>
      ) : (
        <div className="grid grid-3">
          {grouped.map(([skill, items]) => (
            <section key={skill} className={`card ${focus.includes(skill) ? 'card-highlight' : ''}`} aria-labelledby={`res-${skill}`}>
              <div className="row-between">
                <h3 id={`res-${skill}`} style={{ margin: 0 }}>{skill}</h3>
                {focus.includes(skill) && <span className="badge badge-burgundy">Skill gap</span>}
              </div>
              <ul className="list-plain" style={{ marginTop: 8 }}>
                {items.map((r) => (
                  <li key={r.resource_id} style={{ padding: '6px 0' }}>
                    <a href={r.resource_url} target="_blank" rel="noopener noreferrer" className="small">
                      <strong>{r.resource_name}</strong> <ExternalLink size={12} aria-hidden="true" /><span className="sr-only">(opens in a new tab)</span>
                    </a>
                    <div className="small muted">{r.resource_type} · {r.description}</div>
                  </li>
                ))}
              </ul>
            </section>
          ))}
        </div>
      )}
    </div>
  );
}
