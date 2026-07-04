import Link from "next/link";
import { MessageSquare } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import type { SmsStatsResponse } from "@/app/openapi-client";

type Props = {
  stats: SmsStatsResponse | null;
};

const statCards = [
  { key: "total" as const, label: "全部短信", description: "累计接收" },
  { key: "starred" as const, label: "已标记", description: "重点短信" },
  { key: "today" as const, label: "今日", description: "今天收到" },
  { key: "this_week" as const, label: "本周", description: "本周收到" },
];

export function HomeDashboard({ stats }: Props) {
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">传声筒</h1>
        <p className="mt-2 text-muted-foreground">
          短信接收与管理平台，快速查看统计并进入短信列表。
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {statCards.map((card) => (
          <Card key={card.key}>
            <CardHeader className="pb-2">
              <CardDescription>{card.description}</CardDescription>
              <CardTitle className="text-2xl">
                {stats ? stats[card.key] : "—"}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">{card.label}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>快捷入口</CardTitle>
          <CardDescription>进入短信管理，查看、搜索和处理接收的短信</CardDescription>
        </CardHeader>
        <CardContent>
          <Link href="/sms">
            <Button className="gap-2">
              <MessageSquare className="h-4 w-4" />
              进入短信管理
            </Button>
          </Link>
        </CardContent>
      </Card>
    </div>
  );
}
