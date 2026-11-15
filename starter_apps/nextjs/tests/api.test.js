import assert from "node:assert/strict";
import { test } from "node:test";

import { GET } from "../app/health/route.js";
import { POST } from "../app/items/route.js";

const post = (body) =>
  POST(new Request("http://localhost/items", { method: "POST", headers: { "content-type": "application/json" }, body }));

test("GET /health", async () => {
  const r = GET();
  assert.equal(r.status, 200);
  assert.deepEqual(await r.json(), { status: "ok" });
});

test("POST /items crea un item", async () => {
  const r = await post(JSON.stringify({ name: "cafe", quantity: 2 }));
  assert.equal(r.status, 201);
  assert.deepEqual(await r.json(), { name: "cafe", quantity: 2 });
});

test("POST /items rechaza cantidad invalida", async () => {
  const r = await post(JSON.stringify({ name: "cafe", quantity: 0 }));
  assert.equal(r.status, 422);
});

test("POST /items rechaza JSON invalido", async () => {
  const r = await post("no-json");
  assert.equal(r.status, 400);
});
