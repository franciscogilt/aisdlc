import json

from django.test import TestCase


class ApiTests(TestCase):
    def post(self, payload):
        return self.client.post("/items", data=json.dumps(payload), content_type="application/json")

    def test_health(self):
        r = self.client.get("/health")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), {"status": "ok"})

    def test_create_item(self):
        r = self.post({"name": "cafe", "quantity": 2})
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.json()["name"], "cafe")
        self.assertEqual(self.client.get("/items").json(), [{"id": r.json()["id"], "name": "cafe", "quantity": 2}])

    def test_rejects_invalid_quantity(self):
        self.assertEqual(self.post({"name": "cafe", "quantity": 0}).status_code, 422)
        self.assertEqual(self.client.get("/items").json(), [])

    def test_rejects_invalid_json(self):
        r = self.client.post("/items", data="no-json", content_type="application/json")
        self.assertEqual(r.status_code, 400)

    def test_health_rejects_post(self):
        self.assertEqual(self.client.post("/health").status_code, 405)
