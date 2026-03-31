import React, { useEffect, useState, useCallback } from "react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer,
  LineChart, Line, Legend,
  PieChart, Pie, Cell
} from "recharts";
import {
  Package, AlertCircle, CheckCircle,
  TrendingUp, Activity, LogOut, ShieldAlert,
  X, FileText, Truck, CreditCard, Calendar, Clock, ShieldCheck,
  LayoutDashboard, TicketIcon, ShoppingCart, BarChart3, Search,
  MapPin
} from "lucide-react";
import "./App.css";
import { BASE_URL } from "./apiBase";

const weeklyData = [
  { name: "Mon", orders: 400, resolved: 240, escalated: 20 },
  { name: "Tue", orders: 300, resolved: 139, escalated: 10 },
  { name: "Wed", orders: 200, resolved: 180, escalated: 50 },
  { name: "Thu", orders: 278, resolved: 190, escalated: 15 },
  { name: "Fri", orders: 189, resolved: 280, escalated: 25 },
  { name: "Sat", orders: 239, resolved: 180, escalated: 12 },
  { name: "Sun", orders: 349, resolved: 230, escalated: 8 },
];

const INTENT_COLORS = ["#2563EB", "#ef4444", "#f59e0b", "#10b981", "#8b5cf6", "#06b6d4", "#ec4899"];

