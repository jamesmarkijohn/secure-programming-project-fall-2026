import { useEffect, useState } from "react";
import { apiGet, apiPost } from "./api.js";

export default function RecordMove({ onRecorded }) {
  const [rooms, setRooms] = useState([]);
  const [personId, setPersonId] = useState("");
  const [roomId, setRoomId] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    apiGet("/api/gallery/rooms/")
      .then(({ ok, data }) => (ok ? setRooms(data.rooms) : setMessage("Could not load rooms.")))
      .catch(() => setMessage("Could not load rooms."));
  }, []);

  async function handleSubmit(event) {
    event.preventDefault();
    setBusy(true);
    setMessage("");
    try {
      const { ok, data } = await apiPost("/api/gallery/moves/", {
        person_id: Number(personId),
        room_id: Number(roomId),
      });
      if (ok) {
        setMessage(`Recorded: person #${data.person_id} moved from ${data.start_room} to ${data.end_room}.`);
        setPersonId("");
        onRecorded?.();
      } else {
        setMessage(data.error);
      }
    } catch {
      setMessage("Could not reach the server.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section>
      <h2>Record a movement</h2>
      <form onSubmit={handleSubmit}>
        <label>
          Person ID
          <input type="number" min="1" step="1" required
            value={personId} onChange={(e) => setPersonId(e.target.value)} />
        </label>
        <label>
          Moving to
          <select required value={roomId} onChange={(e) => setRoomId(e.target.value)}>
            <option value="">Choose a room</option>
            {rooms.map((room) => (
              <option key={room.room_id} value={room.room_id}>
                {room.name}{room.is_restricted ? " (staff only)" : ""}
              </option>
            ))}
          </select>
        </label>
        <button type="submit" disabled={busy}>Record movement</button>
      </form>
      {message && <p role="status">{message}</p>}
    </section>
  );
}