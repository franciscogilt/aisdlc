import express from "express";

import { memoryRepo } from "./repo.js";

export function createApp({ repo = memoryRepo() } = {}) {
  const app = express();
  app.disable("x-powered-by");
  app.use(express.json({ limit: "100kb" }));

  app.get("/health", (_req, res) => res.json({ status: "ok" }));

  app.get("/items", async (_req, res) => res.json(await repo.list()));

  app.post("/items", async (req, res) => {
    const { name, quantity } = req.body ?? {};
    const errors = {};
    if (typeof name !== "string" || name.length < 1 || name.length > 80) {
      errors.name = "texto de 1 a 80 caracteres";
    }
    if (!Number.isInteger(quantity) || quantity < 1 || quantity > 1000) {
      errors.quantity = "entero de 1 a 1000";
    }
    if (Object.keys(errors).length > 0) return res.status(422).json({ errors });
    return res.status(201).json(await repo.add(name, quantity));
  });

  // Manejo de errores: JSON invalido -> 400; cualquier otro -> 500 sin filtrar detalles internos.
  app.use((err, _req, res, _next) => {
    if (err.type === "entity.parse.failed") return res.status(400).json({ error: "JSON invalido" });
    console.error(err);
    return res.status(500).json({ error: "Error interno" });
  });

  return app;
}
