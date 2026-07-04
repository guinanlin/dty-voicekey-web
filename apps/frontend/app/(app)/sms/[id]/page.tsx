import Link from "next/link";
import { redirect } from "next/navigation";
import { fetchSmsDetail } from "@/components/actions/sms-action";
import { SmsDetailClient } from "@/components/sms/sms-detail-client";

export default async function SmsDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const sms = await fetchSmsDetail(id);

  if (!sms) {
    redirect("/sms");
  }

  return <SmsDetailClient sms={sms} />;
}
