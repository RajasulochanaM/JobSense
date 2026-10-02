import { Link } from 'react-router-dom';
import { Bookmark, ClipboardList, Compass, FileText, Search, Sparkles, Target, Upload } from 'lucide-react';
import { profileApi } from '../services/api';
import { useAsync, useDocumentTitle } from '../hooks/useAsync';
import { EmptyState, ErrorState, Meter, MockBadge, PageHeader, Skeleton, SkillChips, StatCard } from '../components/ui';
import { formatDate, pct } from '../utils/format';
import './Dashboard.css';

const QUICK_ACTIONS = [
  { to: '/resume', label: 'Upload Resume', icon: Upload },
  { to: '/jobs', label: 'Find Jobs', icon: Search },
  { to: '/resume#recommended', label: 'View Matches', icon: Sparkles },
  { to: '/careers', label: 'Explore Career Paths', icon: Compass },
];

export default function Dashboard() {
  useDocumentTitle('Dashboard');
  const { data, loading, error, reload } = useAsync(() => profileApi.dashboard(), []);

  if (loading && !data) return <><PageHeader title="Dashboard" /><Skeleton count={3} /></>;
  if (error) return <><PageHeader title="Dashboard" /><ErrorState error={error} onRetry={reload} /></>;

  const { user, completeness, resume, stats, top_jobs: topJobs, recent_matches: recent, careers,
    top_matched_skills: topSkills, skill_gaps: gaps } = data;
  const firstName = user.name.split(' ')[0];

  return (
    <div className="dashboard">
      <PageHeader title={`Welcome, ${firstName}`}
        description="Your resume insights, matches and next steps at a glance." />

      <nav className="quick-actions" aria-label="Quick actions">
        {QUICK_ACTIONS.map(({ to, label, icon: Icon }) => (
          <Link key={to} to={to} className="quick-action"><Icon size={18} aria-hidden="true" />{label}</Link>
        ))}
      </nav>

      <div className="grid grid-4" style={{ marginBottom: '1rem' }}>
        <StatCard icon={Target} label="Top match score" value={stats.top_match_score === null ? '—' : pct(stats.top_match_score)}
          sub={stats.top_match_score === null ? 'Upload a resume to get scores' : 'Best current job alignment'} />
        <StatCard icon={Sparkles} label="Scored jobs" value={stats.recommended_jobs} sub="Jobs ranked for you" />
        <StatCard icon={Bookmark} label="Saved jobs" value={stats.saved_jobs} />
        <StatCard icon={ClipboardList} label="Applications" value={stats.applications}
          sub={`${stats.applications_by_status.Interview} interview · ${stats.applications_by_status.Offer} offer`} />
      </div>

      <div className="dash-grid">
        <div className="stack">
          <section className="card" aria-labelledby="top-jobs">
            <div className="card-header">
              <h2 id="top-jobs">Top recommended jobs</h2>
              <Link to="/resume#recommended" className="small">View all matches</Link>
            </div>
            {topJobs.length === 0 ? (
              <EmptyState icon={Search} title="No job matches yet"
                action={<Link className="btn btn-primary" to={resume.has_resume ? '/jobs' : '/resume'}>
                  {resume.has_resume ? 'Search jobs' : 'Upload your resume'}</Link>}>
                {resume.has_resume ? 'Search for jobs and JobSense will score them against your resume.'
                  : 'Upload your resume so JobSense can analyse your skills.'}
              </EmptyState>
            ) : (
              <ul className="list-plain list-divided">
                {topJobs.map((job) => (
                  <li key={job.job_id} className="dash-job">
                    <div style={{ minWidth: 0 }}>
                      <Link to={`/jobs/${job.job_id}`} className="dash-job-title">{job.title}</Link>
                      <div className="small muted">{job.company}{job.location ? ` · ${job.location}` : ''} {job.is_mock && <MockBadge />}</div>
                      <div style={{ marginTop: 6 }}><SkillChips skills={job.match.missing_skills} variant="missing" limit={3} emptyText="No missing skills" /></div>
                    </div>
                    <span className="dash-score" aria-label={`Match ${pct(job.match.final_score)}`}>{pct(job.match.final_score)}</span>
                  </li>
                ))}
              </ul>
            )}
          </section>

          <section className="card" aria-labelledby="careers-title">
            <div className="card-header">
              <h2 id="careers-title">Potential career paths</h2>
              <Link to="/careers" className="small">Explore all</Link>
            </div>
            {careers.length === 0 ? <p className="muted small">Career alignment appears after your skills are identified.</p> : (
              <ul className="list-plain list-divided">
                {careers.map((c) => (
                  <li key={c.career_id}>
                    <div className="row-between">
                      <Link to={`/careers/${c.career_id}`}><strong>{c.career_name}</strong></Link>
                      <span className="small">{pct(c.skill_alignment)} skill alignment</span>
                    </div>
                    <Meter value={c.skill_alignment} variant="butter" label={`${c.career_name} skill alignment`} />
                  </li>
                ))}
              </ul>
            )}
          </section>
        </div>

        <div className="stack">
          <section className="card" aria-labelledby="profile-title">
            <h2 id="profile-title">Profile completeness</h2>
            <div className="row-between"><span className="small muted">{completeness.percent}% complete</span></div>
            <Meter value={completeness.percent} label="Profile completeness" />
            <ul className="list-plain checklist">
              {completeness.checks.map((c) => (
                <li key={c.label} className={c.done ? 'done' : ''}>
                  <span aria-hidden="true">{c.done ? '✓' : '○'}</span> {c.label}
                  <span className="sr-only">{c.done ? '(complete)' : '(incomplete)'}</span>
                </li>
              ))}
            </ul>
            {completeness.percent < 100 && <Link to="/profile" className="btn btn-secondary btn-sm">Complete profile</Link>}
          </section>

          <section className="card" aria-labelledby="resume-title">
            <h2 id="resume-title">Resume status</h2>
            {resume.has_resume ? (
              <>
                <p className="row small"><FileText size={16} aria-hidden="true" /><strong>{resume.file_name}</strong></p>
                <p className="small muted">Uploaded {formatDate(resume.uploaded_at)} · {resume.skill_count} skills identified</p>
                <Link to="/resume" className="small">Manage resume</Link>
              </>
            ) : (
              <>
                <p className="small muted">No resume analysed yet.</p>
                <Link to="/resume" className="btn btn-primary btn-sm"><Upload size={15} aria-hidden="true" /> Upload resume</Link>
              </>
            )}
          </section>

          <section className="card" aria-labelledby="skills-title">
            <h2 id="skills-title">Top matched skills</h2>
            <SkillChips skills={topSkills.map((s) => s.skill)} variant="matched" emptyText="Appears once jobs are scored." />
            <h2 style={{ marginTop: '1.1rem' }}>Important skill gaps</h2>
            <SkillChips skills={gaps.map((g) => g.skill)} variant="missing" emptyText="No gaps identified yet." />
            {gaps.length > 0 && <Link to="/learning" className="btn btn-highlight btn-sm" style={{ marginTop: 12 }}>Find learning resources</Link>}
          </section>

          {recent.length > 0 && (
            <section className="card" aria-labelledby="recent-title">
              <h2 id="recent-title">Recent matches</h2>
              <ul className="list-plain list-divided">
                {recent.map((r) => (
                  <li key={r.job_id} className="row-between small">
                    <Link to={`/jobs/${r.job_id}`}>{r.title}</Link><span>{pct(r.final_score)}</span>
                  </li>
                ))}
              </ul>
            </section>
          )}
        </div>
      </div>
    </div>
  );
}
