import React, { useState, useRef, useEffect, useCallback } from "react";
import {
  Send,
  PackageSearch,
  AlertCircle,
  CheckCircle,
  Bot,
  User,
  Truck,
  RotateCcw,
  XCircle,
  ShieldAlert,
  MessageSquare,
  CreditCard,
  Gift,
  LogIn,
  LogOut,
  UserPlus,
  ShoppingBag,
  Clock,
} from "lucide-react";
import "./App.css";

const BASE_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";

/* ===========================
   SESSION ID GENERATOR
=========================== */
const generateSessionId = () => {
  return "sess_" + Date.now() + "_" + Math.random().toString(36).substring(2, 11);
};

/* ===========================
   WELCOME MESSAGE
=========================== */
const WELCOME_MESSAGE = {
  sender: "bot",
  type: "welcome",
  text:
    "Welcome to LogiAI Customer Support! I'm your virtual assistant and I'm here to help you with:\n\n" +
    "• Track your orders\n" +
    "• Cancel or modify orders\n" +
    "• Request refunds\n" +
    "• Report damaged or wrong products\n\n" +
    "Type your query below or use the quick action buttons to get started.",
  timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
};

/* ===========================
   TYPING INDICATOR COMPONENT
=========================== */
const TypingIndicator = () => (
  <div className="chat-bubble bot-bubble typing-bubble">
    <div className="bubble-avatar bot-avatar">
      <Bot size={18} />
    </div>
    <div className="bubble-content">
      <div className="typing-dots">
        <span></span>
        <span></span>
        <span></span>
      </div>
      <p className="typing-label">Bot is typing...</p>
    </div>
  </div>
);

/* ===========================
   INTENT-SPECIFIC RESPONSE UI
=========================== */
const IntentResponseUI = ({ intent, response }) => {
  if (!intent) return null;

  const normalizedIntent = intent.toUpperCase();

  if (normalizedIntent === "REFUND_REQUEST") {
    return (
      <div className="intent-action-card refund-card">
        <div className="intent-action-header">
          <CreditCard size={18} />
          <span>Refund Options</span>
        </div>
        <div className="intent-action-buttons">
          <button className="intent-btn refund-btn">
            <CreditCard size={14} /> Refund to Original Payment
          </button>
          <button className="intent-btn credit-btn">
            <Gift size={14} /> Instant Store Credit (+5% Bonus)
          </button>
        </div>
      </div>
    );
  }

  if (normalizedIntent === "CANCEL_ORDER") {
    return (
      <div className="intent-action-card cancel-card">
        <div className="intent-action-header">
          <XCircle size={18} />
          <span>Cancellation Status</span>
        </div>
        <p className="intent-action-info">
          {response.status === "AUTO_RESOLVED"
            ? "Your cancellation has been processed successfully."
            : "Your cancellation request is under review by our support team."}
        </p>
      </div>
    );
  }

  if (normalizedIntent === "DAMAGED_PRODUCT") {
    return (
      <div className="intent-action-card damage-card">
        <div className="intent-action-header">
          <ShieldAlert size={18} />
          <span>Damage Claim</span>
        </div>
        <p className="intent-action-info">
          Please upload images of the damaged product via the support portal within 48 hours to expedite your claim.
        </p>
      </div>
    );
  }

  if (normalizedIntent === "MISMATCH_PRODUCT") {
    return (
      <div className="intent-action-card mismatch-card">
        <div className="intent-action-header">
          <RotateCcw size={18} />
          <span>Replacement Process</span>
        </div>
        <p className="intent-action-info">
          A replacement has been initiated. Please upload photos of the incorrect item received within 48 hours. The correct product will be shipped at no extra cost.
        </p>
      </div>
    );
  }

  return null;
};

