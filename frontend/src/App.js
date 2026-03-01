import React, { useState, useEffect } from "react";
import { 
  BrowserRouter as Router, 
  Routes, 
  Route, 
  Link, 
  Navigate, 
  useNavigate 
} from "react-router-dom";
import { MessageSquare, ShieldCheck, LogOut, Sun, Moon } from "lucide-react";

import Admin from "./Admin";
import UserPage from "./Userpage";
import Login from "./pages/Login";
import "./App.css";

/* ===========================
   PRIVATE ROUTE
=========================== */

const PrivateRoute = ({ children }) => {
  const token = localStorage.getItem("token");
  return token ? children : <Navigate to="/login" replace />;
};

/* ===========================
   NAVBAR COMPONENT
=========================== */

const Navbar = ({ token, setToken }) => {
  const navigate = useNavigate();

  /* ---------- Theme Toggle ---------- */
  const [theme, setTheme] = useState(() => {
    return localStorage.getItem("theme") || "light";
  });

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("theme", theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme((prev) => (prev === "light" ? "dark" : "light"));
  };

  const handleLogout = () => {
    localStorage.removeItem("token");
    setToken(null);
    navigate("/login");
  };

  return (
    <nav className="navbar">
      <div className="nav-left">
        <h2>LogiAI</h2>
      </div>

      <div className="nav-right">
        <button
          className="theme-toggle-btn"
          onClick={toggleTheme}
          title={theme === "light" ? "Switch to Dark Mode" : "Switch to Light Mode"}
          aria-label="Toggle theme"
        >
          {theme === "light" ? <Moon size={16} /> : <Sun size={16} />}
        </button>

        <Link to="/" style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
          <MessageSquare size={15} /> Chat
        </Link>

        {token ? (
          <>
            <Link to="/admin" style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
              <ShieldCheck size={15} /> Dashboard
            </Link>
            <button className="logout-btn" onClick={handleLogout} style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
              <LogOut size={14} /> Logout
            </button>
          </>
        ) : (
          <Link to="/login" style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
            <ShieldCheck size={15} /> Admin
          </Link>
        )}
      </div>
    </nav>
  );
};

/* ===========================
   MAIN APP
=========================== */

function App() {
  const [token, setToken] = useState(localStorage.getItem("token"));

  useEffect(() => {
    const storedToken = localStorage.getItem("token");
    setToken(storedToken);
  }, []);

  return (
    <Router>
      <Navbar token={token} setToken={setToken} />

      <Routes>
        <Route path="/" element={<UserPage />} />
        <Route path="/login" element={<Login setToken={setToken} />} />

        <Route
          path="/admin"
          element={
            <PrivateRoute>
              <Admin />
            </PrivateRoute>
          }
        />
      </Routes>
    </Router>
  );
}

export default App;