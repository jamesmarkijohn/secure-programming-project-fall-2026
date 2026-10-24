import DeleteAccount from "../DeleteAccount.jsx";
import GalleryMap from "../GalleryMap.jsx";
import Profile from "../Profile.jsx";

export default function HomePage({ user, onDeleted }) {
  return (
    <>
      <h1>Welcome</h1>
      <Profile />
      {/* role="GUEST" here so the home map only ever shows the user's own location */}
      <GalleryMap role="GUEST" />
      {user.role === "GUEST" && <DeleteAccount onDeleted={onDeleted} />}
    </>
  );
}