/* ===========================
   CHAT BUBBLE COMPONENT
=========================== */
const ChatBubble = ({ msg }) => {
  const isBot = msg.sender === "bot";

  return (
    <div className={`chat-bubble ${isBot ? "bot-bubble" : "user-bubble"}`}>
      <div className={`bubble-avatar ${isBot ? "bot-avatar" : "user-avatar"}`}>
        {isBot ? <Bot size={18} /> : <User size={18} />}
      </div>
      <div className="bubble-content">
        <div className={`bubble-message ${isBot ? "bot-msg" : "user-msg"}`}>
          {msg.text.split("\n").map((line, i) => (
            <React.Fragment key={i}>
              {line}
              {i < msg.text.split("\n").length - 1 && <br />}
            </React.Fragment>
          ))}
        </div>

        {/* User-friendly response metadata — NO internal intent/confidence shown */}
        {isBot && msg.response && (
          <div className="bubble-meta">
            <div className="meta-row">
              <span className="meta-label">Reference</span>
              <span className="meta-value">#{msg.response.ticket_id}</span>
            </div>
            <div className="meta-row">
              <span className="meta-label">Status</span>
              <span
                className={`status-badge-chat ${
                  msg.response.status === "AUTO_RESOLVED"
                    ? "status-resolved"
                    : "status-escalated"
                }`}
              >
                {msg.response.status === "AUTO_RESOLVED" ? (
                  <><CheckCircle size={12} /> Resolved</>
                ) : (
                  <><Clock size={12} /> Under Review</>
                )}
              </span>
            </div>
          </div>
        )}

        {/* Intent-specific UI */}
        {isBot && msg.response && (
          <IntentResponseUI
            intent={msg.response.intent}
            response={msg.response}
          />
        )}

        <span className="bubble-time">{msg.timestamp}</span>
      </div>
    </div>
  );
};

