function getCookie(name) {
  const match = document.cookie.match(new RegExp("(?:^|; )" + name + "=([^;]*)"));
  return match ? decodeURIComponent(match[1]) : "";
}

//Function to make a POST request to the API with CSRF protection
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
// Function to get data from the API
export async function apiGet(path) {
  const response = await fetch(path, {
    method: "GET",
    credentials: "same-origin",
  });

  const data = await response.json();
  return { ok: response.ok, data };
}