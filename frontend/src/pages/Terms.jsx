import { useDocumentTitle } from '../hooks/useAsync';

export default function Terms() {
  useDocumentTitle('Terms & Conditions');
  return (
    <div className="doc-page">
      <h1>Terms &amp; Conditions</h1>
      <p className="muted">Last updated: 2026</p>

      <h2>1. Using JobSense</h2>
      <p>JobSense helps you analyse your resume, discover jobs and explore career paths. You agree to use it lawfully and to
        provide accurate information in your account and profile.</p>

      <h2>2. Your content</h2>
      <p>You keep ownership of the resumes, profile details and photos you upload. You allow JobSense to process them solely
        to provide the service, such as extracting skills and calculating match scores. You can delete your resume at any time.</p>

      <h2>3. Job listings and recommendations</h2>
      <p>Job listings come from third-party providers and may change or expire. Match scores and career recommendations are
        estimates to guide your search; they are not guarantees of suitability, interviews or employment.</p>

      <h2>4. Accounts</h2>
      <p>Keep your password confidential and let us know about any unauthorised use. Accounts that misuse the service may be
        suspended.</p>

      <h2>5. Limitation of liability</h2>
      <p>JobSense is provided &ldquo;as is&rdquo; without warranties. We are not responsible for decisions made by employers
        or for the accuracy of third-party job listings.</p>

      <h2>6. Changes</h2>
      <p>We may update these terms from time to time. Continuing to use JobSense after changes means you accept the updated terms.</p>
    </div>
  );
}
