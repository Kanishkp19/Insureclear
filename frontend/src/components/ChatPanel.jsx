import React, { useState, useRef, useEffect } from "react";
import { uploadDocument, queryPipeline } from "../utils/api";

// ─── Helpers ────────────────────────────────────────────────────────────────

function ConfidenceBadge({ score }) {
  const pct = Math.round(score * 100);
  const color =
    pct >= 75 ? "#22c55e" : pct >= 45 ? "#f59e0b" : "#ef4444";
  return (
    <span
      style={{
        background: color + "22",
        color,
        border: `1px solid ${color}55`,
        borderRadius: 6,
        padding: "1px 8px",
        fontSize: 12,
        fontWeight: 600,
        marginLeft: 8,
      }}
    >
      {pct}%
    </span>
  );
}

function ClauseCard({ clause }) {
  const [open, setOpen] = useState(false);
  return (
    <div
      style={{
        background: "rgba(255,255,255,0.04)",
        border: "1px solid rgba(255,255,255,0.1)",
        borderRadius: 10,
        padding: "10px 14px",
        marginTop: 8,
        cursor: "pointer",
      }}
      onClick={() => setOpen((o) => !o)}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
        <span style={{ fontSize: 11, opacity: 0.5 }}>
          {clause.document_id} · node {clause.node_id}
        </span>
        <ConfidenceBadge score={clause.confidence_score} />
        <span style={{ marginLeft: "auto", fontSize: 13, opacity: 0.4 }}>
          {open ? "▲" : "▼"}
        </span>
      </div>
      {open && (
        <p style={{ marginTop: 8, fontSize: 13, lineHeight: 1.6, opacity: 0.85 }}>
          {clause.text}
        </p>
      )}
    </div>
  );
}

