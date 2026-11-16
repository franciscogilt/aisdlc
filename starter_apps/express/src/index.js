import { createApp } from "./app.js";
import { repoFromEnv } from "./repo.js";

const port = Number(process.env.PORT) || 3000;
const repo = await repoFromEnv();
const server = createApp({ repo }).listen(port, () => console.log(`Escuchando en el puerto ${port}`));

for (const signal of ["SIGINT", "SIGTERM"]) {
  process.on(signal, () => server.close(async () => { await repo.close(); process.exit(0); }));
}
