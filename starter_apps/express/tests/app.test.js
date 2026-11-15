import assert from "node:assert/strict";
import { after, before, test } from "node:test";

import { createApp } from "../src/app.js";

let server;
let base;

before(async () => {
  await new Promise((resolve) => {
    server = createApp().listen(0, resolve);
  });
  base = `http://127.0.0.1:${server.address().port}`;
});

after(() => new Promise((resolve) => server.close(resolve)));

const post = (body) =>
  fetch(`${base}/items`, { method: "POST", headers: { "content-type": "application/json" }, body });

test("GET /health", async () => {
  const r = await fetch(`${base}/health`);
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
