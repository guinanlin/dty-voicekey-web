import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import {
  fetchRelayMessages,
  fetchRelayPairs,
} from "@/components/actions/craftsman-action";
import { CraftsmanShell } from "@/components/craftsman/craftsman-shell";

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
    />
  );
}
