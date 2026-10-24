import { useEffect, useState } from "react";
import { Navigate, NavLink, Route, Routes, useNavigate } from "react-router";
import "./App.css";
import Login from "./Login.jsx";
import Register from "./Register.jsx";
import { apiPost } from "./api.js";
import HomePage from "./pages/HomePage.jsx";
import StaffPage from "./pages/StaffPage.jsx";
import AdminPage from "./pages/AdminPage.jsx";

const STAFF_ROLES = ["EMPLOYEE", "ADMIN"];

// Shows a page only to the listed roles, anyone else is sent home
function RequireRole({ user, roles, children }) {
  return roles.includes(user.role) ? children : <Navigate to="/" replace />;
}

export default function App() {
  const [user, setUser] = useState(null);
  const [view, setView] = useState("login");
  const [checking, setChecking] = useState(true);
  const navigate = useNavigate();

  // On page load, ask the server whether this browser already has a session.
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

  function signedOut() {
    setUser(null);
    setView("login");
    navigate("/", { replace: true });
  }

  async function logout() {
    try {
      await apiPost("/api/auth/logout/", {});
    } catch {
      // Even if the server can't be reached, clear the screen.
    }
    signedOut();
  }

  if (!user) {
    return (
      <main>
        {view === "login" ? <Login onLoggedIn={setUser} /> : <Register />}
        <button type="button" onClick={() => setView(view === "login" ? "register" : "login")}>
          {view === "login" ? "Need an account? Create one" : "Have an account? Sign in"}
        </button>
      </main>
    );
  }

  return (
    <main>
      <header>
        <nav aria-label="Main">
          <NavLink to="/" end>Home</NavLink>
          {STAFF_ROLES.includes(user.role) && <NavLink to="/staff">Staff</NavLink>}
          {user.role === "ADMIN" && <NavLink to="/admin">Admin</NavLink>}
        </nav>
        <p>Signed in as {user.email} ({user.role}).</p>
        <button type="button" onClick={logout}>Sign out</button>
      </header>

      <Routes>
        <Route path="/" element={<HomePage user={user} onDeleted={signedOut} />} />
        <Route
          path="/staff"
          element={
            <RequireRole user={user} roles={STAFF_ROLES}>
              <StaffPage user={user} />
            </RequireRole>
          }
        />
        <Route
          path="/admin"
          element={
            <RequireRole user={user} roles={["ADMIN"]}>
              <AdminPage user={user} />
            </RequireRole>
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </main>
  );
}