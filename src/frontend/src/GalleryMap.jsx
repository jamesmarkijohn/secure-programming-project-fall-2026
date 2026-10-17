import { useEffect, useState } from "react";

const ROOMS = [
  { name: "Storage",         x: 65,  y: 15,  w: 240, h: 160, restricted: true },
  { name: "Portrait Hall",   x: 341, y: 15,  w: 90,  h: 246, label: ["Portrait", "Hall"] },
  { name: "Exhibit Hall",    x: 471, y: 15,  w: 140, h: 246 },
  { name: "Sculptures",      x: 625, y: 15,  w: 213, h: 113 },
  { name: "Modern Art",      x: 65,  y: 197, w: 240, h: 64 },
  { name: "Local Art",       x: 625, y: 154, w: 97,  h: 107 },
  { name: "Lecture Hall",    x: 741, y: 154, w: 97,  h: 107, label: ["Lecture", "Hall"] },
  { name: "Main Hall",       x: 65,  y: 283, w: 773, h: 113 },
  { name: "Security Office", x: 105, y: 441, w: 214, h: 67,  restricted: true },
  { name: "Lobby",           x: 372, y: 441, w: 159, h: 128 },
  { name: "Staff Offices",   x: 571, y: 441, w: 176, h: 128, restricted: true },
];

export default function GalleryMap({ role }) {
  const isStaff = role === "EMPLOYEE" || role === "ADMIN";
  const [current, setCurrent] = useState(null);
  const [occupancy, setOccupancy] = useState(null); // staff only
  const [error, setError] = useState("");

  useEffect(() => {
    fetch("/api/gallery/my-location/", { credentials: "same-origin" })
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then((data) => setCurrent(data.room))
      .catch(() => setError("Could not load your location."));

    if (isStaff) {
      fetch("/api/gallery/occupancy/", { credentials: "same-origin" })
        .then((r) => (r.ok ? r.json() : Promise.reject()))
        .then((data) => setOccupancy(data.rooms))
        .catch(() => setError("Could not load occupancy."));
    }
  }, [isStaff]);

  return (
    <section>
      <h2>Gallery map</h2>
      {error && <p role="status">{error}</p>}
      {current === "Outside" && <p>You are outside the gallery.</p>}
      {current && current !== "Outside" && <p>You are in: {current}</p>}

      <svg viewBox="50 0 810 590" width="100%" role="img" aria-label="Gallery floor plan">
        {ROOMS.map((room) => {
          const here = room.name === current;
          const lines = room.label || [room.name];
          const count = occupancy ? (occupancy[room.name] || []).length : null;
          const cx = room.x + room.w / 2;
          const cy = room.y + room.h / 2 - ((lines.length - 1) * 9) - (count !== null ? 9 : 0);
          return (
            <g key={room.name}>
              <rect x={room.x} y={room.y} width={room.w} height={room.h}
                fill={here ? "#f2c14e" : room.restricted ? "#e3e3e3" : "#cfe0f1"}
                stroke="#333" strokeWidth={here ? 3 : 1}
                strokeDasharray={room.restricted ? "6 4" : undefined} />
              <text x={cx} y={cy} textAnchor="middle" dominantBaseline="middle"
                fontSize="15" fill="#222">
                {lines.map((line, i) => (
                  <tspan key={line} x={cx} dy={i === 0 ? 0 : 18}>{line}</tspan>
                ))}
                {count !== null && (
                  <tspan x={cx} dy={20} fontSize="13" fill="#555">
                    {count} {count === 1 ? "person" : "people"}
                  </tspan>
                )}
              </text>
            </g>
          );
        })}
      </svg>
      <p>Dashed grey rooms are staff-only.</p>

      {occupancy && (
        <div>
          <h3>Who is where</h3>
          <ul>
            {Object.entries(occupancy)
              .filter(([, people]) => people.length > 0)
              .map(([roomName, people]) => (
                <li key={roomName}>
                  {roomName}: {people.map((p) => `${p.email} (#${p.user_id}, ${p.role})`).join(", ")}
                </li>
              ))}
          </ul>
        </div>
      )}
    </section>
  );
}