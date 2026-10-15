import { useState } from "react";

function getCookie(name) {
  const match = document.cookie.match(new RegExp("(?:^|; )" + name + "=([^;]*)"));
  return match ? decodeURIComponent(match[1]) : "";
}

export default function App() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    setBusy(true);
    setMessage("");
    try {
      await fetch("/api/auth/csrf/", { credentials: "same-origin" });
      const response = await fetch("/api/auth/register/", {
        method: "POST",
        credentials: "same-origin",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCookie("csrftoken"),
        },
        body: JSON.stringify({ email, password }),
      });
      const data = await response.json();
      setMessage(data.message || data.error);
      if (response.ok) setPassword("");
    } catch {
      setMessage("Could not reach the server.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main>
      <h1>Art Gallery</h1>
      <h2>Create an account</h2>
      <form onSubmit={handleSubmit}>
        <label>
          Email
          <input type="email" autoComplete="email" maxLength={254} required
            value={email} onChange={(e) => setEmail(e.target.value)} />
        </label><br></br><br></br>
        <label>
          Password
          <input type="password" autoComplete="new-password" required
            value={password} onChange={(e) => setPassword(e.target.value)} />
        </label><br></br><br></br>
        <button type="submit" disabled={busy}>Create account</button>
      </form>
      {message && <p role="status">{message}</p>}
    </main>
  );
}