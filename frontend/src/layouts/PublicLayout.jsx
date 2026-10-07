import { Suspense } from 'react';
import { Link, Outlet, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import Footer from '../components/Footer';
import { Skeleton } from '../components/ui';
import { Brand, UserMenu } from './AppLayout';

export default function PublicLayout() {
  const { user, isAdmin, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/', { replace: true });
  };

  return (
    <>
      <a href="#main" className="skip-link">Skip to content</a>
      <header className="public-header">
        <div className="public-header-inner">
          <Brand />
          <nav className="public-nav" aria-label="Account">
            {user ? (
              <UserMenu user={user} admin={isAdmin} onLogout={handleLogout} showDashboard />
            ) : (
              <>
                <Link className="btn btn-ghost btn-sm" to="/login">Log in</Link>
                <Link className="btn btn-primary btn-sm" to="/register">Create account</Link>
              </>
            )}
          </nav>
        </div>
      </header>
      <main id="main" tabIndex={-1}>
        <Suspense fallback={<div style={{ padding: 32 }}><Skeleton /></div>}>
          <Outlet />
        </Suspense>
      </main>
      <Footer />
    </>
  );
}
