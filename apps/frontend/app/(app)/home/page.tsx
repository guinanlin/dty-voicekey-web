import { redirect } from "next/navigation";
import { fetchSmsStats } from "@/components/actions/sms-action";
import { HomeDashboard } from "@/components/home/home-dashboard";

export default async function HomePage() {
  const stats = await fetchSmsStats();

  if (!stats) {
    redirect("/login");
  }

  return <HomeDashboard stats={stats} />;
}
