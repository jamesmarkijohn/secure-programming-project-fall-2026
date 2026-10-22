import { useEffect, useState } from "react";
import { apiGet } from "./api.js";

export default function AdminAccounts() {
  const [accounts, setAccounts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadAccounts() {
      try {
        const response = await apiGet("/api/auth/admin/accounts/");

        if (!response.ok) {
          setError("Could not load accounts.");
          return;
        }

        setAccounts(response.data.accounts);
      } catch {
        setError("Something went wrong while loading accounts.");
      } finally {
        setLoading(false);
      }
    }

    loadAccounts();
  }, []);

  return (
    <section>
      <h2>Account Database</h2>

      {loading && <p>Loading accounts...</p>}
      {error && <p role="alert">{error}</p>}

      {!loading && !error && accounts.length === 0 && (
        <p>No accounts found.</p>
      )}

      {!loading && !error && accounts.length > 0 && (
        <table>
          <thead>
            <tr>
              <th>Account ID</th>
              <th>Email</th>
              <th>Role</th>
              <th>Current Room</th>
              <th>Created</th>
              <th>Status</th>
              <th>MFA</th>
            </tr>
          </thead>

          <tbody>
            {accounts.map((account) => (
              <tr key={account.user_id}>
                <td>{account.user_id}</td>
                <td>{account.email}</td>
                <td>{account.role}</td>
                <td>{account.room}</td>
                <td>{new Date(account.created).toLocaleString()}</td>
                <td>{account.is_active ? "Active" : "Deleted"}</td>
                <td>{account.mfa_enrolled ? "Enabled" : "Not enrolled"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}