import { adminApi } from '../../services/api';
import { useAsync, useDocumentTitle } from '../../hooks/useAsync';
import BarList from '../../components/BarList';
import { ErrorState, PageHeader, Skeleton, StatCard } from '../../components/ui';
import { pct } from '../../utils/format';

export default function AdminAnalytics() {
  useDocumentTitle('Analytics');
  const { data, loading, error, reload } = useAsync(() => adminApi.analytics(), []);

  if (loading && !data) return <><PageHeader title="Analytics" /><Skeleton count={3} /></>;
  if (error) return <><PageHeader title="Analytics" /><ErrorState error={error} onRetry={reload} /></>;

  const ms = data.match_statistics || {};
  const bands = [
    { label: '70-100% (strong)', value: Number(ms.band_high || 0) },
    { label: '40-69% (partial)', value: Number(ms.band_mid || 0) },
    { label: '0-39% (low)', value: Number(ms.band_low || 0) },
  ];

  return (
    <div>
      <PageHeader title="Analytics" description="Aggregated, anonymous statistics across all candidates." />
      <div className="grid grid-4" style={{ marginBottom: '1rem' }}>
        <StatCard label="Matches computed" value={Number(ms.total || 0).toLocaleString('en-IN')} />
        <StatCard label="Average final score" value={pct(ms.avg_final, 1)} />
        <StatCard label="Average text similarity" value={pct(ms.avg_text, 1)} />
        <StatCard label="Average skill match" value={pct(ms.avg_skill, 1)} />
      </div>
      <div className="grid grid-2">
        <section className="card" aria-labelledby="c1"><h2 id="c1">Most common candidate skills</h2>
          <p className="small muted">Number of candidates with each skill</p>
          <BarList title="Most common candidate skills" data={data.top_candidate_skills} labelKey="skill" valueKey="count" emptyText="No candidate skills yet." /></section>
        <section className="card" aria-labelledby="c2"><h2 id="c2">Most common missing skills</h2>
          <p className="small muted">How often a skill is missing across computed job matches</p>
          <BarList title="Most common missing skills" data={data.top_missing_skills} labelKey="skill" valueKey="count" emptyText="No matches computed yet." /></section>
        <section className="card" aria-labelledby="c3"><h2 id="c3">Application status distribution</h2>
          <p className="small muted">Number of tracked applications per status</p>
          <BarList title="Application status distribution" data={data.application_status} labelKey="status" valueKey="count" /></section>
        <section className="card" aria-labelledby="c4"><h2 id="c4">Job match score distribution</h2>
          <p className="small muted">Number of candidate-job matches per final-score band</p>
          <BarList title="Job match score distribution" data={bands} emptyText="No matches computed yet." /></section>
        <section className="card" aria-labelledby="c5"><h2 id="c5">Jobs by source</h2>
          <p className="small muted">Stored jobs per provider (mock = development samples)</p>
          <BarList title="Jobs by source" data={data.jobs_by_source} labelKey="source" valueKey="n" /></section>
        <section className="card" aria-labelledby="c6"><h2 id="c6">New users by month</h2>
          <p className="small muted">Registrations in the last six months with sign-ups</p>
          <BarList title="New users by month" data={data.signups_by_month} labelKey="month" valueKey="n" /></section>
      </div>
    </div>
  );
}
