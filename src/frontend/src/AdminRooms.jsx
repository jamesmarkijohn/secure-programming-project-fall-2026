import { useCallback, useEffect, useState } from "react";
import { apiGet, apiPost } from "./api.js";

export default function AdminRooms() {
  const [rooms, setRooms] = useState([]);
  const [connections, setConnections] = useState([]);
  const [pair, setPair] = useState({ a: "", b: "" });
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    try {
      const { ok, data } = await apiGet("/api/admin/rooms/");
      if (ok) {
        setRooms(data.rooms);
        setConnections(data.connections);
      } else {
        setMessage(data.error || "Could not load rooms.");
      }
    } catch {
      setMessage("Could not reach the server.");
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function run(path, body, success) {
    setBusy(true);
    setMessage("");
    try {
      const { ok, data } = await apiPost(path, body);
      setMessage(ok ? success : data.error);
      if (ok) await load();
    } catch {
      setMessage("Could not reach the server.");
    } finally {
      setBusy(false);
    }
  }

  function toggleRestricted(room) {
    run(`/api/admin/rooms/${room.room_id}/update/`, { is_restricted: !room.is_restricted },
      `${room.name} is now ${room.is_restricted ? "open to guests" : "staff-only"}.`);
  }

  function disconnect(c) {
    if (!window.confirm(`Close the connection between ${c.room_a.name} and ${c.room_b.name}?`)) return;
    run("/api/admin/rooms/disconnect/", { room_a_id: c.room_a.room_id, room_b_id: c.room_b.room_id },
      `Closed ${c.room_a.name} – ${c.room_b.name}.`);
  }

  function connect(event) {
    event.preventDefault();
    run("/api/admin/rooms/connect/", { room_a_id: Number(pair.a), room_b_id: Number(pair.b) }, "Rooms connected.");
  }

  return (
    <section>
      <h2>Rooms</h2>
      {message && <p role="status">{message}</p>}

      <table>
        <thead>
          <tr>
            <th>Room</th>
            <th>People inside</th>
            <th>Access</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          {rooms.map((room) => (
            <tr key={room.room_id}>
              <td>{room.name}</td>
              <td>{room.occupants}</td>
              <td>{room.is_restricted ? "Staff only" : "Open"}</td>
              <td>
                {room.name !== "Outside" && (
                  <button type="button" disabled={busy} onClick={() => toggleRestricted(room)}>
                    {room.is_restricted ? "Open to guests" : "Make staff-only"}
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <h3>Connections</h3>
      <ul>
        {connections.map((c) => (
          <li key={`${c.room_a.room_id}-${c.room_b.room_id}`}>
            {c.room_a.name} – {c.room_b.name}{" "}
            <button type="button" disabled={busy} onClick={() => disconnect(c)}>Close</button>
          </li>
        ))}
      </ul>

      <form onSubmit={connect}>
        <label>
          Connect
          <select required value={pair.a} onChange={(e) => setPair({ ...pair, a: e.target.value })}>
            <option value="">Choose a room</option>
            {rooms.map((r) => <option key={r.room_id} value={r.room_id}>{r.name}</option>)}
          </select>
        </label>
        <label>
          to
          <select required value={pair.b} onChange={(e) => setPair({ ...pair, b: e.target.value })}>
            <option value="">Choose a room</option>
            {rooms.map((r) => <option key={r.room_id} value={r.room_id}>{r.name}</option>)}
          </select>
        </label>
        <button type="submit" disabled={busy}>Open connection</button>
      </form>
    </section>
  );
}