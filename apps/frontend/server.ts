import { createServer } from "node:http";

import httpProxy from "http-proxy";
import next from "next";

const port = Number.parseInt(process.env.PORT ?? "3000", 10);
const hostname = process.env.HOSTNAME ?? "0.0.0.0";
const dev = process.env.NODE_ENV !== "production";
const backendUrl = new URL(process.env.API_BASE_URL ?? "http://localhost:8600");
const backendPort = backendUrl.port
  ? Number.parseInt(backendUrl.port, 10)
  : backendUrl.protocol === "https:"
    ? 443
    : 80;

const app = next({ dev, hostname, port });
const handle = app.getRequestHandler();
const proxy = httpProxy.createProxyServer({
  target: {
    host: backendUrl.hostname,
    port: backendPort,
  },
  ws: true,
  changeOrigin: true,
});

proxy.on("error", (error, _request, socket) => {
  console.error("[ws-proxy] Proxy error:", error);
  if ("destroy" in socket) {
    socket.destroy();
  }
});

await app.prepare();

const server = createServer((request, response) => {
  void handle(request, response);
});

server.on("upgrade", (request, socket, head) => {
  const pathname = new URL(request.url ?? "/", "http://localhost").pathname;
  if (pathname !== "/relay/ws") {
    return;
  }

  proxy.ws(request, socket, head);
});

server.listen(port, hostname, () => {
  console.log(
    `[frontend] Next.js listening on http://${hostname}:${port} (${dev ? "development" : "production"})`,
  );
  console.log(
    `[ws-proxy] /relay/ws -> ${backendUrl.hostname}:${backendPort}/relay/ws`,
  );
});
