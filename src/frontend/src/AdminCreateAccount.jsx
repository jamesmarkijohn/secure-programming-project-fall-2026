import { useState } from "react";
import { apiPost } from "./api.js";

export default function AdminCreateAccount() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState("EMPLOYEE");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();

    setMessage("");
    setError("");
    setLoading(true);

    try {
      const response = await apiPost(
        "/api/auth/admin/accounts/create/",
        { email, password, role }
      );

      if (!response.ok) {
        setError(response.data.error || "Could not create account.");
        return;
      }

      setMessage(
        `Account created successfully for ${response.data.email}. MFA enrollment is required at first login.`
      );

      setEmail("");
      setPassword("");
      setRole("EMPLOYEE");
    } catch {
      setError("Something went wrong while creating the account.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section>
      <h2>Create Employee or Admin Account</h2>

      <p>
        Only administrators can create these accounts.
        New users must set up MFA when they first log in.
      </p>

      <form onSubmit={handleSubmit}>
        <div>
          <label htmlFor="new-account-email">Email</label>
          <input
            id="new-account-email"
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            required
            autoComplete="off"
          />
        </div>

        <div>
          <label htmlFor="new-account-password">Temporary Password</label>
          <input
            id="new-account-password"
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            required
            autoComplete="new-password"
          />
        </div>

        <div>
          <label htmlFor="new-account-role">Account Role</label>
          <select
            id="new-account-role"
            value={role}
            onChange={(event) => setRole(event.target.value)}
          >
            <option value="EMPLOYEE">Employee</option>
            <option value="ADMIN">Admin</option>
          </select>
        </div>

        <button type="submit" disabled={loading}>
          {loading ? "Creating..." : "Create Account"}
        </button>
      </form>

      {message && <p role="status">{message}</p>}
      {error && <p role="alert">{error}</p>}
    </section>
  );
}