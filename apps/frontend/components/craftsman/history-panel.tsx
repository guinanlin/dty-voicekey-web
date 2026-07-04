"use client";

import type { ReactNode } from "react";
import { useMemo } from "react";
import { Search, ArrowDownAZ, ArrowUpAZ } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import type { RelayMessageRead } from "@/lib/relay-types";
import { cn } from "@/lib/utils";

type Props = {
  items: RelayMessageRead[];
  total: number;
  search: string;
  sort: "newest" | "oldest";
  selectedId: string | null;
  onSearchChange: (value: string) => void;
  onSortChange: (value: "newest" | "oldest") => void;
  onSelect: (item: RelayMessageRead) => void;
  actions?: ReactNode;
};

const SHANGHAI_TZ = "Asia/Shanghai";

/** 上海时区日历日期 YYYY-MM-DD，SSR 与浏览器结果一致 */
function shanghaiDateKey(iso: string): string {
  return new Intl.DateTimeFormat("en-CA", {
    timeZone: SHANGHAI_TZ,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(new Date(iso));
}

function dateLabel(iso: string): string {
  const targetKey = shanghaiDateKey(iso);
  const todayKey = shanghaiDateKey(new Date().toISOString());
  if (targetKey === todayKey) return "今天";
  const yesterdayKey = shanghaiDateKey(
    new Date(Date.now() - 86400000).toISOString(),
  );
  if (targetKey === yesterdayKey) return "昨天";
  return new Date(iso).toLocaleDateString("zh-CN", { timeZone: SHANGHAI_TZ });
}

function timeOnly(iso: string): string {
  return new Date(iso).toLocaleTimeString("zh-CN", {
    timeZone: SHANGHAI_TZ,
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });
}

function truncate(text: string, max = 72): string {
  const oneLine = text.replace(/\s+/g, " ").trim();
  if (oneLine.length <= max) return oneLine;
  return `${oneLine.slice(0, max)}…`;
}

export function HistoryPanel({
  items,
  total,
  search,
  sort,
  selectedId,
  onSearchChange,
  onSortChange,
  onSelect,
  actions,
}: Props) {
  const grouped = useMemo(() => {
    const map = new Map<string, RelayMessageRead[]>();
    for (const item of items) {
      const label = dateLabel(item.created_at);
      const list = map.get(label) ?? [];
      list.push(item);
      map.set(label, list);
    }
    return Array.from(map.entries());
  }, [items]);

  return (
    <div className="flex h-full flex-col border-r bg-background">
      <div className="border-b p-3">
        <div className="flex items-center gap-2">
          <div className="relative min-w-0 flex-1">
            <Search className="absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              className="h-8 border-0 bg-muted/50 pl-8 pr-2 shadow-none focus-visible:ring-1"
              placeholder="搜索"
              value={search}
              onChange={(e) => onSearchChange(e.target.value)}
            />
          </div>
          <div className="flex shrink-0 items-center gap-0.5">
            <Button
              variant={sort === "newest" ? "secondary" : "ghost"}
              size="icon"
              className="h-8 w-8"
              onClick={() => onSortChange("newest")}
              title="最新在上"
              aria-label="最新在上"
            >
              <ArrowDownAZ className="h-4 w-4" />
            </Button>
            <Button
              variant={sort === "oldest" ? "secondary" : "ghost"}
              size="icon"
              className="h-8 w-8"
              onClick={() => onSortChange("oldest")}
              title="最早在上"
              aria-label="最早在上"
            >
              <ArrowUpAZ className="h-4 w-4" />
            </Button>
            <span className="w-6 text-center text-xs tabular-nums text-muted-foreground">
              {total}
            </span>
            {actions}
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-2 py-1">
        {grouped.length === 0 ? (
          <p className="py-12 text-center text-sm text-muted-foreground">—</p>
        ) : (
          grouped.map(([label, groupItems]) => (
            <div key={label} className="mb-3">
              <p className="px-2 py-1 text-[11px] uppercase tracking-wide text-muted-foreground">
                {label}
              </p>
              <ul className="space-y-0.5">
                {groupItems.map((item) => (
                  <li key={item.id}>
                    <button
                      type="button"
                      onClick={() => onSelect(item)}
                      className={cn(
                        "w-full rounded-lg px-2.5 py-2 text-left transition-colors hover:bg-muted/80",
                        selectedId === item.id && "bg-muted",
                      )}
                    >
                      <div className="flex items-baseline gap-2">
                        <span className="shrink-0 text-[11px] tabular-nums text-muted-foreground">
                          {timeOnly(item.created_at)}
                        </span>
                        <div className="min-w-0 flex-1">
                          <span className="line-clamp-2 text-sm leading-snug">
                            {truncate(item.text)}
                          </span>
                          <span
                            className="mt-0.5 block truncate font-mono text-[10px] text-muted-foreground/80"
                            title={item.pair_id}
                          >
                            {item.pair_id}
                          </span>
                        </div>
                      </div>
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
