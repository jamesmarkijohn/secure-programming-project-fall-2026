import { useCallback, useEffect, useState } from "react";
import { apiGet, apiPost } from "./api.js";

function toUtc(localValue) {
  return localValue ? new Date(localValue).toISOString() : "";
}

export default function MovementHistory({ canDelete = false }) {
  const [rooms, setRooms] = useState([]);
  const [filters, setFilters] = useState({ personId: "", roomId: "", since: "", until: "" });
  const [applied, setApplied] = useState(filters); // the filters the results reflect
  const [page, setPage] = useState(1);
  const [result, setResult] = useState({ events: [], total: 0, page_size: 25 });
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");

  useEffect(() => {
    apiGet("/api/gallery/rooms/").then(({ ok, data }) => ok && setRooms(data.rooms)).catch(() => {});
  }, []);

  const load = useCallback(async () => {
    setLoading(true);
    const params = new URLSearchParams({ page: String(page) });
    if (applied.personId) params.set("person_id", applied.personId);
    if (applied.roomId) params.set("room_id", applied.roomId);
    if (applied.since) params.set("since", toUtc(applied.since));
    if (applied.until) params.set("until", toUtc(applied.until));
    try {
      const { ok, data } = await apiGet(`/api/gallery/movement-history/?${params}`);
      if (ok) {
        setResult(data);
        setMessage("");
      } else {
        setMessage(data.error || "Could not load movement history.");
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
    const empty = { personId: "", roomId: "", since: "", until: "" };
    setFilters(empty);
    setPage(1);
    setApplied(empty);
  }

  async function deleteEvent(event) {
    const summary = `#${event.event_id}: ${event.email}, ${event.start_room} to ${event.end_room}`;
    if (!window.confirm(`Delete movement event ${summary}? This cannot be undone.`)) return;
    try {
      const { ok, data } = await apiPost(`/api/gallery/events/${event.event_id}/delete/`, {});
      setMessage(ok ? `Deleted event #${event.event_id}.` : data.error);
      if (ok) load();
    } catch {
      setMessage("Could not reach the server.");
    }
  }

  const set = (field) => (e) => setFilters({ ...filters, [field]: e.target.value });
  const lastPage = Math.max(1, Math.ceil(result.total / result.page_size));

  return (
    <section>
      <h2>Movement history</h2>

      <form onSubmit={search}>
        <label>
          Person ID
          <input type="number" min="1" step="1" value={filters.personId} onChange={set("personId")} />
        </label>
        <label>
          Room
          <select value={filters.roomId} onChange={set("roomId")}>
            <option value="">Any room</option>
            {rooms.map((room) => (
              <option key={room.room_id} value={room.room_id}>{room.name}</option>
            ))}
          </select>
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

      {!loading && result.events.length === 0 && !message && <p>No matching movement events.</p>}

      {result.events.length > 0 && (
        <>
          <table>
            <thead>
              <tr>
                <th>Event</th>
                <th>Person</th>
                <th>From</th>
                <th>To</th>
                <th>Date and time</th>
                <th>Recorded by</th>
                {canDelete && <th>Action</th>}
              </tr>
            </thead>
            <tbody>
              {result.events.map((event) => (
                <tr key={event.event_id}>
                  <td>{event.event_id}</td>
                  <td>{event.email} (#{event.user_id})</td>
                  <td>{event.start_room}</td>
                  <td>{event.end_room}</td>
                  <td>{new Date(event.event_time).toLocaleString()}</td>
                  <td>{event.recorded_by}</td>
                  {canDelete && (
                    <td>
                      <button type="button" onClick={() => deleteEvent(event)}>Delete</button>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>

          <p>
            <button type="button" onClick={() => setPage(page - 1)} disabled={loading || page <= 1}>
              Previous
            </button>{" "}
            Page {page} of {lastPage} ({result.total} events){" "}
            <button type="button" onClick={() => setPage(page + 1)} disabled={loading || page >= lastPage}>
              Next
            </button>
          </p>
        </>
      )}
    </section>
  );
}