import { createServer } from "node:http";
import { createServer as createNetServer, connect as netConnect } from "node:net";
import type { Duplex } from "node:stream";

import next from "next";

const port = Number.parseInt(process.env.PORT ?? "3000", 10);
const hostname = process.env.LISTEN_HOST ?? "0.0.0.0";
const dev = process.env.NODE_ENV !== "production";
const backendUrl = new URL(process.env.API_BASE_URL ?? "http://localhost:8600");
const backendPort = backendUrl.port
  ? Number.parseInt(backendUrl.port, 10)
  : backendUrl.protocol === "https:"
    ? 443
    : 80;

const app = next({ dev });
const handle = app.getRequestHandler();
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
        console.log("[ws-proxy] backend healthy, enabling /api/ws and /api/relay/ws");
        return;
      }
    } catch {
      // The backend may still be starting. Retry until the overall deadline.
    }

    await delay(500);
  }

  console.error("[ws-proxy] backend health check timed out after 60s");
}

const frontendToBackendWsPath: Record<string, string> = {
  "/api/ws": "/ws",
  "/ws": "/ws",
  "/api/relay/ws": "/relay/ws",
  "/relay/ws": "/relay/ws",
};

function rewriteHandshake(raw: string, backendPath: string) {
  const lines = raw.split("\r\n");
  lines[0] = lines[0].replace(/^GET\s+\S+/, `GET ${backendPath}`);
  const hostIdx = lines.findIndex((line) => line.toLowerCase().startsWith("host:"));
  if (hostIdx >= 0) {
    lines[hostIdx] = `Host: ${backendUrl.hostname}:${backendPort}`;
  }
  return lines.join("\r\n");
}

function pipeSockets(client: Duplex, upstream: Duplex) {
  const closeBoth = () => {
    client.destroy();
    upstream.destroy();
  };
  upstream.on("data", (chunk: Buffer) => {
    if (!client.destroyed) client.write(chunk);
  });
  client.on("data", (chunk: Buffer) => {
    if (!upstream.destroyed) upstream.write(chunk);
  });
  upstream.on("error", closeBoth);
  client.on("error", closeBoth);
  upstream.on("end", () => client.end());
  client.on("end", () => upstream.end());
}

function proxyTo(client: Duplex, firstPacket: Buffer, host: string, destPort: number, payload?: string) {
  const upstream = netConnect(destPort, host);
  upstream.on("connect", () => {
    upstream.write(payload ?? firstPacket);
  });
  pipeSockets(client, upstream);
}

await app.prepare();
const handleUpgrade = app.getUpgradeHandler();

const httpServer = createServer((request, response) => {
  void handle(request, response);
});
httpServer.on("upgrade", (request, socket, head) => {
  void handleUpgrade(request, socket, head);
});

await new Promise<void>((resolve) => {
  httpServer.listen(0, "127.0.0.1", () => resolve());
});
const internalAddress = httpServer.address();
const internalPort =
  typeof internalAddress === "object" && internalAddress
    ? internalAddress.port
    : 0;

const tcpServer = createNetServer((socket) => {
  socket.once("data", (firstPacket: Buffer) => {
    const text = firstPacket.toString("utf8");
    const firstLine = text.split("\r\n")[0] ?? "";
    const pathToken = firstLine.match(/^GET\s+(\S+)/)?.[1];
    if (pathToken && /upgrade:\s*websocket/i.test(text)) {
      const url = new URL(pathToken, "http://localhost");
      const backendPath = frontendToBackendWsPath[url.pathname];
      if (backendPath) {
        console.log("[ws-proxy] upgrade", url.pathname, "->", backendPath);
        if (!backendReady) {
          socket.destroy();
          return;
        }
        proxyTo(
          socket,
          firstPacket,
          backendUrl.hostname,
          backendPort,
          rewriteHandshake(text, `${backendPath}${url.search}`),
        );
        return;
      }
    }

    proxyTo(socket, firstPacket, "127.0.0.1", internalPort);
  });
});

tcpServer.listen(port, hostname, () => {
  console.log(
    `[frontend] Next.js listening on http://${hostname}:${port} (${dev ? "development" : "production"})`,
  );
  console.log(
    `[ws-proxy] /api/ws,/api/relay/ws -> ${backendUrl.protocol}//${backendUrl.host} (port ${backendPort})`,
  );
  void waitForBackend();
});
