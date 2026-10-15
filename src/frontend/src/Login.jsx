import { useState } from "react";
import { apiPost } from "./api.js";
import { QRCodeSVG } from "qrcode.react";

export default function Login({ onLoggedIn }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [code, setCode] = useState("");
  const [stage, setStage] = useState("password");
  const [setup, setSetup] = useState(null);
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);

  async function submitPassword(event) {
    event.preventDefault();
    setBusy(true);
    setMessage("");
    try {
      const { ok, data } = await apiPost("/api/auth/login/", { email, password });
      if (ok) {
        setPassword("");
        setSetup(data.mfa_setup || null);
        setStage("mfa");
      } else {
        setMessage(data.error);
      }
    } catch {
      setMessage("Could not reach the server.");
    } finally {
      setBusy(false);
    }
  }

  async function submitCode(event) {
    event.preventDefault();
    setBusy(true);
    setMessage("");
    try {
      const { ok, data } = await apiPost("/api/auth/verify-mfa/", { code });
      if (ok) {
        onLoggedIn({ email, role: data.role });
        return;
      }
      setMessage(data.error);
      setCode("");
      if (data.error !== "Invalid MFA code.") {
        setStage("password");
        setSetup(null);
      }
    } catch {
      setMessage("Could not reach the server.");
    } finally {
      setBusy(false);
    }
  }

  if (stage === "mfa") {
    return (
      <section>
        <h1>Enter your code</h1>
        {setup && (
          <div>
            <p>First sign-in: scan this with your authenticator app, then enter the code it shows.</p>
            <QRCodeSVG value={setup.uri} size={200} />
            <p>Can't scan it? Enter this key manually: <code>{setup.secret}</code></p>
          </div>
        )}
        <form onSubmit={submitCode}>
          <label>
            Six-digit code
            <input inputMode="numeric" autoComplete="one-time-code" maxLength={6} required
              value={code} onChange={(e) => setCode(e.target.value)} />
          </label>
          <button type="submit" disabled={busy}>Verify</button>
        </form>
        <p>You have {setup ? "5 minutes" : "60 seconds"} to finish this step.</p>
        {message && <p role="status">{message}</p>}
      </section>
    );
  }

  return (
    <section>
      <h1>Sign in</h1>
      <form onSubmit={submitPassword}>
        <label>
          Email
          <input type="email" autoComplete="username" maxLength={254} required
            value={email} onChange={(e) => setEmail(e.target.value)} />
        </label>
        <label>
          Password
          <input type="password" autoComplete="current-password" required
            value={password} onChange={(e) => setPassword(e.target.value)} />
        </label>
        <button type="submit" disabled={busy}>Sign in</button>
      </form>
      {message && <p role="status">{message}</p>}
    </section>
  );
}