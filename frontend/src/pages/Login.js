import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { ShieldCheck, AlertCircle, LogIn } from "lucide-react";

const BASE_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";

function Login({ setToken }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const navigate = useNavigate();

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
        setError("Invalid username or password");
        setLoading(false);
        return;
      }

      const data = await res.json();

      localStorage.setItem("token", data.access_token);
      setToken(data.access_token);

      navigate("/admin");

    } catch (err) {
      console.error(err);
      setError("Server error. Try again.");
    }
    setLoading(false);
  };

  return (
    <div className="login-container">
      <div style={{ textAlign: "center", marginBottom: "8px" }}>
        <div style={{
          width: 56, height: 56, borderRadius: 16,
          background: "linear-gradient(135deg, #1D4ED8, #2563EB)",
          display: "inline-flex", alignItems: "center", justifyContent: "center",
          boxShadow: "0 4px 20px rgba(37, 99, 235, 0.25)",
          marginBottom: 12
        }}>
          <ShieldCheck size={28} color="#FFFFFF" />
        </div>
      </div>
      <h2>Admin Login</h2>
      <p style={{ textAlign: "center", color: "var(--text-muted)", fontSize: 13, margin: "-16px 0 28px", position: "relative" }}>
        Secure access to the LogiAI dashboard
      </p>

      <form onSubmit={handleLogin}>
        <input
          type="text"
          placeholder="Username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          required
        />

        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />

        <button type="submit" disabled={loading} style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 8 }}>
          <LogIn size={18} /> {loading ? "Signing in..." : "Sign In"}
        </button>
      </form>

      {error && (
        <div style={{
          display: "flex", alignItems: "center", gap: 8,
          padding: "10px 14px", marginTop: 16,
          background: "rgba(239, 68, 68, 0.1)", borderRadius: 10,
          border: "1px solid rgba(239, 68, 68, 0.2)",
          color: "#f87171", fontSize: 13
        }}>
          <AlertCircle size={16} /> {error}
        </div>
      )}
    </div>
  );
}

export default Login;