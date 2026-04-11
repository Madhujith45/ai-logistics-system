import React, { useEffect, useRef, useState } from "react";
import { useNavigate, Link, useSearchParams } from "react-router-dom";
import { Box, AlertCircle, LogIn, ArrowLeft, ShieldCheck, User, Sun, Moon, UserPlus } from "lucide-react";
import { BASE_URL } from "../apiBase";

function Login({ setToken }) {
  const [searchParams] = useSearchParams();
  const initialRole = searchParams.get("role") === "admin" ? "admin" : "user";
  const GOOGLE_CLIENT_ID = process.env.REACT_APP_GOOGLE_CLIENT_ID;

  const [loginRole, setLoginRole] = useState(initialRole);
  const [authMode, setAuthMode] = useState("login");
  const [name, setName] = useState("");
  const [emailOrUsername, setEmailOrUsername] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [googleReady, setGoogleReady] = useState(false);
  const [theme, setTheme] = useState(() => localStorage.getItem("theme") || "light");
  const googleButtonRef = useRef(null);

  const navigate = useNavigate();

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("theme", theme);
  }, [theme]);

  useEffect(() => {
    setError("");
    setSuccessMessage("");
    setEmailOrUsername("");
    setPassword("");
    setName("");
    setConfirmPassword("");
    if (loginRole === "admin") {
      setAuthMode("login");
    }
  }, [loginRole]);

  useEffect(() => {
    if (loginRole !== "user" || authMode !== "login" || !GOOGLE_CLIENT_ID) {
      return;
    }

    let cancelled = false;

    const initializeGoogle = () => {
      if (cancelled || !window.google?.accounts?.id || !googleButtonRef.current) return;

      window.google.accounts.id.initialize({
        client_id: GOOGLE_CLIENT_ID,
        callback: async (response) => {
          if (!response?.credential) {
            setError("Google login failed. Please try again.");
            return;
          }

          setError("");
          setSuccessMessage("");
          setLoading(true);
          try {
            const res = await fetch(`${BASE_URL}/user/google-login`, {
              method: "POST",
              headers: {
                "Content-Type": "application/json",
              },
              body: JSON.stringify({ credential: response.credential }),
            });

            const data = await res.json();
            if (!res.ok) {
              setError(typeof data?.detail === "string" ? data.detail : "Google login failed.");
              return;
            }

            localStorage.setItem("token", data.access_token);
            localStorage.setItem("role", data.user?.role || "user");
            localStorage.setItem("user", JSON.stringify(data.user || {}));
            setToken(data.access_token);
            navigate("/dashboard");
          } catch (err) {
            console.error(err);
            setError("Server error during Google login.");
          } finally {
            setLoading(false);
          }
        },
      });

      googleButtonRef.current.innerHTML = "";
      window.google.accounts.id.renderButton(googleButtonRef.current, {
        theme: theme === "dark" ? "filled_black" : "outline",
        size: "large",
        text: "signin_with",
        shape: "pill",
        width: 320,
      });
      setGoogleReady(true);
    };

    const existingScript = document.querySelector('script[src="https://accounts.google.com/gsi/client"]');
    if (existingScript) {
      initializeGoogle();
    } else {
      const script = document.createElement("script");
      script.src = "https://accounts.google.com/gsi/client";
      script.async = true;
      script.defer = true;
      script.onload = initializeGoogle;
      document.body.appendChild(script);
    }

    return () => {
      cancelled = true;
    };
  }, [GOOGLE_CLIENT_ID, authMode, loginRole, navigate, setToken, theme]);

  const toggleTheme = () => setTheme((p) => (p === "light" ? "dark" : "light"));

  const handleLogin = async (e) => {
    e.preventDefault();
    setError("");
    setSuccessMessage("");
    setLoading(true);

    try {
      let res;

      if (loginRole === "admin") {
        const formData = new URLSearchParams();
        formData.append("username", emailOrUsername);
        formData.append("password", password);
        formData.append("grant_type", "password");

        res = await fetch(`${BASE_URL}/login`, {
          method: "POST",
          headers: {
            "Content-Type": "application/x-www-form-urlencoded",
          },
          body: formData.toString(),
        });
      } else {
        res = await fetch(`${BASE_URL}/user/login`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            email: emailOrUsername,
            password,
          }),
        });
      }

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
      localStorage.setItem("role", data.role || data.user?.role || "user");
      localStorage.setItem("user", JSON.stringify(data.user || {}));
      setToken(data.access_token);

      // Redirect based on role
      if ((data.role || "").toLowerCase() === "admin") {
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

  const handleRegister = async (e) => {
    e.preventDefault();
    setError("");
    setSuccessMessage("");

    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setLoading(true);
    try {
      const res = await fetch(`${BASE_URL}/user/register`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          name,
          email: emailOrUsername,
          password,
        }),
      });

      const data = await res.json();
      if (!res.ok) {
        setError(typeof data?.detail === "string" ? data.detail : "Registration failed.");
        return;
      }

      localStorage.setItem("token", data.access_token);
      localStorage.setItem("role", data.user?.role || "user");
      localStorage.setItem("user", JSON.stringify(data.user || {}));
      setToken(data.access_token);
      setSuccessMessage("Account created successfully.");
      navigate("/dashboard");
    } catch (err) {
      console.error(err);
      setError("Server error. Try again.");
    } finally {
      setLoading(false);
    }
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
            onClick={() => { setLoginRole("user"); setError(""); setSuccessMessage(""); }}
          >
            <User size={16} /> User Login
          </button>
          <button
            className={`login-role-tab ${loginRole === "admin" ? "active" : ""}`}
            onClick={() => { setLoginRole("admin"); setError(""); setSuccessMessage(""); }}
          >
            <ShieldCheck size={16} /> Admin Login
          </button>
        </div>

        {loginRole === "user" && (
          <div className="login-auth-mode-tabs">
            <button
              className={`login-auth-mode-tab ${authMode === "login" ? "active" : ""}`}
              onClick={() => {
                setAuthMode("login");
                setError("");
                setSuccessMessage("");
              }}
              type="button"
            >
              <LogIn size={14} /> Sign In
            </button>
            <button
              className={`login-auth-mode-tab ${authMode === "register" ? "active" : ""}`}
              onClick={() => {
                setAuthMode("register");
                setError("");
                setSuccessMessage("");
              }}
              type="button"
            >
              <UserPlus size={14} /> Create Account
            </button>
          </div>
        )}

        <form onSubmit={loginRole === "user" && authMode === "register" ? handleRegister : handleLogin} className="login-form">
          {loginRole === "user" && authMode === "register" && (
            <div className="login-field">
              <label>Full Name</label>
              <input
                type="text"
                placeholder="Enter your full name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
              />
            </div>
          )}

          <div className="login-field">
            <label>{loginRole === "admin" ? "Username / Email" : "Email"}</label>
            <input
              type="text"
              placeholder={loginRole === "admin" ? "Enter your username or email" : "Enter your email"}
              value={emailOrUsername}
              onChange={(e) => setEmailOrUsername(e.target.value)}
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

          {loginRole === "user" && authMode === "register" && (
            <div className="login-field">
              <label>Confirm Password</label>
              <input
                type="password"
                placeholder="Confirm your password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
              />
            </div>
          )}

          <button type="submit" className="login-submit-btn" disabled={loading}>
            {loginRole === "user" && authMode === "register" ? <UserPlus size={18} /> : <LogIn size={18} />}
            {loading ? "Please wait..." : loginRole === "user" && authMode === "register" ? "Create Account" : "Sign In"}
          </button>
        </form>

        {loginRole === "user" && authMode === "login" && (
          <>
            <div className="login-google-divider">or continue with</div>
            <div className="login-google-wrap">
              {GOOGLE_CLIENT_ID ? <div ref={googleButtonRef} /> : <p>Google login not configured in frontend env.</p>}
              {!googleReady && GOOGLE_CLIENT_ID && <span className="login-google-loading">Loading Google sign-in...</span>}
            </div>
          </>
        )}

        {error && (
          <div className="login-error">
            <AlertCircle size={16} /> {error}
          </div>
        )}

        {successMessage && <div className="login-success">{successMessage}</div>}
      </div>
    </div>
  );
}

export default Login;