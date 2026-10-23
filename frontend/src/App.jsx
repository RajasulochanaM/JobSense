import { lazy } from 'react';
import { Navigate, Route, Routes } from 'react-router-dom';
import AppLayout from './layouts/AppLayout';
import PublicLayout from './layouts/PublicLayout';
import { GuestOnly, RequireAdmin, RequireAuth } from './components/RouteGuards';
import Landing from './pages/Landing';
import Login from './pages/Login';
import Register from './pages/Register';

// Authenticated pages are code-split so the landing/login bundle stays small.
const Dashboard = lazy(() => import('./pages/Dashboard'));
const Resume = lazy(() => import('./pages/Resume'));
const Jobs = lazy(() => import('./pages/Jobs'));
const JobDetails = lazy(() => import('./pages/JobDetails'));
const SavedJobs = lazy(() => import('./pages/SavedJobs'));
const Applications = lazy(() => import('./pages/Applications'));
const Careers = lazy(() => import('./pages/Careers'));
const CareerDetails = lazy(() => import('./pages/CareerDetails'));
const Learning = lazy(() => import('./pages/Learning'));
const Profile = lazy(() => import('./pages/Profile'));
const NotFound = lazy(() => import('./pages/NotFound'));
const Help = lazy(() => import('./pages/Help'));
const Terms = lazy(() => import('./pages/Terms'));
const AdminDashboard = lazy(() => import('./pages/admin/AdminDashboard'));
const AdminUsers = lazy(() => import('./pages/admin/AdminUsers'));
const AdminJobs = lazy(() => import('./pages/admin/AdminJobs'));
const AdminCareers = lazy(() => import('./pages/admin/AdminCareers'));
const AdminResources = lazy(() => import('./pages/admin/AdminResources'));
const AdminAnalytics = lazy(() => import('./pages/admin/AdminAnalytics'));

export default function App() {
  return (
    <Routes>
      <Route element={<PublicLayout />}>
        <Route path="/" element={<Landing />} />
        <Route path="/help" element={<Help />} />
        <Route path="/terms" element={<Terms />} />
        <Route element={<GuestOnly />}>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
        </Route>
      </Route>

      <Route element={<RequireAuth />}>
        <Route element={<AppLayout />}>
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/resume" element={<Resume />} />
          <Route path="/jobs" element={<Jobs />} />
          <Route path="/jobs/:jobId" element={<JobDetails />} />
          {/* "My Matches" now lives on the Resume page. */}
          <Route path="/matches" element={<Navigate to="/resume#recommended" replace />} />
          <Route path="/saved" element={<SavedJobs />} />
          <Route path="/applications" element={<Applications />} />
          <Route path="/careers" element={<Careers />} />
          <Route path="/careers/:careerId" element={<CareerDetails />} />
          <Route path="/learning" element={<Learning />} />
          <Route path="/profile" element={<Profile />} />
        </Route>
      </Route>

      <Route element={<RequireAdmin />}>
        <Route element={<AppLayout admin />}>
          <Route path="/admin" element={<AdminDashboard />} />
          <Route path="/admin/users" element={<AdminUsers />} />
          <Route path="/admin/jobs" element={<AdminJobs />} />
          <Route path="/admin/careers" element={<AdminCareers />} />
          <Route path="/admin/resources" element={<AdminResources />} />
          <Route path="/admin/analytics" element={<AdminAnalytics />} />
        </Route>
      </Route>

      <Route element={<PublicLayout />}>
        <Route path="/404" element={<NotFound />} />
        <Route path="*" element={<Navigate to="/404" replace />} />
      </Route>
    </Routes>
  );
}
