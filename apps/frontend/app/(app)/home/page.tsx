import { redirect } from "next/navigation";
import { fetchSmsStats } from "@/components/actions/sms-action";
import { fetchRelayMessageStats } from "@/components/actions/craftsman-action";
import { HomeDashboard } from "@/components/home/home-dashboard";

export default async function HomePage() {
  const [stats, relayStats] = await Promise.all([
    fetchSmsStats(),
    fetchRelayMessageStats(),
  ]);

  if (!stats) {
    redirect("/login");
  }

  return <HomeDashboard stats={stats} relayStats={relayStats} />;
}
