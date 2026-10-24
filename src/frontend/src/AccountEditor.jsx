import { useEffect, useRef, useState } from "react";
import { apiGet, apiPost } from "./api.js";

export default function AccountEditor({ userId, isSelf, onChanged, onClose }) {
  const [account, setAccount] = useState(null);
  const [form, setForm] = useState({ role: "", full_name: "", phone: "" });
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const panelRef = useRef(null);

  useEffect(() => {
    apiGet(`/api/admin/accounts/${userId}/`)
      .then(({ ok, data }) => {
        if (!ok) {
          setMessage(data.error || "Could not load the account.");
          return;
        }
        setAccount(data);
        setForm({ role: data.role, full_name: data.full_name || "", phone: data.phone || "" });
        panelRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
      })
      .catch(() => setMessage("Could not reach the server."));
  }, [userId]);

  async function run(path, body, confirmText) {
    if (confirmText && !window.confirm(confirmText)) return null;
    setBusy(true);
    setMessage("");
    try {
      const { ok, data } = await apiPost(path, body);
      setMessage(ok ? data.message || "Saved." : data.error);
      if (ok) onChanged();
      return ok ? data : null;
    } catch {
      setMessage("Could not reach the server.");
      return null;
    } finally {
      setBusy(false);
    }
  }

  async function save(event) {
    event.preventDefault();
    const roleChanged = form.role !== account.role;
    const data = await run(
      `/api/admin/accounts/${userId}/update/`,
      form,
      roleChanged ? `Change ${account.email} from ${account.role} to ${form.role}? They will be signed out.` : null,
    );
    if (data) {
      setAccount(data);
      setForm({ role: data.role, full_name: data.full_name || "", phone: data.phone || "" });
    }
  }

  async function resetMfa() {
    await run(
      `/api/admin/accounts/${userId}/reset-mfa/`,
      {},
      `Reset MFA for ${account.email}? They will be signed out and must set up their authenticator again.`,
    );
  }

  async function remove() {
    const data = await run(
      `/api/admin/accounts/${userId}/delete/`,
      {},
      `Delete ${account.email}? Their personal details are removed permanently; their history is kept anonymously.`,
    );
    if (data) onClose();
  }

  const set = (field) => (e) => setForm({ ...form, [field]: e.target.value });

  return (
    <section ref={panelRef}>
      <h3>Manage account #{userId}</h3>
      {account && (
        <>
          <p>
            {account.email}, currently in {account.room}.{" "}
            {account.is_active ? "Active" : "Deleted"}, MFA {account.mfa_enrolled ? "set up" : "not set up"}.
          </p>
          {account.is_active && (
            <form onSubmit={save}>
              <label>
                Role
                <select value={form.role} onChange={set("role")} disabled={isSelf}>
                  <option value="GUEST">Guest</option>
                  <option value="EMPLOYEE">Employee</option>
                  <option value="ADMIN">Admin</option>
                </select>
              </label>
              <label>
                Full name
                <input type="text" maxLength={100} value={form.full_name} onChange={set("full_name")} />
              </label>
              <label>
                Phone number
                <input type="tel" maxLength={25} value={form.phone} onChange={set("phone")} />
              </label>
              <button type="submit" disabled={busy}>Save changes</button>
              <button type="button" onClick={resetMfa} disabled={busy}>Reset MFA</button>
              {!isSelf && (
                <button type="button" onClick={remove} disabled={busy}>Delete account</button>
              )}
            </form>
          )}
        </>
      )}
      {message && <p role="status">{message}</p>}
      <button type="button" onClick={onClose}>Close</button>
    </section>
  );
}