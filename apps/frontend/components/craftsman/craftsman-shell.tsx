"use client";

import { useCallback, useEffect, useRef, useState, useTransition } from "react";
import { RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import type {
  RelayMessageListResponse,
  RelayMessageRead,
  RelayPairCreateResponse,
  RelayPairRead,
} from "@/lib/relay-types";
import {
  fetchRelayMessages,
  refreshCraftsmanData,
} from "@/components/actions/craftsman-action";
import { HistoryPanel } from "@/components/craftsman/history-panel";
import { AssistantPanel } from "@/components/craftsman/assistant-panel";
import { PairDialog } from "@/components/craftsman/pair-dialog";
import { useRelayEvents } from "@/components/craftsman/use-relay-events";

const PAGE_SIZE = 100;

function messageMatchesSearch(message: RelayMessageRead, search: string) {
  if (!search.trim()) return true;
  const query = search.trim().toLowerCase();
  return (
    message.text.toLowerCase().includes(query) ||
    message.pair_id.toLowerCase().includes(query)
  );
}

type Props = {
  initialMessages: RelayMessageListResponse;
  initialPairs: RelayPairRead[];
  accessToken: string;
};

export function CraftsmanShell({
  initialMessages,
  initialPairs,
  accessToken,
}: Props) {
  const [messages, setMessages] = useState(initialMessages);
  const [pairs, setPairs] = useState(initialPairs);
  const [search, setSearch] = useState("");
  const [sort, setSort] = useState<"newest" | "oldest">("newest");
  const [selected, setSelected] = useState<RelayMessageRead | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [pending, startTransition] = useTransition();
  const searchRef = useRef(search);
  const sortRef = useRef(sort);

  useEffect(() => {
    searchRef.current = search;
    sortRef.current = sort;
  }, [search, sort]);

  const handleMessageNew = useCallback((message: RelayMessageRead) => {
    setMessages((prev) => {
      const exists = prev.items.some((item) => item.id === message.id);
      if (exists) {
        return {
          ...prev,
          items: prev.items.map((item) =>
            item.id === message.id ? message : item,
          ),
        };
      }

      const matches = messageMatchesSearch(message, searchRef.current);
      if (!matches) {
        return { ...prev, total: prev.total + 1 };
      }

      const items =
        sortRef.current === "newest"
          ? [message, ...prev.items]
          : [...prev.items, message];

      return {
        ...prev,
        total: prev.total + 1,
        items: items.slice(0, PAGE_SIZE),
      };
    });
  }, []);

  const handleMessageUpdated = useCallback((message: RelayMessageRead) => {
    setMessages((prev) => ({
      ...prev,
      items: prev.items.map((item) =>
        item.id === message.id ? message : item,
      ),
    }));
    setSelected((current) => (current?.id === message.id ? message : current));
  }, []);

  useRelayEvents(accessToken, {
    onMessageNew: handleMessageNew,
    onMessageUpdated: handleMessageUpdated,
  });

  const loadMessages = useCallback((s: string, order: "newest" | "oldest") => {
    startTransition(async () => {
      const result = await fetchRelayMessages({
        page: 1,
        page_size: 100,
        search: s || undefined,
        sort: order,
      });
      if (result) setMessages(result);
    });
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => loadMessages(search, sort), 300);
    return () => clearTimeout(timer);
  }, [search, sort, loadMessages]);

  const handleRefresh = async () => {
    setRefreshing(true);
    const result = await refreshCraftsmanData({ search, sort });
    if (result.messages) setMessages(result.messages);
    if (result.pairs) setPairs(result.pairs.items);
    setRefreshing(false);
  };

  const handlePairCreated = (_data: RelayPairCreateResponse) => {
    handleRefresh();
  };

  const handleDeleted = () => {
    setSelected(null);
    handleRefresh();
  };

  const toolbar = (
    <>
      <PairDialog
        pairs={pairs}
        onPairCreated={handlePairCreated}
        onRefresh={handleRefresh}
      />
      <Button
        variant="ghost"
        size="icon"
        className="h-8 w-8"
        onClick={handleRefresh}
        disabled={refreshing || pending}
        title="刷新"
        aria-label="刷新"
      >
        <RefreshCw className="h-4 w-4" />
      </Button>
    </>
  );

  return (
    <div className="grid min-h-0 flex-1 grid-cols-1 lg:grid-cols-[minmax(280px,360px)_1fr]">
      <HistoryPanel
        items={messages.items}
        total={messages.total}
        search={search}
        sort={sort}
        selectedId={selected?.id ?? null}
        onSearchChange={setSearch}
        onSortChange={setSort}
        onSelect={setSelected}
        actions={toolbar}
      />
      <AssistantPanel selected={selected} onDeleted={handleDeleted} />
    </div>
  );
}
