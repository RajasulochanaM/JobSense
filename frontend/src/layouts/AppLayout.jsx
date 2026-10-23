import { Suspense, useEffect, useRef, useState } from 'react';
import { Link, NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom';
import {
  Bookmark, BarChart3, BookOpen, Briefcase, ChevronDown, ClipboardList, Compass, FileText, GraduationCap,
  LayoutDashboard, LogOut, Menu, Search, User, Users,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import Avatar from '../components/Avatar';
import Footer from '../components/Footer';
import { Skeleton } from '../components/ui';

const CANDIDATE_NAV = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/resume', label: 'Resume & Matches', icon: FileText },
  { to: '/jobs', label: 'Find Jobs', icon: Search },
  { to: '/saved', label: 'Saved Jobs', icon: Bookmark },
  { to: '/applications', label: 'Applications', icon: ClipboardList },
  { to: '/careers', label: 'Career Paths', icon: Compass },
  { to: '/learning', label: 'Skills / Learning', icon: GraduationCap },
  { to: '/profile', label: 'Profile', icon: User },
];

const ADMIN_NAV = [
  { to: '/admin', label: 'Dashboard', icon: LayoutDashboard, end: true },
  { to: '/admin/users', label: 'Users', icon: Users },
  { to: '/admin/jobs', label: 'Jobs', icon: Briefcase },
  { to: '/admin/careers', label: 'Career Paths', icon: Compass },
  { to: '/admin/resources', label: 'Learning Resources', icon: BookOpen },
  { to: '/admin/analytics', label: 'Analytics', icon: BarChart3 },
];

const SIDEBAR_KEY = 'jobsense.sidebar';
const isMobile = () => typeof window !== 'undefined' && window.matchMedia?.('(max-width: 960px)').matches;

/** The brand always links to the public home page. */
export function Brand() {
  return (
    <Link to="/" className="sidebar-brand" aria-label="JobSense home">
      <span className="brand-mark" aria-hidden="true">J</span>
      <span>
        <span className="brand-name">JobSense</span>
        <span className="brand-tag">Resume &amp; job intelligence</span>
      </span>
    </Link>
  );
}

/** Avatar button with an account dropdown. `showDashboard` adds a dashboard link (used on public pages). */
export function UserMenu({ user, admin, onLogout, showDashboard = false }) {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);
  const location = useLocation();

  useEffect(() => setOpen(false), [location.pathname]);
  useEffect(() => {
    if (!open) return undefined;
    const onDown = (e) => { if (!ref.current?.contains(e.target)) setOpen(false); };
    const onKey = (e) => { if (e.key === 'Escape') setOpen(false); };
    document.addEventListener('mousedown', onDown);
    document.addEventListener('keydown', onKey);
    return () => { document.removeEventListener('mousedown', onDown); document.removeEventListener('keydown', onKey); };
  }, [open]);

  return (
    <div className="user-menu" ref={ref}>
      <button type="button" className="user-menu-trigger" onClick={() => setOpen((o) => !o)}
        aria-haspopup="menu" aria-expanded={open} aria-label="Account menu">
        <Avatar user={user} size={32} />
        <span className="user-menu-name">{user?.name}</span>
        <ChevronDown size={16} aria-hidden="true" />
      </button>
      {open && (
        <div className="user-menu-panel" role="menu">
          <div className="user-chip">
            <Avatar user={user} size={40} />
            <span className="who"><strong>{user?.name}</strong><span>{user?.email}</span></span>
          </div>
          {showDashboard && (
            <Link to={admin ? '/admin' : '/dashboard'} role="menuitem" className="user-menu-item">
              <LayoutDashboard size={16} aria-hidden="true" /> Go to Dashboard
            </Link>
          )}
          {!admin && (
            <Link to="/profile" role="menuitem" className="user-menu-item"><User size={16} aria-hidden="true" /> My profile</Link>
          )}
          <button type="button" role="menuitem" className="user-menu-item" onClick={onLogout}>
            <LogOut size={16} aria-hidden="true" /> Log out
          </button>
        </div>
      )}
    </div>
  );
}

export default function AppLayout({ admin = false }) {
  const { user, logout } = useAuth();
  // Desktop: persisted show/hide preference. Mobile: an overlay drawer that starts closed.
  const [open, setOpen] = useState(() => {
    if (isMobile()) return false;
    try { return localStorage.getItem(SIDEBAR_KEY) !== 'hidden'; } catch { return true; }
  });
  const location = useLocation();
  const navigate = useNavigate();
  const nav = admin ? ADMIN_NAV : CANDIDATE_NAV;

  useEffect(() => {
    if (isMobile()) setOpen(false);
    window.scrollTo(0, 0);
  }, [location.pathname]);

  const toggle = () => setOpen((o) => {
    if (!isMobile()) { try { localStorage.setItem(SIDEBAR_KEY, o ? 'hidden' : 'shown'); } catch { /* ignore */ } }
    return !o;
  });

  const handleLogout = async () => {
    await logout();
    navigate('/login', { replace: true });
  };

  return (
    <div className={`app-shell ${open ? 'sidebar-open' : 'sidebar-closed'}`}>
      <a href="#main" className="skip-link">Skip to content</a>

      <header className="topbar">
        <div className="topbar-left">
          <button type="button" className="btn btn-icon hamburger" onClick={toggle}
            aria-expanded={open} aria-controls="app-sidebar" aria-label={open ? 'Hide menu' : 'Show menu'}>
            <Menu size={20} />
          </button>
          <Brand />
        </div>
        <UserMenu user={user} admin={admin} onLogout={handleLogout} />
      </header>

      <aside id="app-sidebar" className="sidebar" aria-label="Main navigation" hidden={!open}>
        <nav>
          {admin && <div className="nav-section">Administration</div>}
          {nav.map(({ to, label, icon: Icon, end }) => (
            <NavLink key={to} to={to} end={end} className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
              <Icon size={18} aria-hidden="true" /> {label}
            </NavLink>
          ))}
          {user?.role === 'admin' && (
            <>
              <div className="nav-section">Switch view</div>
              <NavLink to={admin ? '/dashboard' : '/admin'} className="nav-link">
                {admin ? <User size={18} aria-hidden="true" /> : <BarChart3 size={18} aria-hidden="true" />}
                {admin ? 'Candidate view' : 'Admin console'}
              </NavLink>
            </>
          )}
        </nav>
      </aside>
      {open && <div className="sidebar-backdrop" onClick={() => setOpen(false)} aria-hidden="true" />}

      <div className="main">
        <main id="main" className="main-content" tabIndex={-1}>
          <Suspense fallback={<Skeleton count={3} />}>
            <Outlet />
          </Suspense>
        </main>
        <Footer />
      </div>
    </div>
  );
}
