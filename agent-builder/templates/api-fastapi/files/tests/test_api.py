import unittest

from fastapi.testclient import TestClient

import main


class ApiTests(unittest.TestCase):
    def setUp(self) -> None:
        main.repo = main.Repository()  # fresh storage per test
        self.client = TestClient(main.app)

    def test_health(self) -> None:
        self.assertEqual(self.client.get("/health").json(), {"status": "ok"})

    def test_crud_flow(self) -> None:
        res = self.client.post("/items", json={"name": "Widget", "price": 9.5})
        self.assertEqual(res.status_code, 201)
        item = res.json()
        self.assertEqual(item["name"], "Widget")

        res = self.client.patch(f"/items/{item['id']}", json={"price": 12})
        self.assertEqual(res.json()["price"], 12)
        self.assertEqual(res.json()["name"], "Widget")

        self.assertEqual(len(self.client.get("/items").json()), 1)
        self.assertEqual(self.client.delete(f"/items/{item['id']}").status_code, 204)
        self.assertEqual(self.client.get(f"/items/{item['id']}").status_code, 404)

    def test_validation(self) -> None:
        self.assertEqual(self.client.post("/items", json={"name": "", "price": 1}).status_code, 422)
        self.assertEqual(self.client.post("/items", json={"name": "x", "price": -1}).status_code, 422)


if __name__ == "__main__":
    unittest.main()