function Admin() {
  const [tickets, setTickets] = useState([]);
  const [metrics, setMetrics] = useState(null);
  const [ticketDetail, setTicketDetail] = useState(null);
  // eslint-disable-next-line no-unused-vars
  const [detailLoading, setDetailLoading] = useState(false);
  const [activeTab, setActiveTab] = useState("dashboard");
  const [orders, setOrders] = useState([]);
  const [orderSearch, setOrderSearch] = useState("");
  const [orderUploads, setOrderUploads] = useState([]);
  const [uploadsLoading, setUploadsLoading] = useState(false);
  const [uploadError, setUploadError] = useState("");
  const [uploadPreviewUrl, setUploadPreviewUrl] = useState("");
  const [selectedUploadName, setSelectedUploadName] = useState("");
  const [selectedUploadType, setSelectedUploadType] = useState("");
  const [uploadOrderSearch, setUploadOrderSearch] = useState("");
  const [uploadOrderSelected, setUploadOrderSelected] = useState("");

  const token = localStorage.getItem("token");

  const logout = useCallback(() => {
    localStorage.removeItem("token");
    localStorage.removeItem("role");
    window.location.href = "/";
  }, []);

  const fetchTickets = useCallback(async () => {
    try {
      const res = await fetch(`${BASE_URL}/tickets`, {
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json"
        }
      });

      if (res.status === 401 || res.status === 403) {
        logout();
        return;
      }

      const data = await res.json();
      setTickets(data);
    } catch (err) {
      console.error(err);
    }
  }, [token, logout]);

  const fetchMetrics = useCallback(async () => {
    try {
      const res = await fetch(`${BASE_URL}/admin/metrics`, {
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json"
        }
      });

      if (res.status === 401 || res.status === 403) {
        logout();
        return;
      }

      const data = await res.json();
      setMetrics(data);
    } catch (err) {
      console.error(err);
    }
  }, [token, logout]);

  const fetchOrders = useCallback(async () => {
    try {
      const res = await fetch(`${BASE_URL}/admin/orders`, {
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json"
        }
      });
      if (res.status === 401 || res.status === 403) {
        logout();
        return;
      }
      const data = await res.json();
      setOrders(data);
    } catch (err) {
      console.error(err);
    }
  }, [token, logout]);

  const approveTicket = async (ticketId) => {
    await fetch(`${BASE_URL}/admin/approve/${ticketId}`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json"
      }
    });
    fetchTickets();
    fetchMetrics();
  };

  const rejectTicket = async (ticketId) => {
    await fetch(`${BASE_URL}/admin/reject/${ticketId}`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json"
      }
    });
    fetchTickets();
    fetchMetrics();
    setTicketDetail(null);
  };

  const fetchTicketDetail = async (ticketId) => {
    setDetailLoading(true);
    try {
      const res = await fetch(`${BASE_URL}/admin/ticket/${ticketId}`, {
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json"
        }
      });
      if (res.ok) {
        const data = await res.json();
        setTicketDetail(data);
      }
    } catch (err) {
      console.error(err);
    }
    setDetailLoading(false);
  };

  const fetchOrderUploads = useCallback(async (orderId) => {
    if (!orderId) {
      setOrderUploads([]);
      return;
    }

    setUploadsLoading(true);
    setUploadError("");
    setUploadPreviewUrl("");
    setSelectedUploadName("");
    setSelectedUploadType("");

    try {
      const res = await fetch(`${BASE_URL}/admin/uploads/${orderId}`, {
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json"
        }
      });

      if (res.status === 401 || res.status === 403) {
        logout();
        return;
      }

      if (!res.ok) {
        throw new Error("Failed to load uploads");
      }

      const data = await res.json();
      setOrderUploads(data.uploads || []);
    } catch (err) {
      console.error(err);
      setOrderUploads([]);
      setUploadError("Could not load uploaded proof files for this order.");
    } finally {
      setUploadsLoading(false);
    }
  }, [token, logout]);

  const previewUpload = async (uploadId, filename) => {
    try {
      setUploadError("");
      const res = await fetch(`${BASE_URL}/admin/uploads/${uploadId}/file`, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });

      if (res.status === 401 || res.status === 403) {
        logout();
        return;
      }

      if (!res.ok) {
        throw new Error("Failed to fetch upload preview");
      }

      const blob = await res.blob();
      const objectUrl = URL.createObjectURL(blob);
      const typeFromBlob = (blob.type || "").toLowerCase();
      const fileLower = (filename || "").toLowerCase();
      const extIsImage = /\.(jpg|jpeg|png|gif|webp|bmp|svg)$/i.test(fileLower);
      const extIsVideo = /\.(mp4|webm|ogg|mov|mkv|avi|m4v)$/i.test(fileLower);

      if (uploadPreviewUrl) {
        URL.revokeObjectURL(uploadPreviewUrl);
      }

      setUploadPreviewUrl(objectUrl);
      setSelectedUploadName(filename || "Uploaded proof");
      if (typeFromBlob.startsWith("image/") || extIsImage) {
        setSelectedUploadType("image");
      } else if (typeFromBlob.startsWith("video/") || extIsVideo) {
        setSelectedUploadType("video");
      } else {
        setSelectedUploadType("file");
      }
    } catch (err) {
      console.error(err);
      setUploadError("Could not open this uploaded file.");
    }
  };

  const handleUploadOrderSearch = () => {
    const orderId = uploadOrderSearch.trim();
    if (!orderId) {
      setUploadError("Enter an order ID to load uploaded proofs.");
      return;
    }
    setUploadOrderSelected(orderId);
    fetchOrderUploads(orderId);
  };

  const getPolicyVerdict = (detail) => {
    if (!detail || !detail.order_details) return null;
    const order = detail.order_details;
    const intent = detail.intent;
    const deliveryDate = order.delivery_date;
    const returnDeadline = order.return_deadline;
    const orderStatus = order.order_status || "Unknown";
    const price = order.price || 0;

    const today = new Date();
    let withinWindow = false;
    let daysLeft = null;
    if (returnDeadline) {
      const deadlineDate = new Date(returnDeadline);
      withinWindow = today <= deadlineDate;
      daysLeft = Math.ceil((deadlineDate - today) / (1000 * 60 * 60 * 24));
    }

    const checks = [];

    // Order Status check
    if (intent === "REFUND_REQUEST") {
      checks.push({
        label: "Delivery Confirmed",
        pass: orderStatus === "Delivered",
        detail: orderStatus === "Delivered"
          ? `Delivered on ${deliveryDate}`
          : `Current status: ${orderStatus} — refund requires delivery`,
      });
      checks.push({
        label: "Within Return Window (7 days)",
        pass: withinWindow,
        detail: withinWindow
          ? `${daysLeft} day(s) remaining (deadline: ${returnDeadline})`
          : `Return window expired on ${returnDeadline}`,
      });
      checks.push({
        label: "Order Value",
        pass: price <= 50000,
        detail: price > 50000
          ? `High-value order (₹${price.toLocaleString()}) — requires senior approval (manual review for refunds over ₹50,000)`
          : `₹${price.toLocaleString()} — within auto-approval limit`,
      });
    } else if (intent === "CANCEL_ORDER") {
      const cancellable = ["Processing", "Placed"].includes(orderStatus);
      checks.push({
        label: "Cancellable Status",
        pass: cancellable,
        detail: cancellable
          ? `Order is '${orderStatus}' — can be cancelled`
          : `Order is '${orderStatus}' — cancellation not possible`,
      });
    } else if (intent === "DAMAGED_PRODUCT" || intent === "MISMATCH_PRODUCT") {
      checks.push({
        label: "Delivery Confirmed",
        pass: orderStatus === "Delivered",
        detail: orderStatus === "Delivered" ? `Delivered on ${deliveryDate}` : `Status: ${orderStatus}`,
      });
      checks.push({
        label: "Within Return Window",
        pass: withinWindow,
        detail: withinWindow ? `${daysLeft} day(s) remaining` : `Expired on ${returnDeadline}`,
      });
    }

    const allPass = checks.length > 0 && checks.every((c) => c.pass);
    return { checks, allPass };
  };

  useEffect(() => {
    if (!token) {
      logout();
      return;
    }
    fetchTickets();
    fetchMetrics();
    fetchOrders();
  }, [token, logout, fetchTickets, fetchMetrics, fetchOrders]);

  useEffect(() => {
    const orderId = ticketDetail?.order_details?.order_id;
    if (!ticketDetail || !orderId) {
      setOrderUploads([]);
      return;
    }
    fetchOrderUploads(orderId);
  }, [ticketDetail, fetchOrderUploads]);

  useEffect(() => {
    return () => {
      if (uploadPreviewUrl) {
        URL.revokeObjectURL(uploadPreviewUrl);
      }
    };
  }, [uploadPreviewUrl]);

  const getStatusBadge = (status) => {
    switch (status) {
      case "AUTO_RESOLVED":
        return <span className="badge badge-success">Auto Resolved</span>;
      case "IN_PROGRESS":
        return <span className="badge badge-info">In Progress</span>;
      case "PENDING_ADMIN":
        return <span className="badge badge-warning">Pending Admin</span>;
      case "APPROVED":
        return <span className="badge badge-primary">Approved</span>;
      case "REJECTED":
        return <span className="badge badge-danger">Rejected</span>;
      default:
        return <span className="badge">{status}</span>;
    }
  };

  const getOrderStatusBadge = (status) => {
    const map = {
      "Placed": { cls: "badge-info", label: "Placed" },
      "Processing": { cls: "badge-info", label: "Processing" },
      "Shipped": { cls: "badge-primary", label: "Shipped" },
      "Out for Delivery": { cls: "badge-warning", label: "Out for Delivery" },
      "Delivered": { cls: "badge-success", label: "Delivered" },
      "Cancelled": { cls: "badge-danger", label: "Cancelled" },
    };
    const m = map[status] || { cls: "", label: status };
    return <span className={`badge ${m.cls}`}>{m.label}</span>;
  };

  const ORDER_STEPS = ["Placed", "Processing", "Shipped", "Out for Delivery", "Delivered"];

  const getStepIndex = (status) => {
    if (status === "Cancelled") return -1;
    const idx = ORDER_STEPS.indexOf(status);
    return idx >= 0 ? idx : 0;
  };

  const filteredOrders = orders.filter(o => {
    const q = orderSearch.toLowerCase();
    if (!q) return true;
    return (
      (o.order_id || "").toLowerCase().includes(q) ||
      (o.customer_name || "").toLowerCase().includes(q) ||
      (o.product_name || "").toLowerCase().includes(q)
    );
  });

  return (
    <div className="admin-layout">

      {/* ── Sidebar ── */}
      <aside className="admin-sidebar">
        <div className="sidebar-brand">
          <Package size={28} className="text-primary" />
          <div>
            <h2>LogiAI</h2>
            <span>Support System</span>
          </div>
        </div>

        <nav className="sidebar-nav">
          <button className={`sidebar-link ${activeTab === "dashboard" ? "active" : ""}`} onClick={() => setActiveTab("dashboard")}>
            <LayoutDashboard size={18} /> Dashboard
          </button>
          <button className={`sidebar-link ${activeTab === "tickets" ? "active" : ""}`} onClick={() => setActiveTab("tickets")}>
            <TicketIcon size={18} /> Tickets
          </button>
          <button className={`sidebar-link ${activeTab === "orders" ? "active" : ""}`} onClick={() => setActiveTab("orders")}>
            <ShoppingCart size={18} /> Orders
          </button>
          <button className={`sidebar-link ${activeTab === "analytics" ? "active" : ""}`} onClick={() => setActiveTab("analytics")}>
            <BarChart3 size={18} /> Analytics
          </button>
          <button className={`sidebar-link ${activeTab === "uploads" ? "active" : ""}`} onClick={() => setActiveTab("uploads")}>
            <FileText size={18} /> Uploads
          </button>
        </nav>

        <div className="sidebar-footer">
          <button className="sidebar-link logout-link" onClick={logout}>
            <LogOut size={18} /> Logout
          </button>
        </div>
      </aside>

      {/* ── Main Content ── */}
      <main className="admin-main">

        {/* ─── Dashboard Tab ─── */}
        {activeTab === "dashboard" && (
          <>
            <div className="admin-page-header">
              <h2>Dashboard</h2>
            </div>

            {metrics && (
              <>
                <div className="metrics-grid">
                  <div className="metric-card">
                    <div className="metric-icon" style={{ background: "rgba(37,99,235,0.1)" }}>
                      <Package size={24} color="#2563EB" />
                    </div>
                    <div>
                      <h3>{metrics.total_orders || 0}</h3>
                      <p>Total Orders</p>
                    </div>
                  </div>
                  <div className="metric-card">
                    <div className="metric-icon" style={{ background: "rgba(16,185,129,0.15)" }}>
                      <Truck size={24} color="#10b981" />
                    </div>
                    <div>
                      <h3>{metrics.active_shipments || 0}</h3>
                      <p>Active Shipments</p>
                    </div>
                  </div>
                  <div className="metric-card">
                    <div className="metric-icon" style={{ background: "rgba(245,158,11,0.15)" }}>
                      <AlertCircle size={24} color="#fbbf24" />
                    </div>
                    <div>
                      <h3>{metrics.pending_escalations}</h3>
                      <p>Pending Escalations</p>
                    </div>
                  </div>
                  <div className="metric-card">
                    <div className="metric-icon" style={{ background: "rgba(16,185,129,0.1)" }}>
                      <TrendingUp size={24} color="#10b981" />
                    </div>
                    <div>
                      <h3>{metrics.average_confidence ? (metrics.average_confidence * 100).toFixed(1) : 0}%</h3>
                      <p>AI Accuracy</p>
                    </div>
                  </div>
                </div>

                {/* Charts Row */}
                <div className="charts-grid">
                  <div className="table-card" style={{ padding: 0 }}>
                    <h3 style={{ display: "flex", alignItems: "center", gap: 8 }}>
                      <Activity size={16} /> Query Volume Trend
                    </h3>
                    <div style={{ padding: "0 16px 16px" }}>
                      <ResponsiveContainer width="100%" height={300}>
                        <LineChart data={weeklyData}>
                          <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.06)" />
                          <XAxis dataKey="name" stroke="var(--text-muted)" />
                          <YAxis stroke="var(--text-muted)" />
                          <Tooltip
                            contentStyle={{ background: "var(--bg-card-solid)", border: "1px solid var(--border-color)", borderRadius: 10 }}
                            labelStyle={{ color: "var(--text-primary)" }}
                            itemStyle={{ color: "var(--text-secondary)" }}
                          />
                          <Line type="monotone" dataKey="orders" stroke="#2563EB" strokeWidth={2} dot={{ fill: "#2563EB", r: 4 }} />
                        </LineChart>
                      </ResponsiveContainer>
                    </div>
                  </div>

                  <div className="table-card" style={{ padding: 0 }}>
                    <h3 style={{ display: "flex", alignItems: "center", gap: 8 }}>
                      <BarChart3 size={16} /> Intent Distribution
                    </h3>
                    <div style={{ padding: "0 16px 16px", display: "flex", alignItems: "center", justifyContent: "center" }}>
                      {metrics.intent_distribution && metrics.intent_distribution.length > 0 ? (
                        <ResponsiveContainer width="100%" height={300}>
                          <PieChart>
                            <Pie
                              data={metrics.intent_distribution}
                              cx="50%"
                              cy="50%"
                              innerRadius={60}
                              outerRadius={110}
                              paddingAngle={3}
                              dataKey="value"
                              nameKey="name"
                            >
                              {metrics.intent_distribution.map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={INTENT_COLORS[index % INTENT_COLORS.length]} />
                              ))}
                            </Pie>
                            <Tooltip
                              contentStyle={{ background: "var(--bg-card-solid)", border: "1px solid var(--border-color)", borderRadius: 10 }}
                            />
                            <Legend />
                          </PieChart>
                        </ResponsiveContainer>
                      ) : (
                        <p style={{ color: "var(--text-muted)" }}>No intent data yet</p>
                      )}
                    </div>
                  </div>
                </div>
              </>
            )}
          </>
        )}

        {/* ─── Tickets Tab ─── */}
        {activeTab === "tickets" && (
          <>
            <div className="admin-page-header">
              <h2>Support Tickets</h2>
              <div className="header-stats">
                <span className="badge badge-success">{tickets.filter(t => t.status === "AUTO_RESOLVED").length} Resolved</span>
                <span className="badge badge-warning">{tickets.filter(t => t.status === "PENDING_ADMIN").length} Pending</span>
              </div>
            </div>

            <div className="table-card">
              {tickets.length === 0 ? (
                <div className="empty-state">
                  <ShieldAlert size={48} />
                  <p>No tickets found.</p>
                </div>
              ) : (
                <table className="modern-table">
                  <thead>
                    <tr>
                      <th>Ticket ID</th>
                      <th>User Query</th>
                      <th>Order ID</th>
                      <th>Intent</th>
                      <th>Status</th>
                      <th>Confidence</th>
                      <th>Escalation Reason</th>
                      <th>Bot Response</th>
                      <th>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {tickets.map((ticket) => (
                      <tr key={ticket.ticket_id}>
                        <td>{ticket.ticket_id}</td>
                        <td className="user-query-cell">{ticket.text || "—"}</td>
                        <td>
                          <span
                            className="order-id-link"
                            onClick={() => fetchTicketDetail(ticket.ticket_id)}
                            title="Click to view order details & policy check"
                          >
                            {ticket.order_id || "—"}
                          </span>
                        </td>
                        <td>{ticket.intent.replace("_", " ")}</td>
                        <td>{getStatusBadge(ticket.status)}</td>
                        <td>{(ticket.confidence * 100).toFixed(1)}%</td>
                        <td className="escalation-cell">{ticket.escalation_reason || "—"}</td>
                        <td className="message-cell">{ticket.message}</td>
                        <td>
                          {ticket.status === "PENDING_ADMIN" ? (
                            <>
                              <button onClick={() => approveTicket(ticket.ticket_id)}>Approve</button>
                              <button onClick={() => rejectTicket(ticket.ticket_id)}>Reject</button>
                            </>
                          ) : ticket.status === "IN_PROGRESS" ? (
                            <span style={{ color: "var(--text-muted)", fontStyle: "italic" }}>Awaiting Info</span>
                          ) : (
                            "Resolved"
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </>
        )}

        {/* ─── Orders Tab ─── */}
        {activeTab === "orders" && (
          <>
            <div className="admin-page-header">
              <h2>Orders</h2>
            </div>

            <div className="order-search-bar">
              <Search size={18} className="order-search-icon" />
              <input
                type="text"
                placeholder="Search by Order ID, customer or product..."
                value={orderSearch}
                onChange={(e) => setOrderSearch(e.target.value)}
                className="order-search-input"
              />
            </div>

            <div className="orders-list">
              {filteredOrders.length === 0 ? (
                <div className="empty-state">
                  <ShoppingCart size={48} />
                  <p>No orders found.</p>
                </div>
              ) : (
                filteredOrders.map((order) => {
                  const stepIdx = getStepIndex(order.status);
                  const isCancelled = order.status === "Cancelled";
                  return (
                    <div className={`order-card ${isCancelled ? "order-cancelled" : ""}`} key={order.order_id}>
                      <div className="order-card-header">
                        <div className="order-card-title">
                          <strong>{order.order_id}</strong>
                          {getOrderStatusBadge(order.status)}
                        </div>
                        <div className="order-card-meta">
                          <span><CreditCard size={14} /> {order.payment_mode || "N/A"}</span>
                          <span>₹{(order.price || 0).toLocaleString()}</span>
                        </div>
                      </div>

                      <div className="order-card-info">
                        <span><Package size={14} /> {order.product_name}</span>
                        <span><MapPin size={14} /> {order.destination}</span>
                        {order.customer_name && <span>Customer: {order.customer_name}</span>}
                      </div>

                      {/* Progress Stepper */}
                      <div className="order-stepper">
                        {ORDER_STEPS.map((step, i) => {
                          const completed = !isCancelled && i <= stepIdx;
                          const current = !isCancelled && i === stepIdx;
                          return (
                            <React.Fragment key={step}>
                              <div className={`stepper-step ${completed ? "step-completed" : ""} ${current ? "step-current" : ""}`}>
                                <div className="stepper-circle">
                                  {completed ? <CheckCircle size={18} /> : <span>{i + 1}</span>}
                                </div>
                                <span className="stepper-label">{step}</span>
                              </div>
                              {i < ORDER_STEPS.length - 1 && (
                                <div className={`stepper-line ${!isCancelled && i < stepIdx ? "line-completed" : ""}`} />
                              )}
                            </React.Fragment>
                          );
                        })}
                      </div>

                      <div className="order-card-footer">
                        <span><Calendar size={14} /> Expected: {order.expected_delivery || "N/A"}</span>
                        {order.delivery_date && <span><CheckCircle size={14} /> Delivered: {order.delivery_date}</span>}
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </>
        )}

        {/* ─── Analytics Tab ─── */}
        {activeTab === "analytics" && (
          <>
            <div className="admin-page-header">
              <h2>Analytics</h2>
            </div>

            {metrics && (
              <div className="metrics-grid">
                <div className="metric-card">
                  <div className="metric-icon" style={{ background: "rgba(37,99,235,0.1)" }}>
                    <Package size={24} color="#2563EB" />
                  </div>
                  <div>
                    <h3>{metrics.total_tickets}</h3>
                    <p>Total Tickets</p>
                  </div>
                </div>
                <div className="metric-card">
                  <div className="metric-icon" style={{ background: "rgba(16,185,129,0.15)" }}>
                    <CheckCircle size={24} color="#34d399" />
                  </div>
                  <div>
                    <h3>{metrics.auto_resolved}</h3>
                    <p>Auto Resolved</p>
                  </div>
                </div>
                <div className="metric-card">
                  <div className="metric-icon" style={{ background: "rgba(245,158,11,0.15)" }}>
                    <AlertCircle size={24} color="#fbbf24" />
                  </div>
                  <div>
                    <h3>{metrics.pending_escalations}</h3>
                    <p>Pending Escalations</p>
                  </div>
                </div>
                <div className="metric-card">
                  <div className="metric-icon" style={{ background: "rgba(167,139,250,0.1)" }}>
                    <TrendingUp size={24} color="#a78bfa" />
                  </div>
                  <div>
                    <h3>{metrics.escalation_rate_percent}%</h3>
                    <p>Escalation Rate</p>
                  </div>
                </div>
              </div>
            )}

            <div className="charts-grid">
              <div className="table-card" style={{ padding: 0 }}>
                <h3 style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <BarChart3 size={16} /> Resolution Overview
                </h3>
                <div style={{ padding: "0 16px 16px" }}>
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={weeklyData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.06)" />
                      <XAxis dataKey="name" stroke="var(--text-muted)" />
                      <YAxis stroke="var(--text-muted)" />
                      <Tooltip
                        contentStyle={{ background: "var(--bg-card-solid)", border: "1px solid var(--border-color)", borderRadius: 10 }}
                        labelStyle={{ color: "var(--text-primary)" }}
                        itemStyle={{ color: "var(--text-secondary)" }}
                      />
                      <Legend />
                      <Bar dataKey="resolved" fill="#2563EB" radius={[4, 4, 0, 0]} />
                      <Bar dataKey="escalated" fill="#fbbf24" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>

              <div className="table-card" style={{ padding: 0 }}>
                <h3 style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <Activity size={16} /> Weekly Order Trend
                </h3>
                <div style={{ padding: "0 16px 16px" }}>
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={weeklyData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.06)" />
                      <XAxis dataKey="name" stroke="var(--text-muted)" />
                      <YAxis stroke="var(--text-muted)" />
                      <Tooltip
                        contentStyle={{ background: "var(--bg-card-solid)", border: "1px solid var(--border-color)", borderRadius: 10 }}
                        labelStyle={{ color: "var(--text-primary)" }}
                        itemStyle={{ color: "var(--text-secondary)" }}
                      />
                      <Line type="monotone" dataKey="orders" stroke="#2563EB" strokeWidth={2} dot={{ fill: "#2563EB", r: 4 }} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>
          </>
        )}

        {/* ─── Uploads Tab ─── */}
        {activeTab === "uploads" && (
          <>
            <div className="admin-page-header">
              <h2>Uploaded Proofs</h2>
            </div>

            <div className="order-search-bar">
              <Search size={18} className="order-search-icon" />
              <input
                type="text"
                placeholder="Enter Order ID (e.g. ORD-1003)"
                value={uploadOrderSearch}
                onChange={(e) => setUploadOrderSearch(e.target.value)}
                className="order-search-input"
              />
              <button onClick={handleUploadOrderSearch}>Load Uploads</button>
            </div>

            <div className="table-card">
              {!uploadOrderSelected ? (
                <div className="empty-state">
                  <FileText size={48} />
                  <p>Search by order ID to view uploaded videos/images.</p>
                </div>
              ) : uploadsLoading ? (
                <p className="detail-no-data">Loading uploaded files for {uploadOrderSelected}...</p>
              ) : orderUploads.length === 0 ? (
                <p className="detail-no-data">No proof files uploaded for {uploadOrderSelected} yet.</p>
              ) : (
                <div className="policy-checks">
                  {orderUploads.map((upload) => (
                    <div key={upload.upload_id} className="policy-check-row" style={{ justifyContent: "space-between" }}>
                      <div>
                        <div style={{ fontWeight: 600 }}>{upload.filename || "proof file"}</div>
                        <div style={{ color: "var(--text-muted)", fontSize: 12 }}>
                          {upload.size_bytes || 0} bytes | status: {upload.verification_status || "pending"}
                        </div>
                      </div>
                      <button onClick={() => previewUpload(upload.upload_id, upload.filename)}>Preview</button>
                    </div>
                  ))}
                </div>
              )}

              {uploadError && (
                <div className="detail-escalation-reason" style={{ marginTop: 12 }}>
                  <AlertCircle size={14} /> {uploadError}
                </div>
              )}

              {uploadPreviewUrl && (
                <div style={{ marginTop: 14 }}>
                  <div style={{ fontWeight: 600, marginBottom: 8 }}>{selectedUploadName}</div>
                  {selectedUploadType === "image" ? (
                    <img
                      src={uploadPreviewUrl}
                      alt={selectedUploadName}
                      style={{ width: "100%", borderRadius: 8, maxHeight: 420, objectFit: "contain" }}
                    />
                  ) : selectedUploadType === "video" ? (
                    <video controls style={{ width: "100%", borderRadius: 8 }} src={uploadPreviewUrl} />
                  ) : (
                    <a href={uploadPreviewUrl} target="_blank" rel="noreferrer">Open uploaded file</a>
                  )}
                </div>
              )}
            </div>
          </>
        )}

      </main>

      {/* Ticket Detail Modal */}
      {ticketDetail && (
        <div className="detail-overlay" onClick={() => setTicketDetail(null)}>
          <div className="detail-modal" onClick={(e) => e.stopPropagation()}>
            <div className="detail-modal-header">
              <h3><FileText size={18} /> Ticket #{ticketDetail.ticket_id} — Review Panel</h3>
              <button className="detail-close-btn" onClick={() => setTicketDetail(null)}>
                <X size={18} />
              </button>
            </div>

            <div className="detail-modal-body">
              {/* User Query */}
              <div className="detail-section">
                <h4>User Query</h4>
                <div className="detail-quote">"{ticketDetail.text}"</div>
                <div className="detail-meta-row">
                  <span><strong>Intent:</strong> {ticketDetail.intent?.replace(/_/g, " ")}</span>
                  <span><strong>Confidence:</strong> {((ticketDetail.confidence || 0) * 100).toFixed(1)}%</span>
                </div>
                {ticketDetail.escalation_reason && (
                  <div className="detail-escalation-reason">
                    <AlertCircle size={14} /> {ticketDetail.escalation_reason}
                  </div>
                )}
              </div>

              {/* Order Details */}
              {ticketDetail.order_details ? (
                <div className="detail-section">
                  <h4><Truck size={16} /> Order Details</h4>
                  <div className="detail-grid">
                    <div className="detail-field">
                      <span className="detail-label">Order ID</span>
                      <span className="detail-value">#{ticketDetail.order_details.order_id}</span>
                    </div>
                    <div className="detail-field">
                      <span className="detail-label">Product</span>
                      <span className="detail-value">{ticketDetail.order_details.product_name}</span>
                    </div>
                    <div className="detail-field">
                      <span className="detail-label">Price</span>
                      <span className="detail-value">₹{ticketDetail.order_details.price?.toLocaleString()}</span>
                    </div>
                    <div className="detail-field">
                      <span className="detail-label"><CreditCard size={13} /> Payment</span>
                      <span className="detail-value">{ticketDetail.order_details.payment_mode}</span>
                    </div>
                    <div className="detail-field">
                      <span className="detail-label">Status</span>
                      <span className="detail-value">{ticketDetail.order_details.order_status}</span>
                    </div>
                    <div className="detail-field">
                      <span className="detail-label"><Calendar size={13} /> Delivered</span>
                      <span className="detail-value">{ticketDetail.order_details.delivery_date || "Not yet"}</span>
                    </div>
                    <div className="detail-field">
                      <span className="detail-label"><Clock size={13} /> Return Deadline</span>
                      <span className="detail-value">{ticketDetail.order_details.return_deadline || "N/A"}</span>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="detail-section">
                  <h4><Truck size={16} /> Order Details</h4>
                  <p className="detail-no-data">No order ID was provided with this query.</p>
                </div>
              )}

              {ticketDetail.order_details && (
                <div className="detail-section">
                  <h4>Damage Proof Uploads</h4>
                  {uploadsLoading ? (
                    <p className="detail-no-data">Loading uploaded files...</p>
                  ) : orderUploads.length === 0 ? (
                    <p className="detail-no-data">No proof files uploaded for this order yet.</p>
                  ) : (
                    <div className="policy-checks">
                      {orderUploads.map((upload) => (
                        <div key={upload.upload_id} className="policy-check-row" style={{ justifyContent: "space-between" }}>
                          <div>
                            <div style={{ fontWeight: 600 }}>{upload.filename || "proof file"}</div>
                            <div style={{ color: "var(--text-muted)", fontSize: 12 }}>
                              {upload.size_bytes || 0} bytes | status: {upload.verification_status || "pending"}
                            </div>
                          </div>
                          <button onClick={() => previewUpload(upload.upload_id, upload.filename)}>Preview</button>
                        </div>
                      ))}
                    </div>
                  )}

                  {uploadError && (
                    <div className="detail-escalation-reason" style={{ marginTop: 10 }}>
                      <AlertCircle size={14} /> {uploadError}
                    </div>
                  )}

                  {uploadPreviewUrl && (
                    <div style={{ marginTop: 12 }}>
                      <div style={{ fontWeight: 600, marginBottom: 8 }}>{selectedUploadName}</div>
                      {selectedUploadType === "image" ? (
                        <img
                          src={uploadPreviewUrl}
                          alt={selectedUploadName}
                          style={{ width: "100%", borderRadius: 8, maxHeight: 420, objectFit: "contain" }}
                        />
                      ) : selectedUploadType === "video" ? (
                        <video controls style={{ width: "100%", borderRadius: 8 }} src={uploadPreviewUrl} />
                      ) : (
                        <a href={uploadPreviewUrl} target="_blank" rel="noreferrer">Open uploaded file</a>
                      )}
                    </div>
                  )}
                </div>
              )}

              {/* Policy Check */}
              {(() => {
                const verdict = getPolicyVerdict(ticketDetail);
                if (!verdict || verdict.checks.length === 0) return null;
                return (
                  <div className="detail-section">
                    <h4><ShieldCheck size={16} /> Policy Eligibility Check</h4>
                    <div className="policy-checks">
                      {verdict.checks.map((check, i) => (
                        <div key={i} className={`policy-check-row ${check.pass ? "check-pass" : "check-fail"}`}>
                          <div className="policy-check-icon">
                            {check.pass ? <CheckCircle size={16} /> : <X size={16} />}
                          </div>
                          <div>
                            <div className="policy-check-label">{check.label}</div>
                            <div className="policy-check-detail">{check.detail}</div>
                          </div>
                        </div>
                      ))}
                    </div>
                    <div className={`policy-verdict ${verdict.allPass ? "verdict-approve" : "verdict-caution"}`}>
                      {verdict.allPass
                        ? "\u2705 All policy checks passed — Safe to approve"
                        : "\u26A0\uFE0F Some checks failed — Review carefully before approving"}
                    </div>
                  </div>
                );
              })()}

              {/* Conversation History */}
              {ticketDetail.conversation && ticketDetail.conversation.length > 0 && (
                <div className="detail-section">
                  <h4>Conversation History</h4>
                  <div className="detail-conversation">
                    {ticketDetail.conversation.map((msg, i) => (
                      <div key={i} className={`detail-msg ${msg.sender === "user" ? "detail-msg-user" : "detail-msg-bot"}`}>
                        <span className="detail-msg-sender">{msg.sender === "user" ? "Customer" : "Bot"}</span>
                        <span className="detail-msg-text">{msg.message}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Admin Actions */}
              {ticketDetail.status === "PENDING_ADMIN" && (
                <div className="detail-actions">
                  <button className="detail-approve-btn" onClick={() => { approveTicket(ticketDetail.ticket_id); setTicketDetail(null); }}>
                    <CheckCircle size={16} /> Approve Request
                  </button>
                  <button className="detail-reject-btn" onClick={() => { rejectTicket(ticketDetail.ticket_id); setTicketDetail(null); }}>
                    <X size={16} /> Reject Request
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

    </div>
  );
}

export default Admin;