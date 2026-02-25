import React, { useEffect, useState, useCallback } from "react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer,
  LineChart, Line, Legend
} from "recharts";
import {
  Package, AlertCircle, CheckCircle,
  TrendingUp, Activity, LogOut, ShieldAlert,
  X, FileText, Truck, CreditCard, Calendar, Clock, ShieldCheck
} from "lucide-react";
import "./App.css";

const BASE_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";

const weeklyData = [
  { name: "Mon", orders: 400, resolved: 240, escalated: 20 },
  { name: "Tue", orders: 300, resolved: 139, escalated: 10 },
  { name: "Wed", orders: 200, resolved: 180, escalated: 50 },
  { name: "Thu", orders: 278, resolved: 190, escalated: 15 },
  { name: "Fri", orders: 189, resolved: 280, escalated: 25 },
  { name: "Sat", orders: 239, resolved: 180, escalated: 12 },
  { name: "Sun", orders: 349, resolved: 230, escalated: 8 },
];

function Admin() {
  const [tickets, setTickets] = useState([]);
  const [metrics, setMetrics] = useState(null);
  const [ticketDetail, setTicketDetail] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);

  const token = localStorage.getItem("token");

  const logout = useCallback(() => {
    localStorage.removeItem("token");
    window.location.href = "/login";
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
          ? `High-value order (\u20B9${price.toLocaleString()}) — requires senior approval`
          : `\u20B9${price.toLocaleString()} — within auto-approval limit`,
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
  }, [token, logout, fetchTickets, fetchMetrics]);

  const getStatusBadge = (status) => {
    switch (status) {
      case "AUTO_RESOLVED":
        return <span className="badge badge-success">Auto Resolved</span>;
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

  return (
    <div className="dashboard-container">

      <header className="dashboard-header">
        <div className="header-title">
          <Activity className="icon-large text-primary" />
          <h2>Logistics Command Center</h2>
        </div>
        <button className="btn-outline" onClick={logout}>
          <LogOut size={18} /> Logout
        </button>
      </header>

      {metrics && (
        <div className="metrics-grid">
          <div className="metric-card">
            <Package />
            <h3>{metrics.total_tickets}</h3>
            <p>Total Tickets</p>
          </div>
          <div className="metric-card">
            <CheckCircle />
            <h3>{metrics.auto_resolved}</h3>
            <p>Auto Resolved</p>
          </div>
          <div className="metric-card">
            <AlertCircle />
            <h3>{metrics.pending_escalations}</h3>
            <p>Pending Escalations</p>
          </div>
          <div className="metric-card">
            <TrendingUp />
            <h3>{metrics.escalation_rate_percent}%</h3>
            <p>Escalation Rate</p>
          </div>
        </div>
      )}

      {/* CHARTS (kept intentionally to avoid unused imports) */}
      <div className="charts-grid">
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={weeklyData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey="resolved" fill="#10b981" />
            <Bar dataKey="escalated" fill="#f59e0b" />
          </BarChart>
        </ResponsiveContainer>

        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={weeklyData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis />
            <Tooltip />
            <Line type="monotone" dataKey="orders" stroke="#3b82f6" />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="table-card">
        <h3>Recent Support Tickets</h3>

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
                      <span className="detail-value">\u20B9{ticketDetail.order_details.price?.toLocaleString()}</span>
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