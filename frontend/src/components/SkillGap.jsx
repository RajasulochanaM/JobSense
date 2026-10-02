import { BookOpen, ExternalLink } from 'lucide-react';
import { Meter, SkillChips, Skeleton } from './ui';
import { pct } from '../utils/format';

/** Matched vs missing skills, counts, coverage and learning resources for the gaps. */
export default function SkillGap({ matched = [], missing = [], resources, resourcesLoading }) {
  const names = (list) => list.map((s) => (typeof s === 'string' ? s : s.skill));
  const total = matched.length + missing.length;
  const coverage = total ? (matched.length / total) * 100 : null;
  const withResources = (resources || []).filter((r) => r.resources.length > 0);

  return (
    <div className="stack">
      {total === 0 ? (
        <p className="small muted">No required skills could be identified, so the score is based on text similarity only.</p>
      ) : (
        <>
          <div className="grid grid-3">
            <div><div className="small muted">Required skills covered</div><strong style={{ fontSize: '1.3rem' }}>{pct(coverage)}</strong></div>
            <div><div className="small muted">Matched skills</div><strong style={{ fontSize: '1.3rem' }}>{matched.length}</strong></div>
            <div><div className="small muted">Missing skills</div><strong style={{ fontSize: '1.3rem' }}>{missing.length}</strong></div>
          </div>
          <Meter value={coverage} variant="success" label="Required skills covered" />
          <div className="grid grid-2">
            <div>
              <h3>Matched skills</h3>
              <SkillChips skills={names(matched)} variant="matched" emptyText="None yet" />
            </div>
            <div>
              <h3>Missing skills</h3>
              <SkillChips skills={names(missing)} variant="missing" emptyText="No missing skills identified" />
            </div>
          </div>
        </>
      )}

      {missing.length > 0 && (
        <div>
          <h3 className="row"><BookOpen size={17} aria-hidden="true" /> Learning resources for missing skills</h3>
          {resourcesLoading ? <Skeleton lines={2} /> : withResources.length === 0 ? (
            <p className="small muted">No curated resources for these skills yet.</p>
          ) : (
            <div className="grid grid-2">
              {withResources.map(({ skill, resources: items }) => (
                <div key={skill} className="card card-highlight" style={{ padding: '0.9rem 1rem' }}>
                  <strong>{skill}</strong>
                  <ul className="list-plain" style={{ marginTop: 6 }}>
                    {items.slice(0, 3).map((r) => (
                      <li key={r.resource_id} className="small" style={{ padding: '3px 0' }}>
                        <a href={r.resource_url} target="_blank" rel="noopener noreferrer">
                          {r.resource_name} <ExternalLink size={12} aria-hidden="true" /><span className="sr-only">(opens in a new tab)</span>
                        </a>
                        <span className="muted"> · {r.resource_type}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
