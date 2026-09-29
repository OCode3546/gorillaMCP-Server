// Front end for __APP_TITLE__: talks to the Flask JSON API.
const list = document.getElementById("items");
const form = document.getElementById("add-form");
const input = document.getElementById("title");
const errorBox = document.getElementById("error");

async function api(path, options = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
    body: options.body ? JSON.stringify(options.body) : undefined,
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.error || `Request failed (${res.status})`);
  }
  return res.status === 204 ? null : res.json();
}

function showError(err) {
  errorBox.textContent = err ? err.message : "";
  errorBox.hidden = !err;
}

async function refresh() {
  try {
    const items = await api("/api/items");
    list.replaceChildren(...items.map(renderItem));
    if (items.length === 0) {
      const li = document.createElement("li");
      li.className = "empty";
      li.textContent = "No items yet.";
      list.append(li);
    }
    showError(null);
  } catch (err) {
    showError(err);
  }
}

function renderItem(item) {
  const li = document.createElement("li");
  li.className = item.done ? "done" : "";

  const box = document.createElement("input");
  box.type = "checkbox";
  box.checked = item.done;
  box.addEventListener("change", () => api(`/api/items/${item.id}`, { method: "PATCH", body: { done: box.checked } }).then(refresh, showError));

  const label = document.createElement("span");
  label.className = "label";
  label.textContent = item.title;

  const del = document.createElement("button");
  del.type = "button";
  del.className = "delete";
  del.textContent = "×";
  del.setAttribute("aria-label", `Delete ${item.title}`);
  del.addEventListener("click", () => api(`/api/items/${item.id}`, { method: "DELETE" }).then(refresh, showError));

  li.append(box, label, del);
  return li;
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const title = input.value.trim();
  if (!title) return;
  try {
    await api("/api/items", { method: "POST", body: { title } });
    input.value = "";
    refresh();
  } catch (err) {
    showError(err);
  }
});

refresh();
