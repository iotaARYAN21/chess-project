import React, { useState, useEffect } from "react";
import "./adminlogs.css";
import { useNavigate } from "react-router-dom";

const AdminLogs = () => {
  const [logs, setLogs] = useState([]); // store cheat logs
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedLog, setSelectedLog] = useState(null); // Track log for modal
  const [banDuration, setBanDuration] = useState("permanent");
  const [resolving, setResolving] = useState(false);
  const [resolveError, setResolveError] = useState("");
  const [banReason, setBanReason] = useState("");

  const navigate = useNavigate();

  useEffect(() => {
    async function fetchLogs() {
      try {
        const res = await fetch("http://localhost:8000/admin/cheat-logs", {
          method: "GET",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${localStorage.getItem("token")}`,
          },
        });

        const data = await res.json();

        if (!res.ok) {
          setError(data.detail || "Failed to fetch logs");
          return;
        }

        setLogs(data);
      } catch (err) {
        setError("Something went wrong");
      } finally {
        setLoading(false);
      }
    }

    fetchLogs();
  }, []); // runs once when component mounts

  const handleResolve = async () => {
    if (!selectedLog) return;
    setResolving(true);
    setResolveError("");

    console.log(
      "Resolving log:",
      selectedLog,
      "with ban duration:",
      banDuration,
    );

    try {
      const res = await fetch("http://localhost:8000/admin/anticheat-resolve", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          log_id: selectedLog.id,
          account_id: selectedLog.user_id,
          ban_type: banDuration,
          reason:
            banReason || `Admin resolved via dashboard - ${banDuration} ban`,
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        setResolveError(data.detail || "Failed to resolve log");
        return;
      }

      // Mark log as resolved in local state - no refetch needed
      setLogs((prev) =>
        prev.map((log) =>
          log.id === selectedLog.id
            ? {
                ...log,
                resolved: true,
                ban_type: data.ban_type,
                expires_at: data.expires_at,
              }
            : log,
        ),
      );

      setSelectedLog(null);
      setBanDuration("permanent");
    } catch {
      setResolveError("Network error - please try again");
    } finally {
      setResolving(false);
    }
  };

  return (
    <div className="lobby">
      <div className="lobby-intro">
        <h1>Cheat Logs</h1>
        <p>Monitor suspicious player activity</p>
      </div>

      {loading && <p>Loading...</p>}
      {error && <p style={{ color: "red" }}>{error}</p>}

      <div className="logs-container">
        {/* Header */}
        <div className="log-header">
          <div>Username</div>
          <div>Score</div>
          <div>Time</div>
          <div>Resolved By</div>
          <div>Resolved At</div>
          <div>Status</div>
          <div>Actions</div>
        </div>

        {/* Rows */}
        {logs.length > 0 ? (
          logs.map(
            (log) => (
              console.log(log),
              (
                <div key={log.id} className="log-row">
                  <div className="log-user">{log.username}</div>
                  <div className="log-score">{log.sus_score}</div>
                  <div className="log-time">
                    {new Date(log.added_at).toLocaleString()}
                  </div>

                  <div className="log-admin">
                    {log.resolved ? log.resolver_username : "-"}
                  </div>

                  <div className="log-time">
                    {log.resolved && log.resolved_at
                      ? new Date(log.resolved_at).toLocaleString()
                      : "-"}
                  </div>

                  <div className={`log-status ${log.resolved ? "yes" : "no"}`}>
                    {log.resolved ? "Yes" : "No"}
                  </div>
                  <div className="log-actions">
                    <button
                      className="btn-view"
                      onClick={() => navigate(`/replay/${log.match_id}`)}
                    >
                      View Game
                    </button>
                    {!log.resolved && (
                      <button
                        className="btn-action"
                        onClick={() => {
                          setSelectedLog(log);
                          setResolveError("");
                        }}
                      >
                        Take Action
                      </button>
                    )}
                  </div>
                </div>
              )
            ),
          )
        ) : (
          <div className="log-empty">
            <p>No suspicious activity logs found.</p>
          </div>
        )}
      </div>

      {/* Action Modal */}
      {selectedLog && (
        <div className="modal-overlay">
          <div className="modal-content">
            <h3>Action for {selectedLog.username}</h3>
            <p>Score: {selectedLog.sus_score}</p>

            <div className="modal-group">
              <label>Ban Duration</label>
              <select
                value={banDuration}
                onChange={(e) => setBanDuration(e.target.value)}
                disabled={resolving}
              >
                <option value="none">No Ban</option>
                <option value="24h">24 Hours</option>
                <option value="7d">7 Days</option>
                <option value="permanent">Permanent</option>
              </select>
            </div>

            <div className="modal-group">
              <label>Reason for Action</label>
              <textarea
                placeholder="Enter reason for ban if applicable..."
                value={banReason}
                onChange={(e) => setBanReason(e.target.value)}
                disabled={resolving}
                rows={3}
              />
            </div>

            {resolveError && <p className="modal-error">{resolveError}</p>}

            <div className="modal-buttons">
              <button
                className="btn-cancel"
                onClick={() => {
                  setSelectedLog(null);
                  setResolveError("");
                }}
                disabled={resolving}
              >
                Cancel
              </button>
              <button
                className="btn-confirm"
                onClick={handleResolve}
                disabled={resolving}
              >
                {resolving ? "Resolving" : "Confirm & Resolve"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminLogs;
