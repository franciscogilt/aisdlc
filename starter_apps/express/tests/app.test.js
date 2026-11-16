import assert from "node:assert/strict";
import { after, before, describe, test } from "node:test";

import { createApp } from "../src/app.js";
import { memoryRepo, pgRepo } from "../src/repo.js";

// Cada prueba corre contra memoria y, si hay DATABASE_URL (CI), tambien contra Postgres real.
const backends = [["memoria", async () => memoryRepo()]];
if (process.env.DATABASE_URL) {
  backends.push([
    "postgres",
    async () => {
      const repo = await pgRepo(process.env.DATABASE_URL);
      await repo.pool.query("TRUNCATE items RESTART IDENTITY");
      return repo;
    },
  ]);
}

for (const [label, makeRepo] of backends) {
  describe(label, () => {
    let server;
    let repo;
    let base;

    before(async () => {
      repo = await makeRepo();
      await new Promise((resolve) => {
        server = createApp({ repo }).listen(0, resolve);
      });
      base = `http://127.0.0.1:${server.address().port}`;
    });

    after(async () => {
      await new Promise((resolve) => server.close(resolve));
      await repo.close();
    });

    const post = (body) =>
      fetch(`${base}/items`, { method: "POST", headers: { "content-type": "application/json" }, body });

    test("GET /health", async () => {
      const r = await fetch(`${base}/health`);
      assert.equal(r.status, 200);
      assert.deepEqual(await r.json(), { status: "ok" });
    });

    test("POST /items rechaza cantidad invalida", async () => {
      assert.equal((await post(JSON.stringify({ name: "cafe", quantity: 0 }))).status, 422);
    });

    test("POST /items rechaza JSON invalido", async () => {
      assert.equal((await post("no-json")).status, 400);
    });

    test("POST /items crea un item y GET /items lo lista", async () => {
      const r = await post(JSON.stringify({ name: "cafe", quantity: 2 }));
      assert.equal(r.status, 201);
      assert.deepEqual(await r.json(), { id: 1, name: "cafe", quantity: 2 });
      const list = await (await fetch(`${base}/items`)).json();
      assert.deepEqual(list, [{ id: 1, name: "cafe", quantity: 2 }]);
    });
  });
}
