"use client";

import { Bot, Copy, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { RelayMessageRead } from "@/lib/relay-types";
import { formatDateTimeZhCn } from "@/lib/utils";
import { deleteRelayMessage } from "@/components/actions/craftsman-action";
import { cn } from "@/lib/utils";

type Props = {
  selected: RelayMessageRead | null;
  onDeleted: () => void;
};

const statusDot: Record<string, string> = {
  delivered: "bg-green-500",
  pc_offline: "bg-amber-400",
  failed: "bg-red-500",
  pending: "bg-muted-foreground/40",
};

export function AssistantPanel({ selected, onDeleted }: Props) {
  const handleCopyText = async () => {
    if (!selected) return;
    await navigator.clipboard.writeText(selected.text);
  };

  const handleCopyPairId = async () => {
    if (!selected) return;
    await navigator.clipboard.writeText(selected.pair_id);
  };

  const handleDelete = async () => {
    if (!selected) return;
    const result = await deleteRelayMessage(selected.id);
    if ("success" in result) onDeleted();
  };

  if (!selected) {
    return (
      <div className="flex h-full flex-col items-center justify-center bg-muted/10">
        <Bot className="mb-3 h-10 w-10 text-muted-foreground/40" strokeWidth={1.5} />
        <p className="text-sm text-muted-foreground">选择一条消息</p>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col bg-muted/10">
      <div className="flex items-center justify-between border-b px-4 py-2.5">
        <div className="flex items-center gap-2">
          <span
            className={cn(
              "h-2 w-2 rounded-full",
              statusDot[selected.delivery_status] ?? "bg-muted-foreground/40",
            )}
          />
          <span className="text-xs tabular-nums text-muted-foreground">
            {formatDateTimeZhCn(selected.created_at)}
          </span>
        </div>
        <div className="flex gap-1">
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8"
            onClick={handleCopyText}
            title="复制正文"
            aria-label="复制正文"
          >
            <Copy className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8 text-destructive"
            onClick={handleDelete}
            title="删除"
            aria-label="删除"
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      </div>

      <div className="border-b px-4 py-2">
        <div className="flex items-center gap-2">
          <span className="shrink-0 text-[11px] uppercase tracking-wide text-muted-foreground">
            Pair ID
          </span>
          <code className="min-w-0 flex-1 truncate font-mono text-xs text-foreground/80">
            {selected.pair_id}
          </code>
          <Button
            variant="ghost"
            size="icon"
            className="h-7 w-7 shrink-0"
            onClick={handleCopyPairId}
            title="复制 Pair ID"
            aria-label="复制 Pair ID"
          >
            <Copy className="h-3.5 w-3.5" />
          </Button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-6">
        <p className="whitespace-pre-wrap break-words text-[15px] leading-relaxed">
          {selected.text}
        </p>
        {selected.ack_error && (
          <p className="mt-4 text-sm text-destructive">{selected.ack_error}</p>
        )}
      </div>
    </div>
  );
}
