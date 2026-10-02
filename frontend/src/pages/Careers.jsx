import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Compass, RefreshCw, Heart } from 'lucide-react';
import { careersApi } from '../services/api';
import { useAsync, useDocumentTitle } from '../hooks/useAsync';
import { useToast } from '../context/ToastContext';
import { EmptyState, ErrorState, Meter, PageHeader, Skeleton, SkillChips, Spinner } from '../components/ui';
import { pct } from '../utils/format';

export default function Careers() {
  useDocumentTitle('Career Paths');
  const toast = useToast();
  const [refreshing, setRefreshing] = useState(false);
  const { data, loading, error, reload, setData } = useAsync(() => careersApi.recommendations(), []);

  const refresh = async () => {
    setRefreshing(true);
    try {
      setData(await careersApi.recommendations(true));
      toast.success('Career alignment recalculated');
    } catch (err) {
      toast.error(err.message);
    } finally {
      setRefreshing(false);
    }
  };

  return (
    <div>
      <PageHeader title="Potential Career Paths"
        description="How your current skills align with common technology roles. This is a comparison, not a ranking of the ‘best’ career."
        actions={<button type="button" className="btn btn-secondary" onClick={refresh} disabled={refreshing}>
          {refreshing ? <Spinner dark /> : <RefreshCw size={16} aria-hidden="true" />} Recalculate</button>} />

      {loading && !data ? <Skeleton count={4} /> : error ? <ErrorState error={error} onRetry={reload} /> : (
        <>
          {!data.profile_ready && (
            <EmptyState icon={Compass} title="Add your skills first"
              action={<Link className="btn btn-primary" to="/resume">Upload resume</Link>}>
              Career alignment is calculated from the skills in your resume and profile.
            </EmptyState>
          )}
          {data.profile_ready && (
            <p className="small muted">
              Alignment = {Math.round(data.weights.skill_alignment * 100)}% weighted skill alignment + {Math.round(data.weights.text_similarity * 100)}% resume text similarity
              + {Math.round(data.weights.interest * 100)}% interest match (interests only count when you already have some matching skills).
              {data.interests.length === 0 && <> <Link to="/profile">Add interests</Link> to your profile.</>}
            </p>
          )}
          <div className="grid grid-2" style={{ marginTop: '1rem' }}>
            {data.items.map((c) => (
              <Link key={c.career_id} to={`/careers/${c.career_id}`} className="card card-link">
                <div className="row-between" style={{ alignItems: 'flex-start' }}>
                  <h2 style={{ marginBottom: 4 }}>{c.career_name}</h2>
                  <span className="score" style={{ minWidth: 0 }}><span className="score-value" style={{ fontSize: '1.05rem' }}>{pct(c.match_score)}</span><span className="score-label">Alignment</span></span>
                </div>
                <p className="small muted" style={{ minHeight: 44 }}>{c.description}</p>
                <div className="row-between small"><span>Skill alignment</span><strong>{pct(c.skill_alignment)}</strong></div>
                <Meter value={c.skill_alignment} variant="butter" label={`${c.career_name} skill alignment`} />
                {c.interest_match && <p className="small row" style={{ marginTop: 8, color: 'var(--burgundy)' }}><Heart size={14} aria-hidden="true" /> Matches your interests</p>}
                <div style={{ marginTop: 10 }}>
                  <div className="small muted" style={{ marginBottom: 4 }}>Matched</div>
                  <SkillChips skills={c.matched_skills} variant="matched" limit={5} emptyText="No matching skills yet" />
                </div>
                <div style={{ marginTop: 8 }}>
                  <div className="small muted" style={{ marginBottom: 4 }}>Missing</div>
                  <SkillChips skills={c.missing_skills} variant="missing" limit={5} emptyText="None" />
                </div>
              </Link>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
