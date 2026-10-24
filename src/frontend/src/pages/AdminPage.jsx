import { useState } from "react";
import AdminAccounts from "../AdminAccounts.jsx";
import AdminCreateAccount from "../AdminCreateAccount.jsx";
import SecurityLogs from "../SecurityLogs.jsx";
import AdminRooms from "../AdminRooms.jsx";

export default function AdminPage({ user }) {
  const [version, setVersion] = useState(0);
  return (
    <>
      <h1>Administration</h1>
      <AdminAccounts key={version} currentEmail={user.email} />
      <AdminCreateAccount onCreated={() => setVersion((v) => v + 1)} />
      <AdminRooms />
      <SecurityLogs />
    </>
  );
}