// __APP_TITLE__ — app logic. State is kept in memory and persisted to localStorage.
(() => {
  const STORAGE_KEY = "__APP_NAME__:items";

  const newId = () =>
    crypto.randomUUID ? crypto.randomUUID() : Date.now().toString(36) + Math.random().toString(36).slice(2);

  const state = {
    items: load(),
    filter: "all",
  };

  const form = document.getElementById("add-form");
  const input = document.getElementById("new-item");
  const list = document.getElementById("item-list");
  const counter = document.getElementById("counter");
  const clearDone = document.getElementById("clear-done");
  const filterButtons = document.querySelectorAll("[data-filter]");

  function load() {
    try {
      return JSON.parse(localStorage.getItem(STORAGE_KEY)) || [];
    } catch {
      return [];
    }
  }

  function save() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state.items));
    } catch {
      // Storage can be unavailable (private mode); the app still works in memory.
    }
  }

  function addItem(text) {
    state.items.push({ id: newId(), text, done: false, created: Date.now() });
    save();
    render();
  }

  function toggleItem(id) {
    const item = state.items.find((i) => i.id === id);
    if (item) item.done = !item.done;
    save();
    render();
  }

  function deleteItem(id) {
    state.items = state.items.filter((i) => i.id !== id);
    save();
    render();
  }

  function visibleItems() {
    if (state.filter === "open") return state.items.filter((i) => !i.done);
    if (state.filter === "done") return state.items.filter((i) => i.done);
    return state.items;
  }

  function render() {
    list.replaceChildren();
    const items = visibleItems();

    if (items.length === 0) {
      const empty = document.createElement("li");
      empty.className = "empty";
      empty.textContent = "Nothing here yet.";
      list.append(empty);
    }

    for (const item of items) {
      const li = document.createElement("li");
      li.className = item.done ? "done" : "";

      const checkbox = document.createElement("input");
      checkbox.type = "checkbox";
      checkbox.checked = item.done;
      checkbox.setAttribute("aria-label", `Mark "${item.text}" done`);
      checkbox.addEventListener("change", () => toggleItem(item.id));

      const label = document.createElement("span");
      label.className = "label";
      label.textContent = item.text;

      const del = document.createElement("button");
      del.className = "delete";
      del.type = "button";
      del.textContent = "×";
      del.setAttribute("aria-label", `Delete "${item.text}"`);
      del.addEventListener("click", () => deleteItem(item.id));

      li.append(checkbox, label, del);
      list.append(li);
    }

    const open = state.items.filter((i) => !i.done).length;
    counter.textContent = `${open} open · ${state.items.length} total`;
    filterButtons.forEach((b) => b.classList.toggle("active", b.dataset.filter === state.filter));
  }

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const text = input.value.trim();
    if (!text) return;
    addItem(text);
    input.value = "";
    input.focus();
  });

  filterButtons.forEach((button) =>
    button.addEventListener("click", () => {
      state.filter = button.dataset.filter;
      render();
    })
  );

  clearDone.addEventListener("click", () => {
    state.items = state.items.filter((i) => !i.done);
    save();
    render();
  });


  // ---- Desktop integrations via the preload bridge (window.api) ----
  document.getElementById("export").addEventListener("click", async () => {
    const text = state.items.map((i) => `${i.done ? "[x]" : "[ ]"} ${i.text}`).join("\n");
    const result = await window.api.saveText("__APP_NAME__.txt", text);
    if (result.saved) counter.textContent = `Exported to ${result.filePath}`;
  });

  window.api.getInfo().then((info) => {
    document.getElementById("about").textContent =
      `${info.name} v${info.version} · Electron ${info.electron} · ${info.platform}`;
  });

  render();
})();
