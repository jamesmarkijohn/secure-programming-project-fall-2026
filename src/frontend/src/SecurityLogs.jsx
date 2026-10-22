import { useEffect, useState } from "react";
import { apiGet } from "./api.js";

export default function SecurityLogs() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadLogs() {
      try {
        const response = await apiGet("/api/audit/security-logs/");

        if (!response.ok) {
          setError("Could not load security logs.");
          return;
        }

        setLogs(response.data.logs);
      } catch {
        setError("Something went wrong while loading security logs.");
      } finally {
        setLoading(false);
      }
    }

    loadLogs();
  }, []);

  return (
    <section>
      <h2>Security Logs</h2>

      {loading && <p>Loading security logs...</p>}
      {error && <p role="alert">{error}</p>}

      {!loading && !error && logs.length === 0 && (
        <p>No security logs recorded yet.</p>
      )}

      {!loading && !error && logs.length > 0 && (
        <table>
          <thead>
            <tr>
              <th>Event ID</th>
              <th>User</th>
              <th>Event Type</th>
              <th>Description</th>
              <th>Date and Time</th>
            </tr>
          </thead>

          <tbody>
            {logs.map((log) => (
              <tr key={log.log_id}>
                <td>{log.log_id}</td>
                <td>{log.email}</td>
                <td>{log.event_type}</td>
                <td>{log.event_desc}</td>
                <td>{new Date(log.event_time).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}