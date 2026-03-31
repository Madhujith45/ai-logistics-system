import React, { useState, useRef, useEffect, useCallback } from "react";
import {
  MessageSquare, X, Send, Mic, MicOff, Bot, User,
  Package, Truck, Minimize2, Upload
} from "lucide-react";
import "./ChatWidget.css";
import { BASE_URL } from "../apiBase";

/* ── Session ID ── */
const genSession = () =>
  "w_" + Date.now() + "_" + Math.random().toString(36).slice(2, 9);

/* ── Timestamp ── */
const ts = () =>
  new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

/* ── Speech Recognition ── */
const SpeechRecognition =
  window.SpeechRecognition || window.webkitSpeechRecognition;

/* ================================================================
   ChatWidget — floating bubble + popup
   ================================================================ */
function ChatWidget({ externalOpen, onClose }) {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([
    {
      sender: "bot",
      text:
        "👋 Hello! I'm the LogiAI Support Assistant.\n\nI can help you with:\n• 📦 Track your order\n• ❌ Cancel an order\n• 💳 Request a refund\n• 📝 Report damage or issues\n\nType your message or tap a quick action below!",
      time: ts(),
    },
  ]);
  const [input, setInput] = useState("");
  const [orderId, setOrderId] = useState("");
  const [loading, setLoading] = useState(false);
  const [listening, setListening] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [waitingForProof, setWaitingForProof] = useState(false);  // Show upload only when damage claimed
  const [pulse, setPulse] = useState(true); // attention pulse on bubble
  const [sessionId] = useState(genSession);

  const chatEndRef = useRef(null);
  const inputRef = useRef(null);
  const fileInputRef = useRef(null);
  const recognitionRef = useRef(null);

  /* sync with external open prop (from Dashboard sidebar) */
  useEffect(() => {
    if (externalOpen !== undefined) setOpen(externalOpen);
  }, [externalOpen]);

  const closeChat = () => {
    setOpen(false);
    if (onClose) onClose();
  };

  /* auto-scroll */
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  /* focus input when opened */
  useEffect(() => {
    if (open) {
      setPulse(false);
      setTimeout(() => inputRef.current?.focus(), 300);
    }
  }, [open]);

  /* ── Extract order ID from message ── */
  const extractOrderId = (text) => {
    const m = text.match(/(?:#?\s*)?ORD-\d{4}/i);
    return m ? m[0].replace("#", "").trim().toUpperCase() : null;
  };

  /* ── Send message ── */
  const handleSend = useCallback(
    async (overrideText) => {
      const text = (overrideText || input).trim();
      if (!text || loading) return;

      const extractedId = extractOrderId(text);
      const finalOrderId = orderId.trim() || extractedId;

      setMessages((prev) => [
        ...prev,
        { sender: "user", text: text + (finalOrderId ? ` (Order: #${finalOrderId})` : ""), time: ts() },
      ]);
      setInput("");
      setLoading(true);

      try {
        const token = localStorage.getItem("token");
        const headers = { "Content-Type": "application/json" };
        if (token) headers["Authorization"] = `Bearer ${token}`;

        const res = await fetch(`${BASE_URL}/chat`, {
          method: "POST",
          headers,
          body: JSON.stringify({
            text,
            order_id: finalOrderId || null,
            session_id: sessionId,
          }),
        });

        const data = await res.json();
        
        // Only show upload button if the bot explicitly asks for proof/upload
        // (usually identified by the video emoji or 'upload' keyword in the success message)
        const botMsg = (data.message || "").toLowerCase();
        const isEligible = data.intent === "DAMAGED_PRODUCT" || data.intent === "MISMATCH_PRODUCT";
        const askedForProof = botMsg.includes("upload") || botMsg.includes("📹");
        
        setWaitingForProof(isEligible && askedForProof);
        
        setMessages((prev) => [
          ...prev,
          { sender: "bot", text: data.message, intent: data.intent, time: ts() },
        ]);
      } catch {
        setMessages((prev) => [
          ...prev,
          {
            sender: "bot",
            text: "Sorry, I couldn't reach the server. Please try again later.",
            time: ts(),
          },
        ]);
      }
      setLoading(false);
    },
    [input, loading, orderId, sessionId]
  );

  /* ── Voice input ── */
  const toggleVoice = useCallback(() => {
    if (!SpeechRecognition) {
      alert("Speech recognition is not supported in your browser.");
      return;
    }
    if (listening) {
      recognitionRef.current?.stop();
      setListening(false);
      return;
    }
    const recognition = new SpeechRecognition();
    recognition.lang = "en-US";
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;
    recognition.onresult = (e) => {
      const transcript = e.results[0][0].transcript;
      setInput((prev) => (prev ? prev + " " + transcript : transcript));
      setListening(false);
      // Keep keyboard flow smooth after voice capture: Enter should send.
      setTimeout(() => inputRef.current?.focus(), 0);
    };
    recognition.onerror = () => setListening(false);
    recognition.onend = () => {
      setListening(false);
      setTimeout(() => inputRef.current?.focus(), 0);
    };
    recognitionRef.current = recognition;
    recognition.start();
    setListening(true);
  }, [listening]);

  /* ── File Upload for Damage Proof ── */
  const handleFileSelect = useCallback(async (e) => {
    const file = e.target.files?.[0];
    if (!file || uploading) return;

    const finalOrderId = orderId.trim();
    if (!finalOrderId) {
      setMessages((prev) => [
        ...prev,
        {
          sender: "bot",
          text: "❌ Please enter your Order ID in the field above to upload proof.",
          time: ts(),
        },
      ]);
      return;
    }

    setUploading(true);
    setMessages((prev) => [
      ...prev,
      { sender: "user", text: `📹 Uploading damage proof: ${file.name} (${(file.size / 1024 / 1024).toFixed(2)} MB)`, time: ts() },
    ]);

    try {
      const token = localStorage.getItem("token");
      const formData = new FormData();
      formData.append("order_id", finalOrderId);
      formData.append("file", file);

      const headers = {};
      if (token) headers["Authorization"] = `Bearer ${token}`;

      const res = await fetch(`${BASE_URL}/upload-proof`, {
        method: "POST",
        headers,
        body: formData,
      });

      const data = await res.json();

      if (res.ok) {
        setMessages((prev) => [
          ...prev,
          {
            sender: "bot",
            text: `✅ Damage proof received!\n\nYour video has been securely stored in our database. Our quality team will review it within 24 hours and confirm your replacement or refund.\n\nWhat would you like to do next?`,
            time: ts(),
          },
        ]);
        setWaitingForProof(false);  // Proof uploaded, done waiting
      } else {
        setMessages((prev) => [
          ...prev,
          {
            sender: "bot",
            text: `❌ Upload failed: ${data.detail || "Please try again with a valid file"}`,
            time: ts(),
          },
        ]);
      }
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          sender: "bot",
          text: "❌ Connection error. Please check your internet and try again.",
          time: ts(),
        },
      ]);
    }

    setUploading(false);
    if (fileInputRef.current) fileInputRef.current.value = "";
  }, [orderId, uploading]);

  const openFileDialog = () => fileInputRef.current?.click();

  /* ── Quick actions ── */
  const quickActions = [
    { label: "Track Order", icon: <Truck size={13} />, msg: "I want to track my order" },
    { label: "Cancel", icon: <Package size={13} />, msg: "I want to cancel my order" },
    { label: "Refund", icon: <Package size={13} />, msg: "I want a refund" },
  ];

  /* ── Render ── */
  return (
    <>
      {/* ── Floating Bubble ── */}
      <button
        className={`cw-bubble ${open ? "cw-bubble-hidden" : ""} ${pulse ? "cw-pulse" : ""}`}
        onClick={() => setOpen(true)}
        aria-label="Open chat support"
      >
        <MessageSquare size={26} />
      </button>

      {/* ── Chat Popup ── */}
      <div className={`cw-popup ${open ? "cw-popup-open" : ""}`}>
        {/* Header */}
        <div className="cw-header">
          <div className="cw-header-left">
            <div className="cw-avatar">
              <Bot size={20} />
            </div>
            <div>
              <h3>LogiAI Support Assistant</h3>
              <span className="cw-status">
                <span className="cw-status-dot" /> Online
              </span>
            </div>
          </div>
          <div className="cw-header-actions">
            <button onClick={closeChat} className="cw-header-btn" title="Minimize">
              <Minimize2 size={16} />
            </button>
            <button onClick={closeChat} className="cw-header-btn" title="Close">
              <X size={16} />
            </button>
          </div>
        </div>

        {/* Messages */}
        <div className="cw-messages">
          {messages.map((msg, i) => (
            <div key={i} className={`cw-msg cw-msg-${msg.sender}`}>
              {msg.sender === "bot" && (
                <div className="cw-msg-avatar">
                  <Bot size={14} />
                </div>
              )}
              <div className="cw-msg-content">
                <div className="cw-msg-bubble">
                  {msg.text.split("\n").map((line, j) => (
                    <React.Fragment key={j}>
                      {line}
                      {j < msg.text.split("\n").length - 1 && <br />}
                    </React.Fragment>
                  ))}
                </div>
                <span className="cw-msg-time">{msg.time}</span>
              </div>
              {msg.sender === "user" && (
                <div className="cw-msg-avatar cw-msg-avatar-user">
                  <User size={14} />
                </div>
              )}
            </div>
          ))}

          {loading && (
            <div className="cw-msg cw-msg-bot">
              <div className="cw-msg-avatar">
                <Bot size={14} />
              </div>
              <div className="cw-msg-content">
                <div className="cw-msg-bubble cw-typing">
                  <span /><span /><span />
                </div>
              </div>
            </div>
          )}
          <div ref={chatEndRef} />
        </div>

        {/* Quick Actions */}
        {messages.length <= 1 && (
          <div className="cw-quick-actions">
            {quickActions.map((q) => (
              <button key={q.label} className="cw-quick-btn" onClick={() => handleSend(q.msg)}>
                {q.icon} {q.label}
              </button>
            ))}
          </div>
        )}

        {/* Input */}
        <div className="cw-input-area">
          <button
            className={`cw-voice-btn ${listening ? "cw-voice-active" : ""}`}
            onClick={toggleVoice}
            title={listening ? "Stop listening" : "Voice input"}
          >
            {listening ? <MicOff size={18} /> : <Mic size={18} />}
          </button>
          
          {/* Only show upload button when waiting for damage proof */}
          {waitingForProof && (
            <>
              <button
                className={`cw-upload-btn ${uploading ? "cw-upload-active" : ""}`}
                onClick={openFileDialog}
                disabled={uploading || loading}
                title="Upload damage proof video"
              >
                <Upload size={18} />
              </button>
              <input
                ref={fileInputRef}
                type="file"
                accept="video/*,image/*"
                onChange={handleFileSelect}
                style={{ display: "none" }}
                disabled={uploading}
              />
            </>
          )}
          
          <input
            type="text"
            className="cw-order-input"
            placeholder="Order ID"
            value={orderId}
            onChange={(e) => setOrderId(e.target.value.toUpperCase())}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                e.preventDefault();
                handleSend();
              }
            }}
            maxLength={10}
          />
          <input
            ref={inputRef}
            type="text"
            className="cw-input"
            placeholder={listening ? "Listening..." : "Type your message..."}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
            disabled={loading}
          />
          <button
            className="cw-send-btn"
            onClick={() => handleSend()}
            disabled={!input.trim() || loading}
            title="Send"
          >
            <Send size={18} />
          </button>
        </div>

        {/* Footer */}
        <div className="cw-footer">
          Powered by <strong>LogiAI</strong> &middot; NLP Engine
        </div>
      </div>

      {/* Scroll-to-bottom pill (shows when chat is open & scrolled up) */}
    </>
  );
}

export default ChatWidget;
