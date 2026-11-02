// Non-component resume helpers. Kept out of pages/Resume.jsx so that file only
// exports React components and Vite Fast Refresh keeps working.

export const MAX_RESUME_MB = 5;

/** URL of the full-tab resume viewer (opened in a new browser tab). */
export const resumeViewPath = (id) => `/resume/${id}/view`;

export function validateResumeFile(file) {
  if (!file) return 'Please choose a file';
  const ext = file.name.split('.').pop().toLowerCase();
  if (!['pdf', 'docx'].includes(ext)) return 'Only PDF and DOCX files are supported';
  if (file.size > MAX_RESUME_MB * 1024 * 1024) return `File is larger than ${MAX_RESUME_MB} MB`;
  if (file.size === 0) return 'The file is empty';
  return null;
}
