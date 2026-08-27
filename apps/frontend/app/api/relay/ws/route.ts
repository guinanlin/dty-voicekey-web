import { NextResponse } from "next/server";

/**
 * 工匠页订阅 WebSocket：`ws://{host}/api/relay/ws?token={jwt}`
 * HTTP Upgrade 由自定义 server.ts 代理到后端 `/relay/ws`。
 */
export async function GET() {
  return new NextResponse("Upgrade Required: connect with WebSocket", {
    status: 426,
    headers: { Upgrade: "websocket" },
  });
}
