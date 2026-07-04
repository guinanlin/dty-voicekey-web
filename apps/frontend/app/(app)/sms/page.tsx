import { redirect } from "next/navigation";
import {
  fetchSmsList,
  fetchSmsPhones,
  fetchSmsStats,
} from "@/components/actions/sms-action";
import { SmsListClient } from "@/components/sms/sms-list-client";

export default async function SmsPage() {
  const [list, phones, stats] = await Promise.all([
    fetchSmsList({ page: 1, page_size: 20 }),
    fetchSmsPhones(),
    fetchSmsStats(),
  ]);

  if (!list) {
    redirect("/login");
  }

  return (
    <SmsListClient
      initialData={list}
      phones={phones ?? []}
      stats={stats ?? null}
    />
  );
}
