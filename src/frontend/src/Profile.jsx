import { useEffect, useState } from "react";
import { apiPost } from "./api.js";

// Profile component allows a user to view and update their profile information
export default function Profile() {
  const [fullName, setFullName] = useState("");
  const [phone, setPhone] = useState("");
  const [loaded, setLoaded] = useState(false);
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);

  // Fetch profile information when the component mounts
  useEffect(() => {
    fetch("/api/auth/profile/", { credentials: "same-origin" })
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then((data) => {
        setFullName(data.full_name || "");
        setPhone(data.phone || "");
        setLoaded(true);
      })
      .catch(() => setMessage("Could not load your profile."));
  }, []);

  // Handle form submission to update the profile information
  async function handleSubmit(event) {
    event.preventDefault();
    setBusy(true);
    setMessage("");
    try {
      const { ok, data } = await apiPost("/api/auth/profile/", { full_name: fullName, phone });
      if (ok) {
        setFullName(data.full_name || "");
        setPhone(data.phone || "");
        setMessage("Profile saved.");
      } else {
        setMessage(data.error);
      }
    } catch {
      setMessage("Could not reach the server.");
    } finally {
      setBusy(false);
    }
  }

  // Render the profile form with full name and phone number fields
  return (
    <section>
      <h2>Your details</h2>
      {loaded && (
        <form onSubmit={handleSubmit}>
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
          <button type="submit" disabled={busy}>Save details</button>
        </form>
      )}
      {message && <p role="status">{message}</p>}
    </section>
  );
}