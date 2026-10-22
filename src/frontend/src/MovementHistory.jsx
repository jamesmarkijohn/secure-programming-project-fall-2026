import { useEffect, useState } from "react";
import { apiGet } from "./api.js";

export default function MovementHistory() {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadHistory() {
      try {
        const response = await apiGet("/api/gallery/movement-history/");

        if (!response.ok) {
          setError("Could not load movement history.");
          return;
        }

        setEvents(response.data.events);
      } catch {
        setError("Something went wrong while loading movement history.");
      } finally {
        setLoading(false);
      }
    }

    loadHistory();
  }, []);

  return (
    <section>
      <h2>Movement History</h2>

      {loading && <p>Loading movement history...</p>}
      {error && <p role="alert">{error}</p>}

      {!loading && !error && events.length === 0 && (
        <p>No movement events recorded yet.</p>
      )}

      {!loading && !error && events.length > 0 && (
        <table>
          <thead>
            <tr>
              <th>Person</th>
              <th>From</th>
              <th>To</th>
              <th>Date and Time</th>
              <th>Recorded By</th>
            </tr>
          </thead>
          <tbody>
            {events.map((event) => (
              <tr key={event.event_id}>
                <td>{event.email}</td>
                <td>{event.start_room}</td>
                <td>{event.end_room}</td>
                <td>{new Date(event.event_time).toLocaleString()}</td>
                <td>{event.recorded_by}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}