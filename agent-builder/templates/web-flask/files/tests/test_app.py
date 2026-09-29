import tempfile
import unittest
from pathlib import Path

from app import create_app


class ApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        app = create_app(str(Path(self.tmp.name) / "test.db"))
        app.testing = True
        self.client = app.test_client()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_index_page(self) -> None:
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"__APP_TITLE__", res.data)

    def test_crud_flow(self) -> None:
        created = self.client.post("/api/items", json={"title": "Write tests"})
        self.assertEqual(created.status_code, 201)
        item = created.get_json()
        self.assertEqual(item["title"], "Write tests")
        self.assertFalse(item["done"])

        updated = self.client.patch(f"/api/items/{item['id']}", json={"done": True}).get_json()
        self.assertTrue(updated["done"])

        self.assertEqual(len(self.client.get("/api/items").get_json()), 1)
        self.assertEqual(self.client.delete(f"/api/items/{item['id']}").status_code, 204)
        self.assertEqual(self.client.get("/api/items").get_json(), [])

    def test_validation_and_404(self) -> None:
        self.assertEqual(self.client.post("/api/items", json={"title": "  "}).status_code, 400)
        missing = self.client.patch("/api/items/999", json={"done": True})
        self.assertEqual(missing.status_code, 404)
        self.assertEqual(missing.get_json(), {"error": "Item not found"})


if __name__ == "__main__":
    unittest.main()
