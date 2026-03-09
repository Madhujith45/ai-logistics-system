import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
  Truck, Package, Headphones, MapPin, Search,
  ArrowRight, Shield, Globe, CheckCircle,
  Clock, AlertCircle, ChevronRight, Box, Sun, Moon,
  ShieldCheck, User, BrainCircuit, Database, Zap
} from "lucide-react";

const BASE_URL = process.env.REACT_APP_API_URL || "https://ai-logistics-system.onrender.com";

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

      {/* ── Hero Section (Two-Column) ── */}
      <section className="landing-hero">
        <div className="hero-inner">
          <div className="hero-left">
            <div className="hero-badge">
              <Package size={14} /> Logistics Platform
            </div>
            <h1>Smart Shipment Tracking &amp; Logistics Support Platform</h1>
            <p>
              Track shipments, manage delivery requests, and resolve logistics
              support queries instantly using our AI-assisted logistics platform.
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
                <Package size={18} className="hero-stat-icon" />
                <div>
                  <h3>15K+</h3>
                  <p>Shipments Processed</p>
                </div>
              </div>
              <div className="hero-stat">
                <Truck size={18} className="hero-stat-icon" />
                <div>
                  <h3>98%</h3>
                  <p>On-Time Delivery</p>
                </div>
              </div>
              <div className="hero-stat">
                <Headphones size={18} className="hero-stat-icon" />
                <div>
                  <h3>24/7</h3>
                  <p>Customer Support</p>
                </div>
              </div>
            </div>
          </div>
          <div className="hero-right">
            <div className="hero-image-card">
              <img
                src="https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?auto=format&fit=crop&w=800&q=80"
                alt="Logistics warehouse operations"
                className="hero-image"
              />
              <div className="hero-image-overlay-card">
                <div className="hero-overlay-stat">
                  <Truck size={20} />
                  <div>
                    <span className="overlay-stat-num">2,400+</span>
                    <span className="overlay-stat-label">Active Shipments</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── Track Order Section ── */}
      <section className="landing-track" id="track">
        <div className="track-section-inner">
          <div className="section-tag"><Package size={14} /> Tracking</div>
          <h2><Truck size={24} /> Track Your Shipment</h2>
          <p className="track-subtitle">Enter your order details to get real-time tracking updates</p>

          <div className="track-card">
            <div className="track-input-row">
              <div className="track-input-wrapper">
                <Package size={18} className="track-input-icon" />
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

      {/* ── Logistics Services Section ── */}
      <section className="landing-services" id="services">
        <div className="services-inner">
          <div className="services-header">
            <span className="section-tag"><Package size={14} /> Our Services</span>
            <h2>Logistics Services</h2>
            <p className="services-subtitle">End-to-end logistics solutions for modern supply chains</p>
          </div>
          <div className="services-grid">
            <div className="service-card">
              <div className="service-card-img">
                <img src="https://images.unsplash.com/photo-1553413077-190dd305871c?auto=format&fit=crop&w=600&q=80" alt="Shipment Tracking" />
              </div>
              <div className="service-card-body">
                <div className="service-icon"><Truck size={24} /></div>
                <h3>Real-Time Shipment Tracking</h3>
                <p>Monitor package progress from warehouse to delivery with live status updates and ETA predictions.</p>
              </div>
            </div>
            <div className="service-card">
              <div className="service-card-img">
                <img src="https://images.unsplash.com/photo-1556742049-0cfed4f6a45d?auto=format&fit=crop&w=600&q=80" alt="Customer Support" />
              </div>
              <div className="service-card-body">
                <div className="service-icon"><Headphones size={24} /></div>
                <h3>Customer Support Automation</h3>
                <p>Resolve shipment issues instantly using our AI-powered support assistant available 24/7.</p>
              </div>
            </div>
            <div className="service-card">
              <div className="service-card-img">
                <img src="https://images.unsplash.com/photo-1580674285054-bed31e145f59?auto=format&fit=crop&w=600&q=80" alt="Order Cancellation" />
              </div>
              <div className="service-card-body">
                <div className="service-icon"><Shield size={24} /></div>
                <h3>Policy-Based Order Cancellation</h3>
                <p>Process cancellations and refund requests according to verified logistics policies automatically.</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── How LogiAI Works (4-Step) ── */}
      <section className="landing-solutions" id="solutions">
        <div className="solutions-inner">
          <div className="section-tag"><Globe size={14} /> Workflow</div>
          <h2>How LogiAI Works</h2>
          <p className="solutions-subtitle">From query to resolution in seconds</p>
          <div className="solutions-steps">
            <div className="solution-step">
              <div className="step-icon-wrap"><Package size={26} /></div>
              <div className="step-number">1</div>
              <h3>Enter Order ID</h3>
              <p>Users enter their order number to track shipments or request logistics support.</p>
            </div>
            <div className="solution-connector"><ChevronRight size={22} /></div>
            <div className="solution-step">
              <div className="step-icon-wrap"><BrainCircuit size={26} /></div>
              <div className="step-number">2</div>
              <h3>AI Detects Request</h3>
              <p>The NLP engine analyzes the query and identifies intent such as tracking or cancellation.</p>
            </div>
            <div className="solution-connector"><ChevronRight size={22} /></div>
            <div className="solution-step">
              <div className="step-icon-wrap"><Database size={26} /></div>
              <div className="step-number">3</div>
              <h3>Retrieve Shipment Data</h3>
              <p>The backend queries the logistics database to fetch shipment status and order information.</p>
            </div>
            <div className="solution-connector"><ChevronRight size={22} /></div>
            <div className="solution-step">
              <div className="step-icon-wrap"><Truck size={26} /></div>
              <div className="step-number">4</div>
              <h3>Real-Time Updates</h3>
              <p>Shipment progress and delivery ETA are displayed instantly to the user.</p>
            </div>
          </div>
        </div>
      </section>

      {/* ── Credibility / Trust Metrics ── */}
      <section className="landing-credibility">
        <div className="credibility-inner">
          <h2>Trusted Logistics Support Platform</h2>
          <p>Reliable, AI-powered logistics support trusted by businesses</p>
          <div className="credibility-grid">
            <div className="credibility-card">
              <div className="credibility-icon"><Package size={22} /></div>
              <h3>15K+</h3>
              <p>Shipments Processed</p>
            </div>
            <div className="credibility-card">
              <div className="credibility-icon"><Truck size={22} /></div>
              <h3>98%</h3>
              <p>On-Time Delivery</p>
            </div>
            <div className="credibility-card">
              <div className="credibility-icon"><Headphones size={22} /></div>
              <h3>24/7</h3>
              <p>Customer Support</p>
            </div>
            <div className="credibility-card">
              <div className="credibility-icon"><Zap size={22} /></div>
              <h3>AI</h3>
              <p>Powered Automation</p>
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
          <p>&copy; 2026 LogiAI. All rights reserved.</p>
        </div>
      </footer>

    </div>
  );
}

export default LandingPage;
