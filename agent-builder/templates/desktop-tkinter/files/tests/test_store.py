import tempfile
import unittest
from pathlib import Path

from store import Store


class StoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "data.json"

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_add_update_delete_persist(self) -> None:
        store = Store(self.path)
        item = store.add("First", "hello")
        store.update(item.id, "Renamed", "world")

        reloaded = Store(self.path)
        self.assertEqual([i.title for i in reloaded.items], ["Renamed"])
        self.assertEqual(reloaded.items[0].body, "world")

        reloaded.delete(item.id)
        self.assertEqual(Store(self.path).items, [])

    def test_blank_title_becomes_untitled(self) -> None:
        self.assertEqual(Store(self.path).add("   ").title, "Untitled")

    def test_search_matches_title_and_body(self) -> None:
        store = Store(self.path)
        store.add("Groceries", "milk, eggs")
        store.add("Ideas", "build a game")
        self.assertEqual([i.title for i in store.search("EGGS")], ["Groceries"])
        self.assertEqual(len(store.search("")), 2)

    def test_corrupt_file_starts_empty(self) -> None:
        self.path.write_text("{not json")
        self.assertEqual(Store(self.path).items, [])


if __name__ == "__main__":
    unittest.main()
