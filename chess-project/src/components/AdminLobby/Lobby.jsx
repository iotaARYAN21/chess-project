import React, { useState, useEffect } from "react";
import "./lobby.css";
import { useNavigate } from "react-router-dom";

const AdminLobby = () => {
  const [logs, setLogs] = useState([]); // store cheat logs
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

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
          </div>
        ))}
      </div>
    </div>
  );
};

export default AdminLobby;
