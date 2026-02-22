import React from "react";
import { BrowserRouter as Router, Routes, Route, Link, Navigate } from "react-router-dom";
import Admin from "./Admin";
import UserPage from "./Userpage";
import Login from "./pages/Login";
import "./App.css";

/* -------------------------
   Private Route Component
-------------------------- */
const PrivateRoute = ({ children }) => {
  const token = localStorage.getItem("token");
  return token ? children : <Navigate to="/login" />;
};

function App() {
  const token = localStorage.getItem("token");

  return (
    <Router>
      <div>

        {/* NAVBAR */}
        <nav className="navbar">
          <div className="nav-left">
            <h2>LogiAI</h2>
          </div>

          <div className="nav-right">
            <Link to="/">User</Link>

            {token ? (
              <>
                <Link to="/admin">Admin</Link>
                <button
                  className="logout-btn"
                  onClick={() => {
                    localStorage.removeItem("token");
                    window.location.href = "/login";
                  }}
                >
                  Logout
                </button>
              </>
            ) : (
              <Link to="/login">Admin Login</Link>
            )}
          </div>
        </nav>

        {/* ROUTES */}
        <Routes>
          <Route path="/" element={<UserPage />} />
          <Route path="/login" element={<Login />} />

          <Route
            path="/admin"
            element={
              <PrivateRoute>
                <Admin />
              </PrivateRoute>
            }
          />
        </Routes>
      </div>
    </Router>
  );
}

export default App;