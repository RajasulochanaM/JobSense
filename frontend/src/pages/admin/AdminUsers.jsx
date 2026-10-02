import { useState } from 'react';
import { Users } from 'lucide-react';
import { adminApi } from '../../services/api';
import { useAsync, useDebounce, useDocumentTitle } from '../../hooks/useAsync';
import { useAuth } from '../../context/AuthContext';
import { useToast } from '../../context/ToastContext';
import { ConfirmDialog, EmptyState, ErrorState, PageHeader, Pagination, Skeleton } from '../../components/ui';
import { formatDate } from '../../utils/format';

const LIMIT = 20;

export default function AdminUsers() {
  useDocumentTitle('Users');
  const { user: me } = useAuth();
  const toast = useToast();
  const [q, setQ] = useState('');
  const [role, setRole] = useState('');
  const [offset, setOffset] = useState(0);
  const dq = useDebounce(q, 350);
  const { data, loading, error, reload } = useAsync(() => adminApi.users({ q: dq, role, limit: LIMIT, offset }), [dq, role, offset]);
  const [deleting, setDeleting] = useState(null);
  const [busy, setBusy] = useState(false);

  const toggleActive = async (u) => {
    try {
      await adminApi.setUserActive(u.user_id, !u.is_active);
      toast.success(u.is_active ? 'User deactivated' : 'User activated');
      reload({ silent: true });
    } catch (err) { toast.error(err.message); }
  };

  const doDelete = async () => {
    setBusy(true);
    try {
      await adminApi.deleteUser(deleting.user_id);
      toast.success('User deleted');
      setDeleting(null);
      reload({ silent: true });
    } catch (err) { toast.error(err.message); } finally { setBusy(false); }
  };

  return (
    <div>
      <PageHeader title="Users" description="Registered accounts. Password hashes are never exposed." />
      <div className="card row" style={{ alignItems: 'flex-end', marginBottom: '1rem' }}>
        <div className="field" style={{ marginBottom: 0, flex: '2 1 240px' }}>
          <label htmlFor="uq">Search name or email</label>
          <input id="uq" className="input" value={q} onChange={(e) => { setQ(e.target.value); setOffset(0); }} />
        </div>
        <div className="field" style={{ marginBottom: 0, flex: '1 1 150px' }}>
          <label htmlFor="ur">Role</label>
          <select id="ur" className="select" value={role} onChange={(e) => { setRole(e.target.value); setOffset(0); }}>
            <option value="">All roles</option><option value="candidate">Candidate</option><option value="admin">Admin</option>
          </select>
        </div>
      </div>
      {loading && !data ? <Skeleton /> : error ? <ErrorState error={error} onRetry={reload} /> : data.items.length === 0 ? (
        <EmptyState icon={Users} title="No users found" />
      ) : (
        <>
          <div className="table-wrap">
            <table className="table table-responsive">
              <thead><tr><th scope="col">Name</th><th scope="col">Email</th><th scope="col">Role</th><th scope="col">Resumes</th><th scope="col">Skills</th><th scope="col">Applications</th><th scope="col">Joined</th><th scope="col">Status</th><th scope="col"><span className="sr-only">Actions</span></th></tr></thead>
              <tbody>
                {data.items.map((u) => (
                  <tr key={u.user_id}>
                    <td data-label="Name">{u.name}</td>
                    <td data-label="Email" className="small">{u.email}</td>
                    <td data-label="Role"><span className={`badge ${u.role === 'admin' ? 'badge-burgundy' : ''}`}>{u.role}</span></td>
                    <td data-label="Resumes">{u.resume_count}</td>
                    <td data-label="Skills">{u.skill_count}</td>
                    <td data-label="Applications">{u.application_count}</td>
                    <td data-label="Joined" className="nowrap small">{formatDate(u.created_at)}</td>
                    <td data-label="Status"><span className={`badge ${u.is_active ? 'badge-success' : 'badge-error'}`}>{u.is_active ? 'Active' : 'Inactive'}</span></td>
                    <td data-label="Actions">
                      {u.user_id !== me.user_id && (
                        <div className="row" style={{ flexWrap: 'nowrap' }}>
                          <button type="button" className="btn btn-sm btn-secondary" onClick={() => toggleActive(u)}>{u.is_active ? 'Deactivate' : 'Activate'}</button>
                          {u.role !== 'admin' && <button type="button" className="btn btn-sm btn-danger" onClick={() => setDeleting(u)}>Delete</button>}
                        </div>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Pagination offset={offset} limit={LIMIT} total={data.total} onChange={setOffset} />
        </>
      )}
      {deleting && <ConfirmDialog title="Delete user?" danger confirmLabel="Delete user" busy={busy} onCancel={() => setDeleting(null)} onConfirm={doDelete}
        message={`This permanently deletes ${deleting.email} with their resumes, matches, saved jobs and applications.`} />}
    </div>
  );
}
