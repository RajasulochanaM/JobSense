import { Link } from 'react-router-dom';
import { Compass } from 'lucide-react';
import { EmptyState } from '../components/ui';
import { useDocumentTitle } from '../hooks/useAsync';

export default function NotFound() {
  useDocumentTitle('Page not found');
  return (
    <div className="auth-page">
      <div style={{ width: 'min(480px, 100%)' }}>
        <EmptyState icon={Compass} title="Page not found"
          action={<Link className="btn btn-primary" to="/">Back to home</Link>}>
          The page you are looking for does not exist or has moved.
        </EmptyState>
      </div>
    </div>
  );
}
