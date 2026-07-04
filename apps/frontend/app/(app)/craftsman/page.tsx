import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import {
  fetchRelayMessages,
  fetchRelayPairs,
} from "@/components/actions/craftsman-action";
import { CraftsmanShell } from "@/components/craftsman/craftsman-shell";

function buildRelayEventsWsUrl(): string {
  // 优先使用显式配置的公网可达地址（浏览器直连）
  if (process.env.NEXT_PUBLIC_RELAY_WS_URL) {
    return process.env.NEXT_PUBLIC_RELAY_WS_URL;
  }
  // 降级：从 API_BASE_URL 推导（仅在宿主机直接运行时有效）
  const apiBase = process.env.API_BASE_URL ?? "http://localhost:8600";
  return `${apiBase.replace(/^http/i, "ws")}/relay/ws`;
}

export default async function CraftsmanPage() {
  const [messages, pairs] = await Promise.all([
    fetchRelayMessages({ page: 1, page_size: 100, sort: "newest" }),
    fetchRelayPairs(),
  ]);

  if (!messages) {
    redirect("/login");
  }

  const accessToken = (await cookies()).get("accessToken")?.value ?? "";

  return (
    <CraftsmanShell
      initialMessages={messages}
      initialPairs={pairs?.items ?? []}
      accessToken={accessToken}
      relayEventsWsUrl={buildRelayEventsWsUrl()}
    />
  );
}