function Message({ msg }) {
  const isUser = msg.role === "user";
  const isSystem = msg.role === "system";
  return (
    <div
      style={{
        display: "flex",
        flexDirection: isUser ? "row-reverse" : "row",
        gap: 10,
        marginBottom: 16,
      }}
    >
      <div
        style={{
          width: 32,
          height: 32,
          borderRadius: "50%",
          flexShrink: 0,
          background: isUser
            ? "linear-gradient(135deg,#818cf8,#6366f1)"
            : isSystem
            ? "linear-gradient(135deg,#f59e0b,#d97706)"
            : "linear-gradient(135deg,#22d3ee,#0ea5e9)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: 14,
          fontWeight: 700,
          color: "#fff",
        }}
      >
        {isUser ? "U" : isSystem ? "!" : "AI"}
      </div>

      <div style={{ maxWidth: "75%" }}>
        {/* Meta info for AI responses */}
        {msg.domain && (
          <div style={{ fontSize: 11, opacity: 0.4, marginBottom: 4 }}>
            Domain: <strong>{msg.domain}</strong>
          </div>
        )}

        <div
          style={{
            background: isUser
              ? "linear-gradient(135deg,rgba(99,102,241,0.25),rgba(129,140,248,0.15))"
              : isSystem
              ? "rgba(245,158,11,0.12)"
              : "rgba(255,255,255,0.06)",
            border: `1px solid ${
              isUser
                ? "rgba(99,102,241,0.3)"
                : isSystem
                ? "rgba(245,158,11,0.25)"
                : "rgba(255,255,255,0.1)"
            }`,
            borderRadius: isUser ? "16px 4px 16px 16px" : "4px 16px 16px 16px",
            padding: "12px 16px",
            fontSize: 14,
            lineHeight: 1.65,
            color: isSystem ? "#f59e0b" : "inherit",
            whiteSpace: "pre-wrap",
          }}
        >
          {msg.content}
        </div>

        {/* Selected clauses accordion */}
        {msg.clauses && msg.clauses.length > 0 && (
          <div style={{ marginTop: 6 }}>
            <p style={{ fontSize: 11, opacity: 0.4, marginBottom: 2 }}>
              📌 Top clause(s) selected by Universal Selector
            </p>
            {msg.clauses.map((c, i) => (
              <ClauseCard key={i} clause={c} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// ─── Main Component ──────────────────────────────────────────────────────────

export default function ChatPanel() {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content:
        "👋 Hi! I'm powered by the Universal Selector pipeline.\n\nUpload a PDF policy or ask me any insurance question — I'll extract the most relevant clause and explain it clearly.",
    },
  ]);
  const [input, setInput] = useState("");
  const [sessionId, setSessionId] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [loading, setLoading] = useState(false);
  const [uploadedFile, setUploadedFile] = useState(null);
  const fileRef = useRef(null);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // ── Upload handler
  async function handleFileChange(e) {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setUploadedFile(file.name);
    addSystemMessage(`⏳ Processing "${file.name}"…`);

    try {
      const result = await uploadDocument(file, sessionId);
      setSessionId(result.session_id);
      addSystemMessage(
        `✅ "${file.name}" indexed — ${result.node_count} nodes ready. You can now ask questions about it.`
      );
    } catch (err) {
      addSystemMessage(`❌ Upload error: ${err.message}`);
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  }

  // ── Query handler
  async function handleSend(e) {
    e?.preventDefault();
    const question = input.trim();
    if (!question || loading) return;

    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: question }]);
    setLoading(true);

    try {
      const result = await queryPipeline(question, sessionId);
      setSessionId(result.session_id);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: result.explanation,
          domain: result.domain,
          clauses: result.selected_clauses,
        },
      ]);
    } catch (err) {
      addSystemMessage(`❌ Error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  }

  function addSystemMessage(text) {
    setMessages((prev) => [...prev, { role: "system", content: text }]);
  }

  function handleKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  // ─── Render ────────────────────────────────────────────────────────────────
  return (
    <section
      className="surface-card"
      style={{
        display: "flex",
        flexDirection: "column",
        height: "100%",
        minHeight: 540,
        maxHeight: 700,
        gap: 0,
        padding: 0,
        overflow: "hidden",
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: "16px 20px",
          borderBottom: "1px solid rgba(255,255,255,0.08)",
          display: "flex",
          alignItems: "center",
          gap: 10,
        }}
      >
        <div
          style={{
            width: 10,
            height: 10,
            borderRadius: "50%",
            background: loading ? "#f59e0b" : sessionId ? "#22c55e" : "#6366f1",
            boxShadow: `0 0 6px ${loading ? "#f59e0b" : sessionId ? "#22c55e" : "#6366f1"}`,
            transition: "background 0.3s",
          }}
        />
        <span style={{ fontWeight: 600, fontSize: 15 }}>InsureClear Chat</span>
        {uploadedFile && (
          <span
            style={{
              marginLeft: "auto",
              fontSize: 12,
              opacity: 0.55,
              background: "rgba(99,102,241,0.15)",
              border: "1px solid rgba(99,102,241,0.25)",
              borderRadius: 6,
              padding: "2px 10px",
            }}
          >
            📄 {uploadedFile}
          </span>
        )}
      </div>

      {/* Messages */}
      <div
        style={{
          flex: 1,
          overflowY: "auto",
          padding: "16px 20px",
          scrollbarWidth: "thin",
        }}
      >
        {messages.map((msg, i) => (
          <Message key={i} msg={msg} />
        ))}
        {loading && (
          <div style={{ display: "flex", gap: 10, marginBottom: 16 }}>
            <div
              style={{
                width: 32,
                height: 32,
                borderRadius: "50%",
                background: "linear-gradient(135deg,#22d3ee,#0ea5e9)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: 14,
                fontWeight: 700,
                color: "#fff",
              }}
            >
              AI
            </div>
            <div
              style={{
                background: "rgba(255,255,255,0.06)",
                border: "1px solid rgba(255,255,255,0.1)",
                borderRadius: "4px 16px 16px 16px",
                padding: "12px 18px",
                display: "flex",
                gap: 6,
                alignItems: "center",
              }}
            >
              {[0, 1, 2].map((i) => (
                <span
                  key={i}
                  style={{
                    width: 7,
                    height: 7,
                    borderRadius: "50%",
                    background: "#6366f1",
                    animation: `bounce 1.2s ${i * 0.2}s infinite ease-in-out`,
                  }}
                />
              ))}
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input Row */}
      <form
        onSubmit={handleSend}
        style={{
          borderTop: "1px solid rgba(255,255,255,0.08)",
          padding: "12px 16px",
          display: "flex",
          gap: 10,
          alignItems: "flex-end",
        }}
      >
        {/* Upload button */}
        <button
          type="button"
          title="Upload a PDF policy"
          onClick={() => fileRef.current?.click()}
          disabled={uploading}
          style={{
            width: 40,
            height: 40,
            borderRadius: 10,
            border: "1px solid rgba(255,255,255,0.15)",
            background: "rgba(255,255,255,0.05)",
            color: uploading ? "#f59e0b" : "rgba(255,255,255,0.6)",
            cursor: uploading ? "not-allowed" : "pointer",
            fontSize: 18,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            flexShrink: 0,
            transition: "all 0.2s",
          }}
        >
          {uploading ? "⏳" : "📎"}
        </button>
        <input
          ref={fileRef}
          type="file"
          accept=".pdf"
          style={{ display: "none" }}
          onChange={handleFileChange}
        />

        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask a policy question… (Shift+Enter for new line)"
          rows={1}
          style={{
            flex: 1,
            background: "rgba(255,255,255,0.05)",
            border: "1px solid rgba(255,255,255,0.12)",
            borderRadius: 12,
            padding: "10px 14px",
            color: "inherit",
            fontSize: 14,
            resize: "none",
            outline: "none",
            fontFamily: "inherit",
            lineHeight: 1.5,
          }}
        />

        <button
          type="submit"
          disabled={loading || !input.trim()}
          style={{
            width: 40,
            height: 40,
            borderRadius: 10,
            border: "none",
            background:
              loading || !input.trim()
                ? "rgba(99,102,241,0.25)"
                : "linear-gradient(135deg,#818cf8,#6366f1)",
            color: "#fff",
            cursor: loading || !input.trim() ? "not-allowed" : "pointer",
            fontSize: 18,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            flexShrink: 0,
            transition: "all 0.2s",
          }}
        >
          ➤
        </button>
      </form>

      {/* Bounce animation */}
      <style>{`
        @keyframes bounce {
          0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
          40% { transform: scale(1); opacity: 1; }
        }
      `}</style>
    </section>
  );
}
