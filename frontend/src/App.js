import React, { useState, useEffect } from "react";
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from "react-router-dom";

import Admin from "./Admin";
import LandingPage from "./pages/LandingPage";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import ChatWidget from "./components/ChatWidget";
import "./App.css";

/* ===========================
   PROTECTED ROUTE WRAPPERS
=========================== */

const PrivateRoute = ({ children }) => {
  const token = localStorage.getItem("token");
  return token ? children : <Navigate to="/login" replace />;
};

const AdminRoute = ({ children }) => {
  const token = localStorage.getItem("token");
  const role = localStorage.getItem("role");
  if (!token) return <Navigate to="/login" replace />;
  if (role !== "admin") return <Navigate to="/dashboard" replace />;
  return children;
};

/* ===========================
   Floating Chat Widget Wrapper
   (shows on public pages only — Landing & Login)
=========================== */
const FloatingChat = () => {
  const { pathname } = useLocation();
  // Dashboard has its own ChatWidget via sidebar; Admin doesn't need it
  if (pathname === "/dashboard" || pathname === "/admin") return null;
  return <ChatWidget />;
};

/* ===========================
   MAIN APP
=========================== */

function App() {
  // eslint-disable-next-line no-unused-vars
  const [token, setToken] = useState(localStorage.getItem("token"));

  useEffect(() => {
    const storedToken = localStorage.getItem("token");
    setToken(storedToken);
  }, []);

  return (
    <Router>
      <FloatingChat />
      <Routes>
        {/* Public */}
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<Login setToken={setToken} />} />

        {/* User Dashboard (protected) */}
        <Route
          path="/dashboard"
          element={
            <PrivateRoute>
              <Dashboard setToken={setToken} />
            </PrivateRoute>
          }
        />

        {/* Admin Dashboard (protected + role check) */}
        <Route
          path="/admin"
          element={
            <AdminRoute>
              <Admin setToken={setToken} />
            </AdminRoute>
          }
        />
      </Routes>
    </Router>
  );
}

export default App;