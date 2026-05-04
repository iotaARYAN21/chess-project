import React, { useState, useEffect } from "react";
import "./adminbans.css";

const AdminBans = () => {
  const [logs, setLogs] = useState([]); // store cheat logs
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function fetchLogs() {
      try {
        const res = await fetch("http://localhost:8000/admin/bans", {
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
  }, [] ); // runs once when component mounts

  // console.log('Current Role :',localStorage.getItem("admin_level"));

  return (
    <div className="lobby">
      <div className="lobby-intro">
        <h1>Bans</h1>
        <p>View and manage all bans</p>
      </div>
      {loading && <p>Loading...</p>}
      {error && <p style={{ color: "red" }}>{error}</p>}

      <div className="logs-container">
        {/* Header */}
        <div className="log-header">
          <div>Username</div>
          <div>Banned by</div>
          <div>Ban Type</div>
          <div>Reason</div>
          <div>Created at</div>
          <div>Expires at</div>
        </div>

        {/* Rows */}
        {logs.length > 0 ? (
          logs.map(
            (log) => (
              (
                <div key={log.id} className="log-row">
                  <div className="log-user">{log.username}</div>
                  <div className="log-score">{log.admin_username}</div>
                  <div className="log-ban-type">{log.ban_type}</div>
                  <div className="log-reason">{log.reason}</div>
                  <div className="log-time">
                    {new Date(log.created_at).toLocaleString()}
                  </div>
                  <div className="log-time">
                    {log.expires_at
                      ? new Date(log.expires_at).toLocaleString()
                      : "-"}
                  </div>
                </div>
              )
            ),
          )
        ) : (
          <div className="log-empty">
            <p>No suspicious Bans found.</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default AdminBans;
