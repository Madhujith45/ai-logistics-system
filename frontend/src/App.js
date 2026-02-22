import React, { useState, useEffect } from "react";
import { 
  BrowserRouter as Router, 
  Routes, 
  Route, 
  Link, 
  Navigate, 
  useNavigate 
} from "react-router-dom";

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
        <Link to="/">User</Link>

        {token ? (
          <>
            <Link to="/admin">Admin</Link>
            <button className="logout-btn" onClick={handleLogout}>
              Logout
            </button>
          </>
        ) : (
          <Link to="/login">Admin Login</Link>
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