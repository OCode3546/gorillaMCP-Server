export default function ItemList({ items, onToggle, onDelete }) {
  if (items.length === 0) {
    return <p className="empty">Nothing here yet.</p>;
  }
  return (
    <ul className="item-list">
      {items.map((item) => (
        <li key={item.id} className={item.done ? "done" : ""}>
          <input
            type="checkbox"
            checked={item.done}
            onChange={() => onToggle(item.id)}
            aria-label={`Mark "${item.text}" done`}
          />
          <span className="label">{item.text}</span>
          <button type="button" className="delete" onClick={() => onDelete(item.id)} aria-label={`Delete "${item.text}"`}>
            ×
          </button>
        </li>
      ))}
    </ul>
  );
}
