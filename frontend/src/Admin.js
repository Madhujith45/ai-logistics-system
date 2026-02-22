import React, { useEffect, useState } from "react";
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  LineChart, Line, Legend
} from 'recharts';
import { 
  Package, AlertCircle, CheckCircle, 
  TrendingUp, Activity, LogOut, ShieldAlert
} from 'lucide-react';
import "./App.css";

/* ===========================
   CONFIG
=========================== */

const BASE_URL = "https://ai-logistics-system.onrender.com";

/* ===========================
   MOCK CHART DATA
=========================== */

const weeklyData = [
  { name: 'Mon', orders: 400, resolved: 240, escalated: 20 },
  { name: 'Tue', orders: 300, resolved: 139, escalated: 10 },
  { name: 'Wed', orders: 200, resolved: 980, escalated: 50 },
  { name: 'Thu', orders: 278, resolved: 390, escalated: 15 },
  { name: 'Fri', orders: 189, resolved: 480, escalated: 25 },
  { name: 'Sat', orders: 239, resolved: 380, escalated: 12 },
  { name: 'Sun', orders: 349, resolved: 430, escalated: 8 },
];

/* ===========================
   COMPONENT
=========================== */

function Admin() {
  const [tickets, setTickets] = useState([]);
  const [metrics, setMetrics] = useState(null);

  const token = localStorage.getItem("token");

  const authHeaders = {
    "Authorization": `Bearer ${token}`,
    "Content-Type": "application/json"
  };

  const logout = () => {
    localStorage.removeItem("token");
    window.location.href = "/login";
  };

  const fetchTickets = async () => {
    try {
      const res = await fetch(`${BASE_URL}/tickets`, { headers: authHeaders });

      if (res.status === 401 || res.status === 403) {
        logout();
        return;
      }

      const data = await res.json();
      setTickets(data);
    } catch (err) {
      console.error(err);
    }
  };

  const fetchMetrics = async () => {
    try {
      const res = await fetch(`${BASE_URL}/admin/metrics`, { headers: authHeaders });

      if (res.status === 401 || res.status === 403) {
        logout();
        return;
      }

      const data = await res.json();
      setMetrics(data);
    } catch (err) {
      console.error(err);
    }
  };

  const approveTicket = async (ticketId) => {
    await fetch(`${BASE_URL}/admin/approve/${ticketId}`, {
      method: "POST",
      headers: authHeaders
    });
    fetchTickets();
    fetchMetrics();
  };

  const rejectTicket = async (ticketId) => {
    await fetch(`${BASE_URL}/admin/reject/${ticketId}`, {
      method: "POST",
      headers: authHeaders
    });
    fetchTickets();
    fetchMetrics();
  };

  useEffect(() => {
    if (!token) {
      logout();
      return;
    }

    fetchTickets();
    fetchMetrics();
  }, []);

  const getStatusBadge = (status) => {
    switch(status) {
      case 'AUTO_RESOLVED': return <span className="badge badge-success">Auto Resolved</span>;
      case 'PENDING_ADMIN': return <span className="badge badge-warning">Pending Admin</span>;
      case 'APPROVED': return <span className="badge badge-primary">Approved</span>;
      case 'REJECTED': return <span className="badge badge-danger">Rejected</span>;
      default: return <span className="badge">{status}</span>;
    }
  };

  return (
    <div className="dashboard-container">

      {/* HEADER */}
      <header className="dashboard-header">
        <div className="header-title">
          <Activity className="icon-large text-primary" />
          <h2>Logistics Command Center</h2>
        </div>
        <button className="btn-outline" onClick={logout}>
          <LogOut size={18} /> Logout
        </button>
      </header>

      {/* METRICS */}
      {metrics && (
        <div className="metrics-grid">

          <div className="metric-card">
            <div className="metric-icon bg-blue-light">
              <Package className="text-blue" />
            </div>
            <div className="metric-info">
              <p>Total Tickets</p>
              <h3>{metrics.total_tickets}</h3>
            </div>
          </div>

          <div className="metric-card">
            <div className="metric-icon bg-green-light">
              <CheckCircle className="text-green" />
            </div>
            <div className="metric-info">
              <p>Auto Resolved</p>
              <h3>{metrics.auto_resolved}</h3>
            </div>
          </div>

          <div className="metric-card">
            <div className="metric-icon bg-yellow-light">
              <AlertCircle className="text-yellow" />
            </div>
            <div className="metric-info">
              <p>Pending Escalations</p>
              <h3>{metrics.pending_escalations}</h3>
            </div>
          </div>

          <div className="metric-card">
            <div className="metric-icon bg-purple-light">
              <TrendingUp className="text-purple" />
            </div>
            <div className="metric-info">
              <p>Escalation Rate</p>
              <h3>{metrics.escalation_rate_percent}%</h3>
            </div>
          </div>

        </div>
      )}

      {/* CHARTS */}
      <div className="charts-grid">

        <div className="chart-card">
          <h3>Weekly AI Resolution vs Escalation</h3>
          <div className="chart-wrapper">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={weeklyData}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                <XAxis dataKey="name" axisLine={false} tickLine={false} />
                <YAxis axisLine={false} tickLine={false} />
                <Tooltip />
                <Legend />
                <Bar dataKey="resolved" fill="#10b981" radius={[4,4,0,0]} />
                <Bar dataKey="escalated" fill="#f59e0b" radius={[4,4,0,0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="chart-card">
          <h3>Logistics Volume Trend</h3>
          <div className="chart-wrapper">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={weeklyData}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                <XAxis dataKey="name" axisLine={false} tickLine={false} />
                <YAxis axisLine={false} tickLine={false} />
                <Tooltip />
                <Line type="monotone" dataKey="orders" stroke="#3b82f6" strokeWidth={3} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

      </div>

      {/* TICKETS TABLE */}
      <div className="table-card">
        <h3>Recent Support Tickets</h3>

        {tickets.length === 0 ? (
          <div className="empty-state">
            <ShieldAlert size={48} className="text-gray-light" />
            <p>No tickets found.</p>
          </div>
        ) : (
          <div className="table-responsive">
            <table className="modern-table">
              <thead>
                <tr>
                  <th>Ticket ID</th>
                  <th>Intent</th>
                  <th>Status</th>
                  <th>Confidence</th>
                  <th>Message</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {tickets.map((ticket) => (
                  <tr key={ticket.ticket_id}>
                    <td>{ticket.ticket_id}</td>
                    <td>{ticket.intent.replace('_', ' ')}</td>
                    <td>{getStatusBadge(ticket.status)}</td>
                    <td>{(ticket.confidence * 100).toFixed(1)}%</td>
                    <td>{ticket.message}</td>
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
          </div>
        )}
      </div>

    </div>
  );
}

export default Admin;