import axios from 'axios';

/** Base URL of the Flask API. Only public configuration is exposed through Vite. */
export const API_URL = (import.meta.env.VITE_API_URL || 'http://localhost:5000').replace(/\/$/, '');

const TOKEN_KEY = 'jobsense_token';

export const tokenStore = {
  get: () => {
    try { return localStorage.getItem(TOKEN_KEY); } catch { return null; }
  },
  set: (token) => {
    try { localStorage.setItem(TOKEN_KEY, token); } catch { /* storage unavailable */ }
  },
  clear: () => {
    try { localStorage.removeItem(TOKEN_KEY); } catch { /* storage unavailable */ }
  },
};

const client = axios.create({ baseURL: `${API_URL}/api`, timeout: 60000 });

client.interceptors.request.use((config) => {
  const token = tokenStore.get();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

let onUnauthorized = null;
export function setUnauthorizedHandler(fn) { onUnauthorized = fn; }

/** Normalised error thrown by every API call. */
export class ApiError extends Error {
  constructor(message, { status = 0, code = 'NETWORK_ERROR', details = null } = {}) {
    super(message);
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      const body = error.response.data || {};
      const status = error.response.status;
      if (status === 401 && onUnauthorized && !error.config?.url?.startsWith('/auth/login')) onUnauthorized();
      return Promise.reject(new ApiError(body.message || 'Request failed', {
        status, code: body.error?.code || 'HTTP_ERROR', details: body.error?.details || null,
      }));
    }
    if (error.code === 'ECONNABORTED') {
      return Promise.reject(new ApiError('The request timed out. Please try again.', { code: 'TIMEOUT' }));
    }
    return Promise.reject(new ApiError('Cannot reach the JobSense server. Check your connection and try again.'));
  },
);

/** Unwrap the {success, data, message} envelope. */
const unwrap = (promise) => promise.then((res) => res.data.data);
const withMessage = (promise) => promise.then((res) => ({ data: res.data.data, message: res.data.message }));

export const authApi = {
  register: (body) => unwrap(client.post('/auth/register', body)),
  login: (body) => unwrap(client.post('/auth/login', body)),
  logout: () => unwrap(client.post('/auth/logout')),
  me: () => unwrap(client.get('/auth/me')),
};

export const profileApi = {
  get: () => unwrap(client.get('/profile')),
  update: (body) => unwrap(client.put('/profile', body)),
  skills: () => unwrap(client.get('/profile/skills')),
  addSkill: (skill_name) => unwrap(client.post('/profile/skills', { skill_name })),
  removeSkill: (id) => unwrap(client.delete(`/profile/skills/${id}`)),
  taxonomy: () => unwrap(client.get('/skills')),
  interests: () => unwrap(client.get('/interests')),
  uploadAvatar: (image) => unwrap(client.put('/profile/avatar', { image })),
  removeAvatar: () => unwrap(client.delete('/profile/avatar')),
  dashboard: () => unwrap(client.get('/dashboard')),
};

export const resumeApi = {
  list: () => unwrap(client.get('/resumes')),
  get: (id) => unwrap(client.get(`/resumes/${id}`)),
  upload: (file, onUploadProgress) => {
    const form = new FormData();
    form.append('file', file);
    return unwrap(client.post('/resumes', form, { onUploadProgress, timeout: 120000 }));
  },
  remove: (id) => unwrap(client.delete(`/resumes/${id}`)),
};

export const jobsApi = {
  list: (params) => unwrap(client.get('/jobs', { params })),
  search: (body) => withMessage(client.post('/jobs/search', body, { timeout: 90000 })),
  get: (id) => unwrap(client.get(`/jobs/${id}`)),
  provider: () => unwrap(client.get('/jobs/provider')),
};

export const matchesApi = {
  list: (params) => unwrap(client.get('/matches', { params })),
  get: (jobId) => unwrap(client.get(`/matches/${jobId}`)),
  refresh: (fetch = false) => withMessage(client.post('/matches/refresh', { fetch }, { timeout: 120000 })),
};

export const savedApi = {
  list: () => unwrap(client.get('/saved-jobs')),
  save: (jobId) => unwrap(client.post(`/saved-jobs/${jobId}`)),
  unsave: (jobId) => unwrap(client.delete(`/saved-jobs/${jobId}`)),
};

export const applicationsApi = {
  list: (params) => unwrap(client.get('/applications', { params })),
  create: (body) => unwrap(client.post('/applications', body)),
  update: (id, body) => unwrap(client.put(`/applications/${id}`, body)),
  remove: (id) => unwrap(client.delete(`/applications/${id}`)),
};

export const careersApi = {
  list: () => unwrap(client.get('/careers')),
  get: (id) => unwrap(client.get(`/careers/${id}`)),
  recommendations: (refresh = false) => unwrap(client.get('/career-recommendations', { params: refresh ? { refresh: 1 } : {} })),
};

export const learningApi = {
  list: (params) => unwrap(client.get('/learning-resources', { params })),
  forSkill: (skill) => unwrap(client.get(`/learning-resources/${encodeURIComponent(skill)}`)),
};

export const adminApi = {
  stats: () => unwrap(client.get('/admin/stats')),
  analytics: () => unwrap(client.get('/admin/analytics')),
  users: (params) => unwrap(client.get('/admin/users', { params })),
  setUserActive: (id, is_active) => unwrap(client.patch(`/admin/users/${id}`, { is_active })),
  deleteUser: (id) => unwrap(client.delete(`/admin/users/${id}`)),
  careers: () => unwrap(client.get('/admin/careers')),
  createCareer: (body) => unwrap(client.post('/admin/careers', body)),
  updateCareer: (id, body) => unwrap(client.put(`/admin/careers/${id}`, body)),
  deleteCareer: (id) => unwrap(client.delete(`/admin/careers/${id}`)),
  createResource: (body) => unwrap(client.post('/admin/learning-resources', body)),
  updateResource: (id, body) => unwrap(client.put(`/admin/learning-resources/${id}`, body)),
  deleteResource: (id) => unwrap(client.delete(`/admin/learning-resources/${id}`)),
  jobs: (params) => unwrap(client.get('/admin/jobs', { params })),
  deleteJob: (id) => unwrap(client.delete(`/admin/jobs/${id}`)),
  deleteMockJobs: () => unwrap(client.delete('/admin/jobs/mock')),
};