/* ===========================
   MAIN USER PAGE COMPONENT
=========================== */
function UserPage() {
  const [text, setText] = useState("");
  const [orderId, setOrderId] = useState("");
  const [messages, setMessages] = useState([WELCOME_MESSAGE]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  // Keep original state variables for backward compatibility
  const [response, setResponse] = useState(null);

  // --- New: Session & User Auth State ---
  const [sessionId] = useState(() => generateSessionId());
  const [userToken, setUserToken] = useState(
    localStorage.getItem("user_token") || localStorage.getItem("token")
  );
  const [userProfile, setUserProfile] = useState(null);
  const [showAuthPanel, setShowAuthPanel] = useState(false);
  const [authMode, setAuthMode] = useState("login"); // "login" | "register"
  const [authForm, setAuthForm] = useState({ name: "", email: "", password: "" });
  const [authError, setAuthError] = useState("");
  const [authLoading, setAuthLoading] = useState(false);
  const [userOrders, setUserOrders] = useState([]);
  const [showOrders, setShowOrders] = useState(false);

  const chatEndRef = useRef(null);
  const inputRef = useRef(null);

  // Auto-scroll to bottom
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  // Load user profile if token exists
  const fetchProfile = useCallback(async (token) => {
    try {
      const res = await fetch(`${BASE_URL}/user/profile`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setUserProfile(data);
      } else {
        // Token invalid — clear user_token only (keep main token intact)
        localStorage.removeItem("user_token");
        // Try main app token as fallback
        const mainToken = localStorage.getItem("token");
        if (mainToken && token !== mainToken) {
          fetchProfile(mainToken);
          setUserToken(mainToken);
        } else {
          setUserToken(null);
          setUserProfile(null);
        }
      }
    } catch {
      // silently fail
    }
  }, []);

  useEffect(() => {
    if (userToken) {
      fetchProfile(userToken);
    }
  }, [userToken, fetchProfile]);

  // Load user orders
  const fetchOrders = async () => {
    if (!userToken) return;
    try {
      const res = await fetch(`${BASE_URL}/user/orders`, {
        headers: { Authorization: `Bearer ${userToken}` },
      });
      if (res.ok) {
        const data = await res.json();
        setUserOrders(Array.isArray(data) ? data : data.orders || []);
        setShowOrders(true);
      }
    } catch {
      // silently fail
    }
  };

  const getTimestamp = () =>
    new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

  // --- Auth Handlers ---
  const handleAuth = async (e) => {
    e.preventDefault();
    setAuthError("");
    setAuthLoading(true);
    try {
      const endpoint = authMode === "register" ? "/user/register" : "/user/login";
      const body =
        authMode === "register"
          ? { name: authForm.name, email: authForm.email, password: authForm.password }
          : { email: authForm.email, password: authForm.password };

      const res = await fetch(`${BASE_URL}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const data = await res.json();
      if (!res.ok) {
        setAuthError(data.detail || "Authentication failed");
        setAuthLoading(false);
        return;
      }

      // Both register and login return a token
      const token = data.access_token || data.token;
      if (token) {
        localStorage.setItem("user_token", token);
        setUserToken(token);
        setShowAuthPanel(false);
        setAuthForm({ name: "", email: "", password: "" });

        // Add welcome-back message
        const userName = data.name || (data.user && data.user.name) || "";
        const welcomeMsg = {
          sender: "bot",
          text: `Welcome${authMode === "register" ? "" : " back"}, ${userName}! You're now signed in. Your conversations and order history are linked to your account.`,
          timestamp: getTimestamp(),
        };
        setMessages((prev) => [...prev, welcomeMsg]);
      }
    } catch {
      setAuthError("Connection error. Please try again.");
    }
    setAuthLoading(false);
  };

  const handleLogout = () => {
    localStorage.removeItem("user_token");
    setUserToken(null);
    setUserProfile(null);
    setShowOrders(false);
    setUserOrders([]);
    const logoutMsg = {
      sender: "bot",
      text: "You've been signed out. You can continue as a guest or sign in again anytime.",
      timestamp: getTimestamp(),
    };
    setMessages((prev) => [...prev, logoutMsg]);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!text.trim()) {
      setError("Please enter your query.");
      return;
    }

    // Add user message to chat
    const userMsg = {
      sender: "user",
      text: text + (orderId ? ` (Order: #${orderId})` : ""),
      timestamp: getTimestamp(),
    };
    setMessages((prev) => [...prev, userMsg]);

    setLoading(true);
    setError("");
    setResponse(null);

    try {
      // Build request payload with session and user context
      const payload = {
        text: text,
        order_id: orderId,
        session_id: sessionId,
      };

      // Add user_id if logged in
      if (userProfile && userProfile.id) {
        payload.user_id = userProfile.id;
      }

      const headers = { "Content-Type": "application/json" };
      if (userToken) {
        headers["Authorization"] = `Bearer ${userToken}`;
      }

      const res = await fetch(`${BASE_URL}/chat`, {
        method: "POST",
        headers,
        body: JSON.stringify(payload),
      });

      const data = await res.json();
      setResponse(data);

      // Add bot response to chat
      const botMsg = {
        sender: "bot",
        text: data.message,
        response: data,
        timestamp: getTimestamp(),
      };
      setMessages((prev) => [...prev, botMsg]);
    } catch (err) {
      console.error(err);
      setError("Server error. Please try again.");
      const errorMsg = {
        sender: "bot",
        text: "We're experiencing a temporary issue connecting to our servers. Please try again in a moment.",
        timestamp: getTimestamp(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    }

    setLoading(false);
    setText("");
    inputRef.current?.focus();
  };

  const handleQuickAction = (query) => {
    setText(query);
    inputRef.current?.focus();
  };

  return (
    <div className="chat-container">
      {/* Chat Header */}
      <div className="chat-header">
        <div className="chat-header-left">
          <div className="chat-header-icon">
            <PackageSearch size={24} />
          </div>
          <div>
            <h2>LogiAI Support</h2>
            <span className="chat-header-status">
              <span className="status-dot"></span> Online
            </span>
          </div>
        </div>
        <div className="chat-header-right">
          {userProfile ? (
            <div className="user-header-info">
              <span className="user-greeting">Hi, {userProfile.name}</span>
              <button
                className="header-icon-btn"
                onClick={fetchOrders}
                title="My Orders"
              >
                <ShoppingBag size={18} />
              </button>
              <button
                className="header-icon-btn"
                onClick={handleLogout}
                title="Sign Out"
              >
                <LogOut size={18} />
              </button>
            </div>
          ) : (
            <button
              className="header-icon-btn sign-in-btn"
              onClick={() => setShowAuthPanel(!showAuthPanel)}
              title="Sign In"
            >
              <LogIn size={18} />
              <span>Sign In</span>
            </button>
          )}
        </div>
      </div>

      {/* Auth Panel — Card Style */}
      {showAuthPanel && !userProfile && (
        <div className="auth-overlay" onClick={() => setShowAuthPanel(false)}>
          <div className="auth-card" onClick={(e) => e.stopPropagation()}>
            <div style={{ textAlign: "center", marginBottom: 8 }}>
              <div className="auth-card-icon">
                {authMode === "register" ? <UserPlus size={28} /> : <LogIn size={28} />}
              </div>
            </div>
            <h2 className="auth-card-title">{authMode === "register" ? "Create Account" : "Sign In"}</h2>
            <p className="auth-card-subtitle">
              {authMode === "register"
                ? "Register to track orders and get personalized support"
                : "Sign in to access your orders and support history"}
            </p>

            <div className="auth-tabs">
              <button
                className={`auth-tab ${authMode === "login" ? "active" : ""}`}
                onClick={() => { setAuthMode("login"); setAuthError(""); }}
              >
                Sign In
              </button>
              <button
                className={`auth-tab ${authMode === "register" ? "active" : ""}`}
                onClick={() => { setAuthMode("register"); setAuthError(""); }}
              >
                Register
              </button>
            </div>

            <form className="auth-form" onSubmit={handleAuth}>
              {authMode === "register" && (
                <input
                  type="text"
                  placeholder="Full Name"
                  value={authForm.name}
                  onChange={(e) => setAuthForm({ ...authForm, name: e.target.value })}
                  required
                />
              )}
              <input
                type="email"
                placeholder="Email Address"
                value={authForm.email}
                onChange={(e) => setAuthForm({ ...authForm, email: e.target.value })}
                required
              />
              <input
                type="password"
                placeholder="Password"
                value={authForm.password}
                onChange={(e) => setAuthForm({ ...authForm, password: e.target.value })}
                required
              />
              {authError && <p className="auth-error">{authError}</p>}
              <button type="submit" className="auth-submit-btn" disabled={authLoading}>
                {authLoading
                  ? "Please wait..."
                  : authMode === "register"
                  ? "Create Account"
                  : "Sign In"}
              </button>
            </form>
            <button className="auth-close-btn" onClick={() => setShowAuthPanel(false)}>
              Skip — Continue as Guest
            </button>
          </div>
        </div>
      )}

      {/* Orders Panel */}
      {showOrders && userOrders.length > 0 && (
        <div className="orders-panel">
          <div className="orders-panel-header">
            <h3><ShoppingBag size={16} /> My Orders</h3>
            <button className="orders-close-btn" onClick={() => setShowOrders(false)}>
              <XCircle size={16} />
            </button>
          </div>
          <div className="orders-list">
            {userOrders.map((order) => (
              <div
                key={order.order_id}
                className="order-card-mini"
                onClick={() => {
                  setOrderId(String(order.order_id));
                  setShowOrders(false);
                  inputRef.current?.focus();
                }}
              >
                <div className="order-card-top">
                  <span className="order-id-mini">#{order.order_id}</span>
                  <span className={`order-status-mini status-${(order.order_status || "").toLowerCase().replace(/ /g, "-")}`}>
                    {order.order_status}
                  </span>
                </div>
                <p className="order-product-mini">{order.product_name}</p>
                <p className="order-price-mini">₹{order.price?.toLocaleString()}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Chat Messages Area */}
      <div className="chat-messages">
        {messages.map((msg, index) => (
          <ChatBubble key={index} msg={msg} />
        ))}
        {loading && <TypingIndicator />}
        <div ref={chatEndRef} />
      </div>

      {/* Quick Actions */}
      <div className="chat-quick-actions">
        <button
          type="button"
          onClick={() => handleQuickAction("Track my order")}
          className="quick-action-btn"
        >
          <Truck size={14} /> Track Order
        </button>
        <button
          type="button"
          onClick={() => handleQuickAction("I want a refund")}
          className="quick-action-btn"
        >
          <RotateCcw size={14} /> Refund
        </button>
        <button
          type="button"
          onClick={() => handleQuickAction("Cancel my order")}
          className="quick-action-btn"
        >
          <XCircle size={14} /> Cancel
        </button>
        <button
          type="button"
          onClick={() => handleQuickAction("I received a damaged product")}
          className="quick-action-btn"
        >
          <ShieldAlert size={14} /> Report Damage
        </button>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="chat-error">
          <AlertCircle size={16} /> {error}
        </div>
      )}

      {/* Chat Input Area */}
      <form className="chat-input-area" onSubmit={handleSubmit}>
        <div className="chat-input-row">
          <input
            type="text"
            className="chat-order-input"
            placeholder="Order ID"
            value={orderId}
            onChange={(e) => setOrderId(e.target.value)}
          />
          <input
            ref={inputRef}
            type="text"
            className="chat-text-input"
            placeholder="Type your message..."
            value={text}
            onChange={(e) => setText(e.target.value)}
          />
          <button
            type="submit"
            className="chat-send-btn"
            disabled={loading}
          >
            <Send size={18} />
          </button>
        </div>
      </form>
    </div>
  );
}

export default UserPage;