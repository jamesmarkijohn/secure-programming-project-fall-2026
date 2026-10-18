import { useState } from "react";
import { apiPost } from "./api.js";

//Account registration component, requiring username & password
export default function Register() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const [fullName, setFullName] = useState("");
  const [phone, setPhone] = useState("");

  async function handleSubmit(event) {
    event.preventDefault();
    setBusy(true);
    setMessage("");
    try {
      const { ok, data } = await apiPost("/api/auth/register/", {
        email, password, full_name: fullName, phone,
      });
      setMessage(data.message || data.error);
      if (ok) setPassword("");
    } catch {
      setMessage("Could not reach the server.");
    } finally {
      setBusy(false);
    }
  }

  //Render the registration form with email and password fields
  return (
    <section>
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
        <label>
          Full name (optional)
          <input type="text" autoComplete="name" maxLength={100}
            value={fullName} onChange={(e) => setFullName(e.target.value)} />
        </label>
        <label>
          Phone number (optional)
          <input type="tel" autoComplete="tel" maxLength={25}
            value={phone} onChange={(e) => setPhone(e.target.value)} />
        </label>
        <button type="submit" disabled={busy}>Create account</button>
      </form>
      {message && <p role="status">{message}</p>}
    </section>
  );
}