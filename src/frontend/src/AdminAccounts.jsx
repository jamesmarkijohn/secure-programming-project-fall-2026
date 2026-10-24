import { useCallback, useEffect, useState } from "react";
import { apiGet } from "./api.js";
import AccountEditor from "./AccountEditor.jsx";

export default function AdminAccounts({ currentEmail }) {
  const [filters, setFilters] = useState({ role: "", email: "", includeDeleted: false });
  const [applied, setApplied] = useState(filters);
  const [page, setPage] = useState(1);
  const [result, setResult] = useState({ accounts: [], total: 0, page_size: 25 });
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");
  const [selected, setSelected] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    const params = new URLSearchParams({ page: String(page) });
    if (applied.role) params.set("role", applied.role);
    if (applied.email) params.set("email", applied.email);
    if (applied.includeDeleted) params.set("include_deleted", "1");
    try {
      const { ok, data } = await apiGet(`/api/admin/accounts/?${params}`);
      if (ok) {
        setResult(data);
        setMessage("");
      } else {
        setMessage(data.error || "Could not load accounts.");
      }
    } catch {
      setMessage("Could not reach the server.");
    } finally {
      setLoading(false);
    }
  }, [applied, page]);

  useEffect(() => {
    load();
  }, [load]);

  function search(event) {
    event.preventDefault();
    setPage(1);
    setApplied({ ...filters });
  }

  const lastPage = Math.max(1, Math.ceil(result.total / result.page_size));

  return (
    <section>
      <h2>Accounts</h2>

      <form onSubmit={search}>
        <label>
          Role
          <select value={filters.role} onChange={(e) => setFilters({ ...filters, role: e.target.value })}>
            <option value="">Any role</option>
            <option value="GUEST">Guest</option>
            <option value="EMPLOYEE">Employee</option>
            <option value="ADMIN">Admin</option>
          </select>
        </label>
        <label>
          Email contains
          <input type="text" maxLength={254} value={filters.email}
            onChange={(e) => setFilters({ ...filters, email: e.target.value })} />
        </label>
        <label>
          <input type="checkbox" checked={filters.includeDeleted}
            onChange={(e) => setFilters({ ...filters, includeDeleted: e.target.checked })} />
          Include deleted accounts
        </label>
        <button type="submit" disabled={loading}>Search</button>
      </form>

      {message && <p role="status">{message}</p>}
      {!loading && result.accounts.length === 0 && !message && <p>No matching accounts.</p>}

      {result.accounts.length > 0 && (
        <>
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Email</th>
                <th>Role</th>
                <th>Current room</th>
                <th>Created</th>
                <th>Status</th>
                <th>MFA</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {result.accounts.map((account) => (
                <tr key={account.user_id}>
                  <td>{account.user_id}</td>
                  <td>{account.email}</td>
                  <td>{account.role}</td>
                  <td>{account.room}</td>
                  <td>{new Date(account.created).toLocaleString()}</td>
                  <td>{account.is_active ? "Active" : "Deleted"}</td>
                  <td>{account.mfa_enrolled ? "Set up" : "Not set up"}</td>
                  <td>
                    <button type="button" onClick={() => setSelected(account.user_id)}>Manage</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <p>
            <button type="button" onClick={() => setPage(page - 1)} disabled={loading || page <= 1}>
              Previous
            </button>{" "}
            Page {page} of {lastPage} ({result.total} accounts){" "}
            <button type="button" onClick={() => setPage(page + 1)} disabled={loading || page >= lastPage}>
              Next
            </button>
          </p>
        </>
      )}

      {selected && (
        <AccountEditor
          key={selected}
          userId={selected}
          isSelf={result.accounts.some((a) => a.user_id === selected && a.email === currentEmail)}
          onChanged={load}
          onClose={() => setSelected(null)}
        />
      )}
    </section>
  );
}