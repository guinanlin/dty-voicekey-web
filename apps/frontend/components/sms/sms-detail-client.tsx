"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useTransition } from "react";
import { Star, Trash2, Copy, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { removeSms, toggleSmsStar } from "@/components/actions/sms-action";
import type { SmsRead } from "@/app/openapi-client";
import { formatDateTimeZhCn } from "@/lib/utils";

export function SmsDetailClient({ sms }: { sms: SmsRead }) {
  const router = useRouter();
  const [pending, startTransition] = useTransition();

  const handleCopy = async () => {
    await navigator.clipboard.writeText(sms.content);
  };

  const handleStar = () => {
    startTransition(async () => {
      await toggleSmsStar(sms.id, !sms.starred);
      router.refresh();
    });
  };

  const handleDelete = () => {
    if (!confirm("确定删除这条短信吗？")) return;
    startTransition(async () => {
      await removeSms(sms.id);
      router.push("/sms");
    });
  };

  return (
    <div className="space-y-6">
      <Link
        href="/sms"
        className="inline-flex items-center gap-1 text-sm text-blue-500"
      >
        <ArrowLeft className="h-4 w-4" />
        返回列表
      </Link>

      <div className="border rounded-lg bg-background p-6 shadow-sm space-y-4">
        <div className="grid gap-2 text-sm">
          <p>
            <span className="text-muted-foreground">发送号码：</span>
            {sms.phone}
          </p>
          <p>
            <span className="text-muted-foreground">接收时间：</span>
            {formatDateTimeZhCn(sms.received_at)}
          </p>
          <p>
            <span className="text-muted-foreground">标记状态：</span>
            {sms.starred ? "已标记" : "未标记"}
          </p>
        </div>

        <hr />

        <div className="whitespace-pre-wrap text-sm leading-relaxed">
          {sms.content}
        </div>

        <hr />

        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={handleCopy}>
            <Copy className="h-4 w-4 mr-1" />
            复制内容
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={handleStar}
            disabled={pending}
          >
            <Star
              className={`h-4 w-4 mr-1 ${sms.starred ? "fill-yellow-400 text-yellow-400" : ""}`}
            />
            {sms.starred ? "取消标记" : "标记"}
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={handleDelete}
            disabled={pending}
          >
            <Trash2 className="h-4 w-4 mr-1" />
            删除
          </Button>
        </div>
      </div>
    </div>
  );
}
