import { useState } from "react";
import Login from "./Login.jsx";
import Register from "./Register.jsx";
import { apiPost } from "./api.js";

export default function App() {
  const [user, setUser] = useState(null);
  const [view, setView] = useState("login");

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