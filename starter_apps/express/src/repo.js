// Almacenamiento de items. Con DATABASE_URL usa Postgres; sin ella, memoria (desarrollo y pruebas).
import { readdir, readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";

import pg from "pg";

const MIGRATIONS = fileURLToPath(new URL("../migrations/", import.meta.url));

export function memoryRepo() {
  const items = [];
  return {
    async add(name, quantity) {
      const item = { id: items.length + 1, name, quantity };
      items.push(item);
      return item;
    },
    async list() {
      return [...items];
    },
    async close() {},
  };
}

export async function pgRepo(connectionString) {
  const pool = new pg.Pool({ connectionString });
  // Aplica migrations/*.sql en orden, una vez cada una. El lock evita carreras entre replicas.
  const client = await pool.connect();
  try {
    await client.query("BEGIN");
    await client.query("SELECT pg_advisory_xact_lock(727274)");
    await client.query("CREATE TABLE IF NOT EXISTS schema_migrations (name TEXT PRIMARY KEY)");
    const done = new Set((await client.query("SELECT name FROM schema_migrations")).rows.map((r) => r.name));
    for (const file of (await readdir(MIGRATIONS)).filter((f) => f.endsWith(".sql")).sort()) {
      if (done.has(file)) continue;
      await client.query(await readFile(MIGRATIONS + file, "utf8"));
      await client.query("INSERT INTO schema_migrations (name) VALUES ($1)", [file]);
    }
    await client.query("COMMIT");
  } catch (err) {
    await client.query("ROLLBACK");
    throw err;
  } finally {
    client.release();
  }
  return {
    async add(name, quantity) {
      const { rows } = await pool.query(
        "INSERT INTO items (name, quantity) VALUES ($1, $2) RETURNING id::int AS id, name, quantity",
        [name, quantity],
      );
      return rows[0];
    },
    async list() {
      return (await pool.query("SELECT id::int AS id, name, quantity FROM items ORDER BY id")).rows;
    },
    async close() {
      await pool.end();
    },
    pool,
  };
}

export async function repoFromEnv() {
  return process.env.DATABASE_URL ? pgRepo(process.env.DATABASE_URL) : memoryRepo();
}
