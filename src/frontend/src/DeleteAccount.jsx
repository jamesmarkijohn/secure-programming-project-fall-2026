import { useState } from "react";
import { apiPost } from "./api.js";

// DeleteAccount component allows a user to delete their account by confirming their password
// Handles the form submission, communicates with the backend API, manages the UI state for feedback and status.
export default function DeleteAccount({ onDeleted }) {
  const [open, setOpen] = useState(false);
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    setBusy(true);
    setMessage("");
    try {
      const { ok, data } = await apiPost("/api/auth/delete-account/", { password });
      setPassword("");
      if (ok) {
        onDeleted();
        return;
      }
      setMessage(data.error);
    } catch {
      setMessage("Could not reach the server.");
    } finally {
      setBusy(false);
    }
  }

  if (!open) {
    return <button type="button" onClick={() => setOpen(true)}>Delete my account</button>;
  }

  return (
    <section>
      <h2>Delete your account</h2>
      <p>
        This removes your email and personal details permanently. Records of your
        visits are kept without your name. You must be outside the gallery.
      </p>
      <form onSubmit={handleSubmit}>
        <label>
          Confirm your password
          <input type="password" autoComplete="current-password" required
            value={password} onChange={(e) => setPassword(e.target.value)} />
        </label>
        <button type="submit" disabled={busy}>Delete account</button>
        <button type="button" onClick={() => { setOpen(false); setMessage(""); }}>Cancel</button>
      </form>
      {message && <p role="status">{message}</p>}
    </section>
  );
}