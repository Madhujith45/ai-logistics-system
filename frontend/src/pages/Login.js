import React, { useState } from "react";
import axios from "axios";
import { Lock, User, LogIn } from 'lucide-react';
import "../App.css";

function Login() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    const formData = new FormData();
    formData.append("username", username);
    formData.append("password", password);

    try {
      const res = await axios.post("http://127.0.0.1:8000/login", formData);
      localStorage.setItem("token", res.data.access_token);
      window.location.href = "/admin";
    } catch (err) {
      setError("Invalid username or password");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container" style={{ maxWidth: '400px', marginTop: '100px' }}>
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', marginBottom: '32px' }}>
        <div style={{ width: '64px', height: '64px', backgroundColor: 'var(--info-light)', borderRadius: '16px', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '16px' }}>
          <Lock className="text-primary" size={32} />
        </div>
        <h2 style={{ margin: 0 }}>Admin Login</h2>
        <p className="text-gray text-sm" style={{ marginTop: '8px' }}>Sign in to access the command center</p>
      </div>

      {error && (
        <div style={{ backgroundColor: 'var(--danger-light)', color: 'var(--danger)', padding: '12px', borderRadius: '8px', marginBottom: '20px', fontSize: '14px', textAlign: 'center', fontWeight: '500' }}>
          {error}
        </div>
      )}

      <form onSubmit={handleLogin}>
        <div style={{ position: 'relative', marginBottom: '16px' }}>
          <User size={18} className="text-gray" style={{ position: 'absolute', left: '14px', top: '14px' }} />
          <input 
            placeholder="Username" 
            value={username}
            onChange={e => setUsername(e.target.value)} 
            style={{ paddingLeft: '40px', margin: 0 }}
            required
          />
        </div>

        <div style={{ position: 'relative', marginBottom: '24px' }}>
          <Lock size={18} className="text-gray" style={{ position: 'absolute', left: '14px', top: '14px' }} />
          <input 
            type="password" 
            placeholder="Password" 
            value={password}
            onChange={e => setPassword(e.target.value)} 
            style={{ paddingLeft: '40px', margin: 0 }}
            required
          />
        </div>

        <button type="submit" disabled={loading} style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '8px' }}>
          {loading ? "Signing in..." : <><LogIn size={18} /> Sign In</>}
        </button>
      </form>
    </div>
  );
}

export default Login;
