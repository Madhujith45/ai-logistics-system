import React, { useState } from "react";
import { Send, PackageSearch, AlertCircle, CheckCircle } from 'lucide-react';
import "./App.css";

function UserPage() {
  const [text, setText] = useState("");
  const [orderId, setOrderId] = useState("");
  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!text) {
      setError("Please enter your query.");
      return;
    }

    setLoading(true);
    setError("");
    setResponse(null);

    try {
      const res = await fetch("http://127.0.0.1:8000/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          text: text,
          order_id: orderId
        })
      });

      const data = await res.json();
      setResponse(data);

    } catch (err) {
      console.error(err);
      setError("Server error. Please try again.");
    }

    setLoading(false);
  };

  return (
    <div className="container">
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '24px' }}>
        <PackageSearch className="text-primary" size={32} />
        <h2 style={{ margin: 0 }}>Logistics Support</h2>
      </div>

      <form onSubmit={handleSubmit}>
        <label className="text-sm font-medium text-dark">Order ID (Optional)</label>
        <input
          type="text"
          placeholder="e.g. 123"
          value={orderId}
          onChange={(e) => setOrderId(e.target.value)}
        />

        <label className="text-sm font-medium text-dark">How can we help you?</label>
        <textarea
          placeholder="Type your query here... (e.g. 'Where is my order?' or 'Cancel my order')"
          value={text}
          onChange={(e) => setText(e.target.value)}
        />

        <button type="submit" disabled={loading} style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '8px' }}>
          {loading ? "Processing..." : <><Send size={18} /> Send Request</>}
        </button>
      </form>

      {error && (
        <div className="response" style={{ backgroundColor: "var(--danger-light)", borderColor: "#fca5a5", display: 'flex', gap: '12px', alignItems: 'flex-start' }}>
          <AlertCircle className="text-danger" size={20} style={{ flexShrink: 0 }} />
          <p style={{ margin: 0, color: "#991b1b" }}>{error}</p>
        </div>
      )}

      {response && (
        <div className="response" style={{ borderLeft: `4px solid ${response.status === 'AUTO_RESOLVED' ? 'var(--success)' : 'var(--warning)'}` }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
            {response.status === 'AUTO_RESOLVED' ? <CheckCircle className="text-green" size={20} /> : <AlertCircle className="text-yellow" size={20} />}
            <h3 style={{ margin: 0, fontSize: '16px' }}>
              {response.status === 'AUTO_RESOLVED' ? 'Request Resolved' : 'Ticket Escalated'}
            </h3>
          </div>
          
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '16px' }}>
            <div>
              <p className="text-xs text-gray" style={{ margin: '0 0 4px 0' }}>Ticket ID</p>
              <p className="font-medium text-sm" style={{ margin: 0 }}>{response.ticket_id}</p>
            </div>
            <div>
              <p className="text-xs text-gray" style={{ margin: '0 0 4px 0' }}>Intent Detected</p>
              <span className="intent-tag">{response.intent.replace('_', ' ')}</span>
            </div>
          </div>

          <div style={{ backgroundColor: 'white', padding: '12px', borderRadius: '6px', border: '1px solid var(--border-color)' }}>
            <p className="text-xs text-gray" style={{ margin: '0 0 4px 0' }}>System Response</p>
            <p className="text-sm text-dark font-medium" style={{ margin: 0 }}>{response.message}</p>
          </div>
        </div>
      )}
    </div>
  );
}

export default UserPage;
