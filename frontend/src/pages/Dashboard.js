import React, { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import {
  LayoutDashboard, ShoppingBag, MessageSquare, LogOut,
  Package, Truck, CheckCircle, Clock, MapPin, Box,
  AlertCircle, Sun, Moon
} from "lucide-react";
import ChatWidget from "../components/ChatWidget";
import "./Dashboard.css";

const BASE_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";

function Dashboard({ setToken }) {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState("dashboard");
  const [chatOpen, setChatOpen] = useState(false);
  const [orders, setOrders] = useState([]);
  const [userName, setUserName] = useState("User");
  const [theme, setTheme] = useState(() => localStorage.getItem("theme") || "light");

  const token = localStorage.getItem("token");

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("theme", theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme((prev) => (prev === "light" ? "dark" : "light"));
  };

  const logout = useCallback(() => {
    localStorage.removeItem("token");
    localStorage.removeItem("role");
    setToken(null);
    navigate("/");
  }, [navigate, setToken]);

  const fetchUser = useCallback(async () => {
    try {
      const res = await fetch(`${BASE_URL}/user/profile`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setUserName(data.name || data.email || "User");
      }
    } catch (err) {
      console.error(err);
    }
  }, [token]);

  const fetchOrders = useCallback(async () => {
    try {
      const res = await fetch(`${BASE_URL}/user/orders`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setOrders(data);
      }
    } catch (err) {
      console.error(err);
    }
  }, [token]);

  useEffect(() => {
    if (!token) {
      navigate("/login");
      return;
    }
    fetchUser();
    fetchOrders();
  }, [token, navigate, fetchUser, fetchOrders]);

  const getStatusIcon = (status) => {
    switch (status) {
      case "Delivered": return <CheckCircle size={16} className="text-green" />;
      case "Shipped":
      case "Out for Delivery": return <Truck size={16} className="text-blue" />;
      case "Cancelled": return <AlertCircle size={16} className="text-red" />;
      default: return <Clock size={16} className="text-yellow" />;
    }
  };

  const getStatusClass = (status) => {
    switch (status) {
      case "Delivered": return "order-status-delivered";
      case "Shipped":
      case "Out for Delivery": return "order-status-shipped";
      case "Cancelled": return "order-status-cancelled";
      default: return "order-status-processing";
    }
  };

  return (
    <div className="user-dashboard-layout">

      {/* ── Sidebar ── */}
      <aside className="user-sidebar">
        <div className="user-sidebar-brand">
          <Box size={24} />
          <span>LogiAI</span>
        </div>

        <nav className="user-sidebar-nav">
          <button
            className={`user-sidebar-link ${activeTab === "dashboard" ? "active" : ""}`}
            onClick={() => setActiveTab("dashboard")}
          >
            <LayoutDashboard size={18} /> Dashboard
          </button>
          <button
            className={`user-sidebar-link ${activeTab === "orders" ? "active" : ""}`}
            onClick={() => setActiveTab("orders")}
          >
            <ShoppingBag size={18} /> My Orders
          </button>
          <button
            className={`user-sidebar-link ${chatOpen ? "active" : ""}`}
            onClick={() => setChatOpen((p) => !p)}
          >
            <MessageSquare size={18} /> AI Support Chat
          </button>
        </nav>

        <div className="user-sidebar-footer">
          <button className="user-sidebar-link" onClick={toggleTheme}>
            {theme === "light" ? <Moon size={18} /> : <Sun size={18} />}
            {theme === "light" ? "Dark Mode" : "Light Mode"}
          </button>
          <button className="user-sidebar-link logout" onClick={logout}>
            <LogOut size={18} /> Logout
          </button>
        </div>
      </aside>

      {/* ── Main Content ── */}
      <main className="user-main">

        {/* ─── Dashboard Tab ─── */}
        {activeTab === "dashboard" && (
          <div className="user-content">
            <div className="user-welcome">
              <h1>Welcome, {userName}!</h1>
              <p>Here's an overview of your orders and support activity.</p>
            </div>

            <div className="user-stats-grid">
              <div className="user-stat-card">
                <Package size={24} className="text-blue" />
                <div>
                  <h3>{orders.length}</h3>
                  <p>Total Orders</p>
                </div>
              </div>
              <div className="user-stat-card">
                <Truck size={24} className="text-yellow" />
                <div>
                  <h3>{orders.filter(o => ["Processing", "Shipped", "Out for Delivery"].includes(o.status)).length}</h3>
                  <p>Active Shipments</p>
                </div>
              </div>
              <div className="user-stat-card">
                <CheckCircle size={24} className="text-green" />
                <div>
                  <h3>{orders.filter(o => o.status === "Delivered").length}</h3>
                  <p>Delivered</p>
                </div>
              </div>
            </div>

            <div className="user-recent-orders">
              <h2>Recent Orders</h2>
              {orders.length === 0 ? (
                <div className="user-empty">
                  <ShoppingBag size={40} />
                  <p>No orders yet.</p>
                </div>
              ) : (
                <div className="user-orders-list">
                  {orders.slice(0, 5).map((order) => (
                    <div className="user-order-row" key={order.order_id}>
                      <div className="user-order-info">
                        <strong>{order.order_id}</strong>
                        <span className="user-order-product">{order.product_name}</span>
                      </div>
                      <div className="user-order-meta">
                        <span className={`user-order-badge ${getStatusClass(order.status)}`}>
                          {getStatusIcon(order.status)} {order.status}
                        </span>
                        <span className="user-order-price">₹{(order.price || 0).toLocaleString()}</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* ─── My Orders Tab ─── */}
        {activeTab === "orders" && (
          <div className="user-content">
            <h1>My Orders</h1>
            {orders.length === 0 ? (
              <div className="user-empty">
                <ShoppingBag size={48} />
                <p>No orders found.</p>
              </div>
            ) : (
              <div className="user-orders-grid">
                {orders.map((order) => (
                  <div className="user-order-card" key={order.order_id}>
                    <div className="user-order-card-top">
                      <div>
                        <h3>{order.order_id}</h3>
                        <p>{order.product_name}</p>
                      </div>
                      <span className={`user-order-badge ${getStatusClass(order.status)}`}>
                        {getStatusIcon(order.status)} {order.status}
                      </span>
                    </div>
                    <div className="user-order-card-details">
                      <div className="user-order-detail">
                        <MapPin size={14} />
                        <span>{order.destination || "N/A"}</span>
                      </div>
                      <div className="user-order-detail">
                        <Clock size={14} />
                        <span>Expected: {order.expected_delivery || "N/A"}</span>
                      </div>
                      <div className="user-order-detail">
                        <Package size={14} />
                        <span>₹{(order.price || 0).toLocaleString()}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

      </main>

      {/* ── Floating Chat Widget ── */}
      <ChatWidget externalOpen={chatOpen} onClose={() => setChatOpen(false)} />
    </div>
  );
}

export default Dashboard;
