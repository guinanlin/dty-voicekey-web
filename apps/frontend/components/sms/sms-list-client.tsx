"use client";

import { useCallback, useEffect, useState, useTransition } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Star,
  Trash2,
  Copy,
  ChevronLeft,
  ChevronRight,
  RefreshCw,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  batchRemove,
  batchStar,
  fetchSmsList,
  refreshSmsData,
  removeSms,
  toggleSmsStar,
} from "@/components/actions/sms-action";
import type { SmsListResponse, SmsRead, SmsStatsResponse } from "@/app/openapi-client";
import { formatDateTimeZhCn } from "@/lib/utils";

type Props = {
  initialData: SmsListResponse;
  phones: string[];
  stats: SmsStatsResponse | null;
};

export function SmsListClient({ initialData, phones, stats }: Props) {
  const router = useRouter();
  const [data, setData] = useState(initialData);
  const [statsOverride, setStatsOverride] = useState<SmsStatsResponse | null>(null);
  const [phonesOverride, setPhonesOverride] = useState<string[] | null>(null);
  const [prevStats, setPrevStats] = useState(stats);
  const [prevPhones, setPrevPhones] = useState(phones);

  if (stats !== prevStats) {
    setPrevStats(stats);
    setStatsOverride(null);
  }
  if (phones !== prevPhones) {
    setPrevPhones(phones);
    setPhonesOverride(null);
  }

  const statsData = statsOverride ?? stats;
  const phoneList = phonesOverride ?? phones;
  const [search, setSearch] = useState("");
  const [phoneFilter, setPhoneFilter] = useState("");
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [expanded, setExpanded] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [message, setMessage] = useState("");
  const [refreshing, setRefreshing] = useState(false);
  const [pending, startTransition] = useTransition();

  const loadList = useCallback(
    (p: number, s: string, ph: string) => {
      startTransition(async () => {
        const result = await fetchSmsList({
          page: p,
          page_size: 20,
          search: s || undefined,
          phone: ph || undefined,
        });
        if (result) setData(result);
      });
    },
    [],
  );

  useEffect(() => {
    const timer = setTimeout(() => {
      setPage(1);
      loadList(1, search, phoneFilter);
    }, 300);
    return () => clearTimeout(timer);
  }, [search, phoneFilter, loadList]);

  const toggleSelect = (id: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const handleCopy = async (content: string) => {
    await navigator.clipboard.writeText(content);
    setMessage("已复制到剪贴板");
    setTimeout(() => setMessage(""), 2000);
  };

  const handleStar = (item: SmsRead) => {
    startTransition(async () => {
      await toggleSmsStar(item.id, !item.starred);
      router.refresh();
      loadList(page, search, phoneFilter);
    });
  };

  const handleDelete = (id: string) => {
    if (!confirm("确定删除这条短信吗？")) return;
    startTransition(async () => {
      await removeSms(id);
      router.refresh();
      loadList(page, search, phoneFilter);
    });
  };

  const handleBatchStar = (starred: boolean) => {
    const ids = Array.from(selected);
    if (!ids.length) return;
    startTransition(async () => {
      await batchStar(ids, starred);
      setSelected(new Set());
      router.refresh();
      loadList(page, search, phoneFilter);
    });
  };

  const handleBatchDelete = () => {
    const ids = Array.from(selected);
    if (!ids.length) return;
    if (!confirm(`确定删除选中的 ${ids.length} 条短信吗？`)) return;
    startTransition(async () => {
      await batchRemove(ids);
      setSelected(new Set());
      router.refresh();
      loadList(page, search, phoneFilter);
    });
  };

  const handleRefresh = () => {
    setRefreshing(true);
    startTransition(async () => {
      try {
        const result = await refreshSmsData({
          page,
          page_size: 20,
          search: search || undefined,
          phone: phoneFilter || undefined,
        });
        if (result) {
          setData(result.list);
          setStatsOverride(result.stats);
          setPhonesOverride(result.phones);
        }
      } finally {
        setRefreshing(false);
      }
    });
  };

  const totalPages = Math.max(1, Math.ceil(data.total / data.page_size));

  return (
    <div className="space-y-4">
      {statsData && (
        <div className="flex flex-wrap gap-2">
          <Badge variant="outline">全部 {statsData.total}</Badge>
          <Badge variant="outline">已标记 {statsData.starred}</Badge>
          <Badge variant="outline">今日 {statsData.today}</Badge>
          <Badge variant="outline">本周 {statsData.this_week}</Badge>
        </div>
      )}

      <div className="flex flex-col sm:flex-row gap-3 sm:items-center">
        <Input
          placeholder="搜索短信内容..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="flex-1"
        />
        <select
          className="border rounded-md px-3 py-2 text-sm bg-background"
          value={phoneFilter}
          onChange={(e) => setPhoneFilter(e.target.value)}
        >
          <option value="">全部号码</option>
          {phoneList.map((p) => (
            <option key={p} value={p}>
              {p}
            </option>
          ))}
        </select>
        <Button
          variant="outline"
          size="icon"
          onClick={handleRefresh}
          disabled={refreshing || pending}
          title="刷新"
        >
          <RefreshCw
            className={`h-4 w-4 ${refreshing ? "animate-spin" : ""}`}
          />
        </Button>
      </div>

      {selected.size > 0 && (
        <div className="flex gap-2 items-center">
          <span className="text-sm text-muted-foreground">
            已选 {selected.size} 条
          </span>
          <Button size="sm" variant="outline" onClick={() => handleBatchStar(true)}>
            批量标记
          </Button>
          <Button size="sm" variant="outline" onClick={() => handleBatchDelete()}>
            批量删除
          </Button>
        </div>
      )}

      {message && <p className="text-sm text-green-600">{message}</p>}

      <div className="space-y-2">
        {data.items.length === 0 ? (
          <p className="text-center text-muted-foreground py-12">暂无短信</p>
        ) : (
          data.items.map((item) => (
            <SmsItemCard
              key={item.id}
              item={item}
              selected={selected.has(item.id)}
              expanded={expanded === item.id}
              onToggleSelect={() => toggleSelect(item.id)}
              onToggleExpand={() =>
                setExpanded(expanded === item.id ? null : item.id)
              }
              onStar={() => handleStar(item)}
              onDelete={() => handleDelete(item.id)}
              onCopy={() => handleCopy(item.content)}
            />
          ))
        )}
      </div>

      <div className="flex items-center justify-between pt-4">
        <span className="text-sm text-muted-foreground">
          共 {data.total} 条短信
          {(pending || refreshing) && " · 加载中..."}
        </span>
        <div className="flex items-center gap-2">
          <Button
            size="sm"
            variant="outline"
            disabled={page <= 1}
            onClick={() => {
              const p = page - 1;
              setPage(p);
              loadList(p, search, phoneFilter);
            }}
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <span className="text-sm">
            {page} / {totalPages}
          </span>
          <Button
            size="sm"
            variant="outline"
            disabled={page >= totalPages}
            onClick={() => {
              const p = page + 1;
              setPage(p);
              loadList(p, search, phoneFilter);
            }}
          >
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}

function SmsItemCard({
  item,
  selected,
  expanded,
  onToggleSelect,
  onToggleExpand,
  onStar,
  onDelete,
  onCopy,
}: {
  item: SmsRead;
  selected: boolean;
  expanded: boolean;
  onToggleSelect: () => void;
  onToggleExpand: () => void;
  onStar: () => void;
  onDelete: () => void;
  onCopy: () => void;
}) {
  const receivedAt = formatDateTimeZhCn(item.received_at);
  const preview =
    item.content.length > 80 ? `${item.content.slice(0, 80)}...` : item.content;

  return (
    <div className="border rounded-lg bg-background p-4 shadow-sm">
      <div className="flex items-start gap-3">
        <input
          type="checkbox"
          checked={selected}
          onChange={onToggleSelect}
          className="mt-1"
        />
        <div className="flex-1 min-w-0 cursor-pointer" onClick={onToggleExpand}>
          <div className="flex items-center justify-between gap-2">
            <span className="font-medium">📱 {item.phone}</span>
            <span className="text-xs text-muted-foreground shrink-0">
              {receivedAt}
            </span>
          </div>
          <p className="text-sm text-muted-foreground mt-1 line-clamp-2">
            {expanded ? item.content : preview}
          </p>
        </div>
        <div className="flex items-center gap-1 shrink-0">
          <button
            type="button"
            onClick={onStar}
            className="p-1 hover:text-yellow-500"
            title="标记"
          >
            <Star
              className={`h-4 w-4 ${item.starred ? "fill-yellow-400 text-yellow-400" : ""}`}
            />
          </button>
          <button type="button" onClick={onCopy} className="p-1 hover:text-blue-500" title="复制">
            <Copy className="h-4 w-4" />
          </button>
          <button type="button" onClick={onDelete} className="p-1 hover:text-red-500" title="删除">
            <Trash2 className="h-4 w-4" />
          </button>
          <Link href={`/sms/${item.id}`} className="p-1 text-xs text-blue-500">
            详情
          </Link>
        </div>
      </div>
    </div>
  );
}
