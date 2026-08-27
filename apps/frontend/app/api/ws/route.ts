import { NextResponse } from "next/server";

/**
 * 中继配对 WebSocket：`ws://{host}/api/ws?pair={pair_token}`
 * HTTP Upgrade 由自定义 server.ts 代理到后端 `/ws`。
 */
export async function GET() {
  return new NextResponse("Upgrade Required: connect with WebSocket", {
    status: 426,
    headers: { Upgrade: "websocket" },
  });
}
