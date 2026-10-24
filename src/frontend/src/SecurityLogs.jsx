import { useCallback, useEffect, useState } from "react";
import { apiGet } from "./api.js";

function toUtc(localValue) {
  return localValue ? new Date(localValue).toISOString() : "";
}

export default function SecurityLogs() {
  const [filters, setFilters] = useState({ eventType: "", userId: "", since: "", until: "" });
  const [applied, setApplied] = useState(filters);
  const [page, setPage] = useState(1);
  const [result, setResult] = useState({ logs: [], event_types: [], total: 0, page_size: 25 });
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    const params = new URLSearchParams({ page: String(page) });
    if (applied.eventType) params.set("event_type", applied.eventType);
    if (applied.userId) params.set("user_id", applied.userId);
    if (applied.since) params.set("since", toUtc(applied.since));
    if (applied.until) params.set("until", toUtc(applied.until));
    try {
      const { ok, data } = await apiGet(`/api/audit/security-logs/?${params}`);
      if (ok) {
        setResult(data);
        setMessage("");
      } else {
        setMessage(data.error || "Could not load security logs.");
      }
    } catch {
      setMessage("Could not reach the server.");
    } finally {
      setLoading(false);
    }
  }, [applied, page]);

  useEffect(() => {
    load();
  }, [load]);

  function search(event) {
    event.preventDefault();
    setPage(1);
    setApplied({ ...filters });
  }

  function clear() {
    const empty = { eventType: "", userId: "", since: "", until: "" };
    setFilters(empty);
    setPage(1);
    setApplied(empty);
  }

  const set = (field) => (e) => setFilters({ ...filters, [field]: e.target.value });
  const lastPage = Math.max(1, Math.ceil(result.total / result.page_size));

  return (
    <section>
      <h2>Security log</h2>

      <form onSubmit={search}>
        <label>
          Event type
          <select value={filters.eventType} onChange={set("eventType")}>
            <option value="">Any event</option>
            {result.event_types.map((type) => <option key={type} value={type}>{type}</option>)}
          </select>
        </label>
        <label>
          Account ID
          <input type="number" min="1" step="1" value={filters.userId} onChange={set("userId")} />
        </label>
        <label>
          From
          <input type="datetime-local" value={filters.since} onChange={set("since")} />
        </label>
        <label>
          To
          <input type="datetime-local" value={filters.until} onChange={set("until")} />
        </label>
        <button type="submit" disabled={loading}>Search</button>
        <button type="button" onClick={clear} disabled={loading}>Clear filters</button>
      </form>

      {message && <p role="status">{message}</p>}
      {!loading && result.logs.length === 0 && !message && <p>No matching log entries.</p>}

      {result.logs.length > 0 && (
        <>
          <table>
            <thead>
              <tr>
                <th>Entry</th>
                <th>Account</th>
                <th>Event type</th>
                <th>Details</th>
                <th>Date and time</th>
              </tr>
            </thead>
            <tbody>
              {result.logs.map((log) => (
                <tr key={log.log_id}>
                  <td>{log.log_id}</td>
                  <td>{log.email} (#{log.user_id})</td>
                  <td>{log.event_type}</td>
                  <td>{log.event_desc}</td>
                  <td>{new Date(log.event_time).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p>
            <button type="button" onClick={() => setPage(page - 1)} disabled={loading || page <= 1}>
              Previous
            </button>{" "}
            Page {page} of {lastPage} ({result.total} entries){" "}
            <button type="button" onClick={() => setPage(page + 1)} disabled={loading || page >= lastPage}>
              Next
            </button>
          </p>
        </>
      )}
    </section>
  );
}