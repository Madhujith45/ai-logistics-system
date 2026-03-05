import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
  Truck, Package, Headphones, MapPin, Search,
  ArrowRight, Shield, Zap, Globe, CheckCircle,
  Clock, AlertCircle, ChevronRight, Box, Sun, Moon,
  ShieldCheck, User
} from "lucide-react";

const BASE_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";

function LandingPage() {
  const navigate = useNavigate();
  const [trackInput, setTrackInput] = useState("");
  const [trackResult, setTrackResult] = useState(null);
  const [trackError, setTrackError] = useState("");
  const [trackLoading, setTrackLoading] = useState(false);
  const [theme, setTheme] = useState(() => localStorage.getItem("theme") || "light");

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("theme", theme);
  }, [theme]);

  const toggleTheme = () => setTheme((p) => (p === "light" ? "dark" : "light"));

  const handleTrack = async () => {
    if (!trackInput.trim()) {
      setTrackError("Please enter an Order ID");
      return;
    }
    setTrackError("");
    setTrackResult(null);
    setTrackLoading(true);

    try {
      const res = await fetch(`${BASE_URL}/track/${trackInput.trim()}`);
      if (!res.ok) {
        setTrackError("Order not found. Please check the ID and try again.");
        setTrackLoading(false);
        return;
      }
      const data = await res.json();
      setTrackResult(data);
    } catch (err) {
      setTrackError("Unable to connect to server. Please try again.");
    }
    setTrackLoading(false);
  };

  const getStatusStep = (status) => {
    const steps = ["Placed", "Processing", "Shipped", "Out for Delivery", "Delivered"];
    if (status === "Cancelled") return -1;
    return steps.indexOf(status);
  };

  const ORDER_STEPS = ["Placed", "Processing", "Shipped", "Out for Delivery", "Delivered"];

  return (
    <div className="landing-page">

      {/* ── Navbar ── */}
      <nav className="landing-nav">
        <div className="landing-nav-inner">
          <div className="landing-logo">
            <Box size={28} />
            <span>LogiAI</span>
          </div>
          <div className="landing-nav-links">
            <a href="#services">Services</a>
            <a href="#solutions">Solutions</a>
            <a href="#track">Track</a>
            <a href="#support">Support</a>
            <button className="theme-toggle-btn" onClick={toggleTheme} title="Toggle theme">
              {theme === "light" ? <Moon size={16} /> : <Sun size={16} />}
            </button>
            <button className="landing-login-btn landing-login-user" onClick={() => navigate("/login?role=user")}>
              <User size={16} /> User Login
            </button>
            <button className="landing-login-btn landing-login-admin" onClick={() => navigate("/login?role=admin")}>
              <ShieldCheck size={16} /> Admin Login
            </button>
          </div>
        </div>
      </nav>

      {/* ── Hero Section ── */}
      <section className="landing-hero">
        <div className="hero-overlay"></div>
        <div className="hero-content">
          <div className="hero-badge">
            <Zap size={14} /> AI-Powered Platform
          </div>
          <h1>AI-Powered Logistics<br />Support System</h1>
          <p>
            Intelligent order tracking, automated customer support, and real-time
            shipment visibility — all powered by advanced NLP technology.
          </p>
          <div className="hero-buttons">
            <a href="#track" className="hero-btn-primary">
              <Search size={18} /> Track Your Order
            </a>
            <button className="hero-btn-secondary" onClick={() => navigate("/login?role=user")}>
              Get Started <ArrowRight size={18} />
            </button>
          </div>
          <div className="hero-stats">
            <div className="hero-stat">
              <h3>15K+</h3>
              <p>Orders Tracked</p>
            </div>
            <div className="hero-stat">
              <h3>91.5%</h3>
              <p>AI Accuracy</p>
            </div>
            <div className="hero-stat">
              <h3>24/7</h3>
              <p>AI Support</p>
            </div>
          </div>
        </div>
      </section>

      {/* ── Track Order Section ── */}
      <section className="landing-track" id="track">
        <div className="track-section-inner">
          <h2>Track Your Shipment</h2>
          <p className="track-subtitle">Enter your order details to get real-time tracking updates</p>

          <div className="track-card">
            <div className="track-input-row">
              <div className="track-input-wrapper">
                <Search size={18} className="track-input-icon" />
                <input
                  type="text"
                  placeholder="Enter Order ID (e.g. ORD-1001)"
                  value={trackInput}
                  onChange={(e) => setTrackInput(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleTrack()}
                  className="track-input"
                />
              </div>
              <button className="track-btn" onClick={handleTrack} disabled={trackLoading}>
                {trackLoading ? "Tracking..." : "Track Order"}
                {!trackLoading && <ArrowRight size={16} />}
              </button>
            </div>

            {trackError && (
              <div className="track-error">
                <AlertCircle size={16} /> {trackError}
              </div>
            )}

            {/* Track Result */}
            {trackResult && (
              <div className="track-result">
                <div className="track-result-header">
                  <div>
                    <h3>{trackResult.order_id}</h3>
                    <span className="track-product">{trackResult.product_name}</span>
                  </div>
                  <span className={`track-status-badge status-${trackResult.status?.toLowerCase().replace(/ /g, "-")}`}>
                    {trackResult.status}
                  </span>
                </div>

                {/* Stepper */}
                {trackResult.status !== "Cancelled" && (
                  <div className="track-stepper">
                    {ORDER_STEPS.map((step, i) => {
                      const currentStep = getStatusStep(trackResult.status);
                      const completed = i <= currentStep;
                      const isCurrent = i === currentStep;
                      return (
                        <React.Fragment key={step}>
                          <div className={`track-step ${completed ? "step-done" : ""} ${isCurrent ? "step-active" : ""}`}>
                            <div className="track-step-circle">
                              {completed ? <CheckCircle size={20} /> : <span>{i + 1}</span>}
                            </div>
                            <span className="track-step-label">{step}</span>
                          </div>
                          {i < ORDER_STEPS.length - 1 && (
                            <div className={`track-step-line ${i < currentStep ? "line-done" : ""}`} />
                          )}
                        </React.Fragment>
                      );
                    })}
                  </div>
                )}

                {trackResult.status === "Cancelled" && (
                  <div className="track-cancelled">
                    <AlertCircle size={18} /> This order has been cancelled.
                  </div>
                )}

                <div className="track-details-grid">
                  <div className="track-detail-item">
                    <MapPin size={14} />
                    <div>
                      <span className="track-detail-label">Route</span>
                      <span className="track-detail-value">
                        {trackResult.origin || "Warehouse"} → {trackResult.destination || "N/A"}
                      </span>
                    </div>
                  </div>
                  <div className="track-detail-item">
                    <Clock size={14} />
                    <div>
                      <span className="track-detail-label">Expected Delivery</span>
                      <span className="track-detail-value">{trackResult.expected_delivery || "N/A"}</span>
                    </div>
                  </div>
                  {trackResult.delivery_date && (
                    <div className="track-detail-item">
                      <CheckCircle size={14} />
                      <div>
                        <span className="track-detail-label">Delivered On</span>
                        <span className="track-detail-value">{trackResult.delivery_date}</span>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </section>

      {/* ── Services Section ── */}
      <section className="landing-services" id="services">
        <div className="services-inner">
          <h2>Our Services</h2>
          <p className="services-subtitle">Comprehensive logistics solutions powered by AI</p>
          <div className="services-grid">
            <div className="service-card">
              <div className="service-icon">
                <Truck size={28} />
              </div>
              <h3>Real-Time Tracking</h3>
              <p>Track your shipments in real-time with AI-powered status updates and delivery predictions.</p>
            </div>
            <div className="service-card">
              <div className="service-icon">
                <Headphones size={28} />
              </div>
              <h3>AI Support</h3>
              <p>Get instant answers to your queries with our NLP-powered chatbot available 24/7.</p>
            </div>
            <div className="service-card">
              <div className="service-icon">
                <Shield size={28} />
              </div>
              <h3>Smart Escalation</h3>
              <p>Complex issues are automatically escalated to human agents with full context preserved.</p>
            </div>
            <div className="service-card">
              <div className="service-icon">
                <Globe size={28} />
              </div>
              <h3>Pan-India Coverage</h3>
              <p>Delivering across India with strategically located warehouses and fulfillment centers.</p>
            </div>
          </div>
        </div>
      </section>

      {/* ── Solutions / How It Works ── */}
      <section className="landing-solutions" id="solutions">
        <div className="solutions-inner">
          <h2>How It Works</h2>
          <p className="solutions-subtitle">Simple, fast, and intelligent logistics support</p>
          <div className="solutions-steps">
            <div className="solution-step">
              <div className="step-number">1</div>
              <h3>Enter Order ID</h3>
              <p>Type your order ID in the tracking widget to get instant updates.</p>
            </div>
            <div className="solution-connector"><ChevronRight size={24} /></div>
            <div className="solution-step">
              <div className="step-number">2</div>
              <h3>AI Analyzes Query</h3>
              <p>Our NLP model understands your intent and fetches relevant order data.</p>
            </div>
            <div className="solution-connector"><ChevronRight size={24} /></div>
            <div className="solution-step">
              <div className="step-number">3</div>
              <h3>Get Instant Resolution</h3>
              <p>Receive accurate status updates, cancel orders, or request refunds instantly.</p>
            </div>
          </div>
        </div>
      </section>

      {/* ── Support CTA ── */}
      <section className="landing-support" id="support">
        <div className="support-inner">
          <Package size={48} />
          <h2>Need Help With Your Order?</h2>
          <p>Our AI-powered support system is ready to help you with tracking, cancellations, refunds, and more.</p>
          <button className="support-login-btn" onClick={() => navigate("/login?role=user")}>
            Login for AI Support <ArrowRight size={18} />
          </button>
        </div>
      </section>

      {/* ── Footer ── */}
      <footer className="landing-footer">
        <div className="footer-inner">
          <div className="footer-brand">
            <Box size={22} />
            <span>LogiAI</span>
          </div>
          <p>&copy; 2026 LogiAI. Built for academic purposes.</p>
        </div>
      </footer>

    </div>
  );
}

export default LandingPage;
