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
const proxyTarget = `${backendUrl.protocol === "https:" ? "wss:" : "ws:"}//${backendUrl.host}`;
const proxy = httpProxy.createProxyServer({
  target: proxyTarget,
  ws: true,
  changeOrigin: true,
});
const backendHealthUrl = new URL("/api/v1/health", backendUrl.origin);
const backendWaitTimeoutMs = 60_000;
let backendReady = false;

const delay = (milliseconds: number) =>
  new Promise<void>((resolve) => setTimeout(resolve, milliseconds));

async function waitForBackend() {
  const deadline = Date.now() + backendWaitTimeoutMs;

  while (Date.now() < deadline) {
    try {
      const response = await fetch(backendHealthUrl, {
        signal: AbortSignal.timeout(3_000),
      });
      if (response.ok) {
        backendReady = true;
        console.log("[ws-proxy] backend healthy, enabling /relay/ws");
        return;
      }
    } catch {
      // The backend may still be starting. Retry until the overall deadline.
    }

    await delay(500);
  }

  console.error("[ws-proxy] backend health check timed out after 60s");
}

async function waitForBackendReady() {
  const deadline = Date.now() + backendWaitTimeoutMs;
  while (!backendReady && Date.now() < deadline) {
    await delay(200);
  }
  return backendReady;
}

proxy.on("error", (error, request, socket) => {
  console.error(`[ws-proxy] proxy error for ${request.url ?? "unknown URL"}:`, error);
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

  if (backendReady) {
    proxy.ws(request, socket, head);
    return;
  }

  void waitForBackendReady().then((ready) => {
    if (ready) {
      proxy.ws(request, socket, head);
      return;
    }

    console.error(
      `[ws-proxy] backend readiness timed out for ${request.url ?? "/relay/ws"}; closing socket`,
    );
    socket.destroy();
  });
});

server.listen(port, hostname, () => {
  console.log(
    `[frontend] Next.js listening on http://${hostname}:${port} (${dev ? "development" : "production"})`,
  );
  console.log(
    `[ws-proxy] /relay/ws -> ${proxyTarget} (port ${backendPort})`,
  );
  void waitForBackend();
});
