import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('../services/api', async (orig) => {
  const actual = await orig();
  return {
    ...actual,
    authApi: { me: vi.fn(), login: vi.fn(), logout: vi.fn(), register: vi.fn() },
    profileApi: { ...actual.profileApi, dashboard: vi.fn() },
  };
});

import { authApi, profileApi } from '../services/api';
import { AuthProvider } from '../context/AuthContext';
import { ToastProvider } from '../context/ToastContext';
import Footer from '../components/Footer';
import JobCard from '../components/JobCard';
import Login, { validateLogin } from '../pages/Login';
import { validateRegister } from '../pages/Register';
import { validateResumeFile } from '../pages/Resume';
import Dashboard from '../pages/Dashboard';
import Landing from '../pages/Landing';
import PublicLayout from '../layouts/PublicLayout';

function renderWithProviders(ui, { route = '/' } = {}) {
  return render(
    <MemoryRouter initialEntries={[route]}>
      <ToastProvider><AuthProvider>{ui}</AuthProvider></ToastProvider>
    </MemoryRouter>,
  );
}

const JOB = {
  job_id: 7, title: 'React Developer', company: 'Kaveri Tech (Sample)', location: 'Chennai, India', remote: true,
  employment_type: 'Full-time', is_mock: true, is_saved: false, job_url: null, snippet: 'Build UIs', posted_at: null,
  required_skills: ['React', 'TypeScript'],
  match: { final_score: 72.5, text_similarity: 41.2, skill_match: 93.3, matched_skills: ['React', 'JavaScript'], missing_skills: ['TypeScript'], skill_data_available: true },
};

beforeEach(() => {
  localStorage.clear();
  vi.clearAllMocks();
});

describe('Footer', () => {
  it('renders a minimal copyright line with help and terms links', () => {
    render(<MemoryRouter><Footer /></MemoryRouter>);
    expect(screen.getByRole('contentinfo')).toHaveTextContent(`© ${new Date().getFullYear()} JobSense`);
    expect(screen.getByRole('link', { name: 'Help' })).toHaveAttribute('href', '/help');
    expect(screen.getByRole('link', { name: 'Terms & Conditions' })).toHaveAttribute('href', '/terms');
  });
});

describe('Public header', () => {
  it('shows Log in for guests', () => {
    renderWithProviders(<PublicLayout />);
    expect(screen.getByRole('link', { name: 'Log in' })).toHaveAttribute('href', '/login');
  });

  it('replaces Log in with an account menu offering dashboard and logout', async () => {
    localStorage.setItem('jobsense_token', 't');
    authApi.me.mockResolvedValue({ user: { name: 'Asha Rao', email: 'asha@example.com', role: 'candidate' } });
    renderWithProviders(<PublicLayout />);
    const trigger = await screen.findByRole('button', { name: 'Account menu' });
    expect(screen.queryByRole('link', { name: 'Log in' })).not.toBeInTheDocument();
    await userEvent.click(trigger);
    expect(screen.getByRole('menuitem', { name: /go to dashboard/i })).toHaveAttribute('href', '/dashboard');
    expect(screen.getByRole('menuitem', { name: /log out/i })).toBeInTheDocument();
  });
});

describe('Landing page', () => {
  it('shows the hero and primary calls to action', () => {
    renderWithProviders(<Landing />);
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Understand your resume.');
    expect(screen.getByRole('link', { name: 'Analyze My Resume' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Explore Jobs' })).toBeInTheDocument();
  });
});

describe('Login form', () => {
  it('validates input before calling the API', async () => {
    renderWithProviders(<Login />, { route: '/login' });
    await userEvent.click(screen.getByRole('button', { name: /log in/i }));
    expect(screen.getByText('Email is required')).toBeInTheDocument();
    expect(screen.getByText('Password is required')).toBeInTheDocument();
    expect(authApi.login).not.toHaveBeenCalled();
  });

  it('shows the server error on invalid credentials', async () => {
    authApi.login.mockRejectedValue(new Error('Invalid email or password'));
    renderWithProviders(<Login />, { route: '/login' });
    await userEvent.type(screen.getByLabelText('Email'), 'a@b.com');
    await userEvent.type(screen.getByLabelText('Password'), 'wrongpass1');
    await userEvent.click(screen.getByRole('button', { name: /log in/i }));
    expect(await screen.findByText('Invalid email or password')).toBeInTheDocument();
    expect(authApi.login).toHaveBeenCalledWith({ email: 'a@b.com', password: 'wrongpass1' });
  });

  it('validation helpers behave', () => {
    expect(validateLogin({ email: 'bad', password: 'x' })).toEqual({ email: 'Enter a valid email address' });
    expect(Object.keys(validateRegister({ name: 'A', email: 'x@y.io', password: 'abc', password_confirmation: 'abd' })))
      .toEqual(['name', 'password', 'password_confirmation']);
    expect(validateResumeFile(new File(['x'], 'cv.txt'))).toMatch(/PDF and DOCX/);
    expect(validateResumeFile(new File(['x'], 'cv.pdf'))).toBeNull();
  });
});

describe('JobCard', () => {
  it('renders the match explanation and labels mock listings', async () => {
    const onToggleSave = vi.fn();
    render(<MemoryRouter><JobCard job={JOB} onToggleSave={onToggleSave} /></MemoryRouter>);
    expect(screen.getByRole('link', { name: 'React Developer' })).toHaveAttribute('href', '/jobs/7');
    expect(screen.getByText('73%')).toBeInTheDocument();
    expect(screen.getByText(/Text similarity 41% · Skill match 93%/)).toBeInTheDocument();
    expect(screen.getByText('Sample listing')).toBeInTheDocument();
    expect(screen.getByRole('list', { name: 'Missing skills' })).toHaveTextContent('TypeScript');
    await userEvent.click(screen.getByRole('button', { name: 'Save React Developer' }));
    expect(onToggleSave).toHaveBeenCalledWith(JOB);
  });
});

describe('Dashboard', () => {
  it('renders summary data from the API', async () => {
    profileApi.dashboard.mockResolvedValue({
      user: { name: 'Priya Sharma', email: 'p@example.com' },
      completeness: { percent: 50, checks: [{ label: 'Resume uploaded', done: true }, { label: 'Interests', done: false }] },
      resume: { has_resume: true, file_name: 'cv.pdf', uploaded_at: '2026-09-01T10:00:00', skill_count: 9 },
      stats: { top_match_score: 72.5, recommended_jobs: 12, saved_jobs: 3, applications: 2,
        applications_by_status: { Saved: 0, Applied: 1, Interview: 1, Offer: 0, Rejected: 0, Withdrawn: 0 } },
      top_jobs: [JOB], recent_matches: [], careers: [], interests: [],
      top_matched_skills: [{ skill: 'React', count: 3 }], skill_gaps: [{ skill: 'TypeScript', count: 2 }],
    });
    renderWithProviders(<Dashboard />, { route: '/dashboard' });
    expect(await screen.findByRole('heading', { name: 'Welcome, Priya' })).toBeInTheDocument();
    expect(screen.getByText('cv.pdf')).toBeInTheDocument();
    expect(screen.getByText('12')).toBeInTheDocument();
    await waitFor(() => expect(screen.getByRole('link', { name: 'React Developer' })).toBeInTheDocument());
  });
});
