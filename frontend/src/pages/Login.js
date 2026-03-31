import React, { useState, useEffect } from "react";
import { useNavigate, Link, useSearchParams } from "react-router-dom";
import { Box, AlertCircle, LogIn, ArrowLeft, ShieldCheck, User, Sun, Moon } from "lucide-react";
import { BASE_URL } from "../apiBase";

function Login({ setToken }) {
  const [searchParams] = useSearchParams();
  const initialRole = searchParams.get("role") === "admin" ? "admin" : "user";

  const [loginRole, setLoginRole] = useState(initialRole);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [theme, setTheme] = useState(() => localStorage.getItem("theme") || "light");

  const navigate = useNavigate();

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("theme", theme);
  }, [theme]);

  const toggleTheme = () => setTheme((p) => (p === "light" ? "dark" : "light"));

  const handleLogin = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const formData = new URLSearchParams();
      formData.append("username", username);
      formData.append("password", password);
      formData.append("grant_type", "password");

      const res = await fetch(`${BASE_URL}/login`, {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
        body: formData.toString(),
      });

      if (!res.ok) {
        let serverMessage = "Invalid username or password";
        try {
          const errBody = await res.json();
          if (typeof errBody?.detail === "string" && errBody.detail.trim()) {
            serverMessage = errBody.detail;
          }
        } catch {
          // Keep default message if response body is not JSON.
        }

        if (res.status >= 500) {
          setError(serverMessage || "Authentication service unavailable. Please try again.");
        } else {
          setError(serverMessage);
        }
        setLoading(false);
        return;
      }

      const data = await res.json();

      localStorage.setItem("token", data.access_token);
      localStorage.setItem("role", data.role || "user");
      setToken(data.access_token);

      // Redirect based on role
      if (data.role === "admin") {
        navigate("/admin");
      } else {
        navigate("/dashboard");
      }

    } catch (err) {
      console.error(err);
      setError("Server error. Try again.");
    }
    setLoading(false);
  };

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-top-row">
          <Link to="/" className="login-back-link">
            <ArrowLeft size={16} /> Back to Home
          </Link>
          <button className="theme-toggle-btn" onClick={toggleTheme} title="Toggle theme">
            {theme === "light" ? <Moon size={16} /> : <Sun size={16} />}
          </button>
        </div>

        <div className="login-logo">
          <div className="login-logo-icon">
            <Box size={28} color="#fff" />
          </div>
          <h2>Welcome Back</h2>
          <p>Sign in to access LogiAI</p>
        </div>

        {/* ── Role Tabs ── */}
        <div className="login-role-tabs">
          <button
            className={`login-role-tab ${loginRole === "user" ? "active" : ""}`}
            onClick={() => { setLoginRole("user"); setError(""); setUsername(""); setPassword(""); }}
          >
            <User size={16} /> User Login
          </button>
          <button
            className={`login-role-tab ${loginRole === "admin" ? "active" : ""}`}
            onClick={() => { setLoginRole("admin"); setError(""); setUsername(""); setPassword(""); }}
          >
            <ShieldCheck size={16} /> Admin Login
          </button>
        </div>

        <form onSubmit={handleLogin} className="login-form">
          <div className="login-field">
            <label>Username / Email</label>
            <input
              type="text"
              placeholder="Enter your username or email"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
          </div>

          <div className="login-field">
            <label>Password</label>
            <input
              type="password"
              placeholder="Enter your password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>

          <button type="submit" className="login-submit-btn" disabled={loading}>
            <LogIn size={18} /> {loading ? "Signing in..." : "Sign In"}
          </button>
        </form>

        {error && (
          <div className="login-error">
            <AlertCircle size={16} /> {error}
          </div>
        )}
      </div>
    </div>
  );
}

export default Login;