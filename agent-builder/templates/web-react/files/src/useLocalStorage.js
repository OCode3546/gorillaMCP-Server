import { useEffect, useState } from "react";

/** useState that persists to localStorage (falls back to memory if storage is unavailable). */
export function useLocalStorage(key, initialValue) {
  const [value, setValue] = useState(() => {
    try {
      const stored = localStorage.getItem(key);
      return stored !== null ? JSON.parse(stored) : initialValue;
    } catch {
      return initialValue;
    }
  });

  useEffect(() => {
    try {
      localStorage.setItem(key, JSON.stringify(value));
    } catch {
      // ignore: private mode or quota exceeded
    }
  }, [key, value]);

  return [value, setValue];
}
