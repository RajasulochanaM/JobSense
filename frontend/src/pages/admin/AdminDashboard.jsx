import { Link } from 'react-router-dom';
import { Bookmark, Briefcase, ClipboardList, Compass, FileText, Sparkles, Users, BookOpen } from 'lucide-react';
import { adminApi } from '../../services/api';
import { useAsync, useDocumentTitle } from '../../hooks/useAsync';
import { ErrorState, PageHeader, Skeleton, StatCard } from '../../components/ui';

const LINKS = [
  { to: '/admin/users', label: 'Manage users', icon: Users },
  { to: '/admin/jobs', label: 'Manage jobs', icon: Briefcase },
  { to: '/admin/careers', label: 'Career paths & skills', icon: Compass },
  { to: '/admin/resources', label: 'Learning resources', icon: BookOpen },
  { to: '/admin/analytics', label: 'Analytics', icon: Sparkles },
];

export default function AdminDashboard() {
  useDocumentTitle('Admin');
  const { data, loading, error, reload } = useAsync(() => adminApi.stats(), []);
  const n = (v) => Number(v || 0).toLocaleString('en-IN');

  return (
    <div>
      <PageHeader title="Admin dashboard" description="System overview and management." />
      {loading && !data ? <Skeleton count={2} /> : error ? <ErrorState error={error} onRetry={reload} /> : (
        <>
          <div className="grid grid-4">
            <StatCard icon={Users} label="Total users" value={n(data.total_users)} sub={`${n(data.total_candidates)} candidates`} />
            <StatCard icon={FileText} label="Total resumes" value={n(data.total_resumes)} />
            <StatCard icon={Briefcase} label="Total jobs" value={n(data.total_jobs)} sub={data.mock_jobs ? `${n(data.mock_jobs)} are mock samples` : 'All from job provider'} />
            <StatCard icon={ClipboardList} label="Total applications" value={n(data.total_applications)} />
            <StatCard icon={Bookmark} label="Total saved jobs" value={n(data.total_saved_jobs)} />
            <StatCard icon={Sparkles} label="Job matches computed" value={n(data.total_matches)} />
            <StatCard icon={Compass} label="Career paths" value={n(data.total_careers)} />
            <StatCard icon={BookOpen} label="Learning resources" value={n(data.total_resources)} />
          </div>
          <section className="card" style={{ marginTop: '1rem' }} aria-labelledby="mgmt">
            <h2 id="mgmt">Management</h2>
            <div className="row">
              {LINKS.map(({ to, label, icon: Icon }) => (
                <Link key={to} to={to} className="btn btn-secondary"><Icon size={16} aria-hidden="true" /> {label}</Link>
              ))}
            </div>
          </section>
        </>
      )}
    </div>
  );
}
