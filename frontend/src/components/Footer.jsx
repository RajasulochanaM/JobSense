import { Link } from 'react-router-dom';

export default function Footer() {
  return (
    <footer className="site-footer">
      <span>&copy; {new Date().getFullYear()} JobSense. All rights reserved.</span>
      <nav aria-label="Footer">
        <Link to="/help">Help</Link>
        <Link to="/terms">Terms &amp; Conditions</Link>
      </nav>
    </footer>
  );
}
