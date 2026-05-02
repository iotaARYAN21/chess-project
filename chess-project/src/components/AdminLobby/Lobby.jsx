import React, { useState, useEffect } from "react";
import "./lobby.css";
import { useNavigate } from "react-router-dom";

const AdminLobby = () => {
  const [logs, setLogs] = useState([]); // store cheat logs
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedLog, setSelectedLog] = useState(null); // Track log for modal
  const [banDuration, setBanDuration] = useState("permanent");

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

  const handleResolve = (logId, action) => {
    console.log(
      `Action: ${action} for Log: ${logId} with Duration: ${banDuration}`,
    );
    // Add your fetch call here to update the DB
    setSelectedLog(null); // Close modal
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
          <div>Resolved</div>
          <div></div>
        </div>

        {/* Rows */}
        {logs.map((log) => (
          <div key={log.id} className="log-row">
            <div className="log-user">{log.username}</div>

            <div className="log-score">{log.sus_score}</div>

            <div className="log-time">
              {new Date(log.added_at).toLocaleString()}
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
                  onClick={() => setSelectedLog(log)}
                >
                  Take Action
                </button>
              )}
            </div>
          </div>
        ))}

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
                >
                  <option value="none">No Ban (Warning)</option>
                  <option value="24h">24 Hours</option>
                  <option value="7d">7 Days</option>
                  <option value="permanent">Permanent</option>
                </select>
              </div>

              <div className="modal-buttons">
                <button
                  className="btn-cancel"
                  onClick={() => setSelectedLog(null)}
                >
                  Cancel
                </button>
                <button
                  className="btn-confirm"
                  onClick={() => handleResolve(selectedLog.id, "resolved")}
                >
                  Confirm & Resolve
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AdminLobby;
