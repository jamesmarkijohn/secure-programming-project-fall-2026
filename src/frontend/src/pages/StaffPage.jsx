import { useState } from "react";
import GalleryMap from "../GalleryMap.jsx";
import MovementHistory from "../MovementHistory.jsx";
import RecordMove from "../RecordMove.jsx";

export default function StaffPage({ user }) {
  const [version, setVersion] = useState(0);
  return (
    <>
      <h1>Staff</h1>
      <RecordMove onRecorded={() => setVersion((v) => v + 1)} />
      <GalleryMap key={`map-${version}`} role={user.role} />
      <MovementHistory key={`history-${version}`} canDelete={user.role === "ADMIN"} />
    </>
  );
}