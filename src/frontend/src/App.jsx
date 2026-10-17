import { useState } from "react";
import Login from "./Login.jsx";
import Register from "./Register.jsx";
import { apiPost } from "./api.js";
import { useEffect } from "react";
import GalleryMap from "./GalleryMap.jsx";

export default function App() {
  const [user, setUser] = useState(null);
  const [view, setView] = useState("login");
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    fetch("/api/auth/me/", { credentials: "same-origin" })
      .then((response) => (response.ok ? response.json() : null))
      .then((data) => {
        if (data) setUser(data);
      })
      .catch(() => {})
      .finally(() => setChecking(false));
  }, []);
  if (checking) return null;

  async function logout() {
    try {
      await apiPost("/api/auth/logout/", {});
    } catch { }
    setUser(null);
    setView("login");
  }

  if (user) {
    return (
      <main>
        <h1>Welcome</h1>
        <p>Signed in as {user.email} ({user.role}).</p>
        <button type="button" onClick={logout}>Sign out</button>
        <GalleryMap role={user.role} />
      </main>
    );
  }

  return (
    <main>
      {view === "login" ? <Login onLoggedIn={setUser} /> : <Register />}
      <button type="button" onClick={() => setView(view === "login" ? "register" : "login")}>
        {view === "login" ? "Need an account? Create one" : "Have an account? Sign in"}
      </button>
    </main>
  );
}