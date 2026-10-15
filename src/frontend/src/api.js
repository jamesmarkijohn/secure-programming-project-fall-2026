function getCookie(name) {
  const match = document.cookie.match(new RegExp("(?:^|; )" + name + "=([^;]*)"));
  return match ? decodeURIComponent(match[1]) : "";
}

export async function apiPost(path, body) {
  await fetch("/api/auth/csrf/", { credentials: "same-origin" });
  const response = await fetch(path, {
    method: "POST",
    credentials: "same-origin",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": getCookie("csrftoken"),
    },
    body: JSON.stringify(body),
  });
  const data = await response.json();
  return { ok: response.ok, data };
}