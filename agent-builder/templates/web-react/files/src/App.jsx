import { useMemo, useState } from "react";
import ItemList from "./components/ItemList.jsx";
import { useLocalStorage } from "./useLocalStorage.js";

// crypto.randomUUID only exists in secure contexts (https, localhost, file).
const newId = () =>
  crypto.randomUUID ? crypto.randomUUID() : Date.now().toString(36) + Math.random().toString(36).slice(2);

const FILTERS = {
  all: () => true,
  open: (item) => !item.done,
  done: (item) => item.done,
};

export default function App() {
  const [items, setItems] = useLocalStorage("__APP_NAME__:items", []);
  const [draft, setDraft] = useState("");
  const [filter, setFilter] = useState("all");

  const visible = useMemo(() => items.filter(FILTERS[filter]), [items, filter]);
  const openCount = items.filter((i) => !i.done).length;

  function addItem(event) {
    event.preventDefault();
    const text = draft.trim();
    if (!text) return;
    setItems([...items, { id: newId(), text, done: false }]);
    setDraft("");
  }

  const toggleItem = (id) => setItems(items.map((i) => (i.id === id ? { ...i, done: !i.done } : i)));
  const deleteItem = (id) => setItems(items.filter((i) => i.id !== id));

  return (
    <main className="container">
      <header>
        <h1>__APP_TITLE__</h1>
        <p className="subtitle">__APP_DESCRIPTION__</p>
      </header>

      <form className="add-form" onSubmit={addItem}>
        <input value={draft} onChange={(e) => setDraft(e.target.value)} placeholder="Add an item…" aria-label="New item" />
        <button type="submit">Add</button>
      </form>

      <nav className="filters" aria-label="Filter items">
        {Object.keys(FILTERS).map((name) => (
          <button key={name} type="button" className={filter === name ? "active" : ""} onClick={() => setFilter(name)}>
            {name[0].toUpperCase() + name.slice(1)}
          </button>
        ))}
      </nav>

      <ItemList items={visible} onToggle={toggleItem} onDelete={deleteItem} />

      <footer>
        <span>
          {openCount} open · {items.length} total
        </span>
        <button type="button" className="link" onClick={() => setItems(items.filter((i) => !i.done))}>
          Clear completed
        </button>
      </footer>
    </main>
  );
}
