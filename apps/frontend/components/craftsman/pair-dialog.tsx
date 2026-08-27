"use client";

import { useEffect, useState } from "react";
import { QRCodeSVG } from "qrcode.react";
import {
  Circle,
  Copy,
  Link2,
  Loader2,
  Plus,
  RefreshCw,
  Trash2,
  X,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import type { RelayPairCreateResponse, RelayPairRead } from "@/lib/relay-types";
import {
  createRelayPair,
  refreshRelayPairToken,
  revokeRelayPair,
} from "@/components/actions/craftsman-action";
import { cn } from "@/lib/utils";

const STORAGE_KEY = "dty_relay_pairs";
const LEGACY_STORAGE_KEY = "dty_relay_pair";
type StoredPairs = Record<string, RelayPairCreateResponse>;

type Props = {
  pairs: RelayPairRead[];
  onPairCreated: (data: RelayPairCreateResponse) => void;
  onRefresh: () => void;
};

function loadStoredPairs(): StoredPairs {
  if (typeof window === "undefined") return {};
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) return JSON.parse(raw) as StoredPairs;
    const legacy = localStorage.getItem(LEGACY_STORAGE_KEY);
    if (!legacy) return {};
    const pair = JSON.parse(legacy) as RelayPairCreateResponse;
    return { [pair.pair_id]: pair };
  } catch {
    return {};
  }
}

function saveStoredPairs(data: StoredPairs) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
  localStorage.removeItem(LEGACY_STORAGE_KEY);
}

function frontendWsOrigin() {
  if (typeof window === "undefined") return "";
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  return `${protocol}//${window.location.host}`;
}

export function PairDialog({ pairs, onPairCreated, onRefresh }: Props) {
  const [open, setOpen] = useState(false);
  const [creating, setCreating] = useState(false);
  const [busyPairId, setBusyPairId] = useState<string | null>(null);
  const [toast, setToast] = useState("");
  const [storedPairs, setStoredPairs] = useState<StoredPairs>({});

  useEffect(() => {
    // The agent token is intentionally only available when a pair is created,
    // so keep each pair's credentials in this browser rather than one global slot.
    const timer = window.setTimeout(() => setStoredPairs(loadStoredPairs()), 0);
    return () => window.clearTimeout(timer);
  }, []);

  const showToast = (text: string) => {
    setToast(text);
    setTimeout(() => setToast(""), 2000);
  };

  const updateStoredPair = (data: RelayPairCreateResponse) => {
    setStoredPairs((current) => {
      const next = { ...current, [data.pair_id]: data };
      saveStoredPairs(next);
      return next;
    });
  };

  const handleCreate = async () => {
    setCreating(true);
    const result = await createRelayPair();
    setCreating(false);
    if ("error" in result && result.error) return showToast(result.error);
    if (result.data) {
      updateStoredPair(result.data);
      onPairCreated(result.data);
      onRefresh();
      setOpen(true);
    }
  };

  const handleRefreshToken = async (pair: RelayPairRead) => {
    setBusyPairId(pair.pair_id);
    const result = await refreshRelayPairToken(pair.pair_id);
    setBusyPairId(null);
    if ("error" in result && result.error) return showToast(result.error);
    if (!result.data) return;
    const previous = storedPairs[pair.pair_id];
    updateStoredPair({
      pair_id: pair.pair_id,
      pair_token: result.data.pair_token,
      agent_token: previous?.agent_token ?? "",
      relay_ws_url: result.data.qr_payload.ws,
      relay_agent_url: previous?.relay_agent_url ?? "",
      expires_at: result.data.expires_at,
      qr_payload: result.data.qr_payload,
    });
    showToast("二维码已更新");
  };

  const handleRevoke = async (pairId: string) => {
    setBusyPairId(pairId);
    const result = await revokeRelayPair(pairId);
    setBusyPairId(null);
    if ("error" in result && result.error) return showToast(result.error);
    setStoredPairs((current) => {
      const next = { ...current };
      delete next[pairId];
      saveStoredPairs(next);
      return next;
    });
    onRefresh();
  };

  const copyAgentInfo = async (data: RelayPairCreateResponse) => {
    await navigator.clipboard.writeText(
      `relay_agent_url=${data.relay_agent_url}\npair_id=${data.pair_id}\nagent_token=${data.agent_token}`,
    );
    showToast("Agent 连接信息已复制");
  };

  const origin = frontendWsOrigin();
  const frontendWsBase = origin ? `${origin}/api/ws` : null;
  const anyOnline = pairs.some((pair) => pair.pc_online);

  return (
    <>
      <Button
        variant="ghost"
        size="icon"
        className="relative h-9 w-9"
        onClick={() => setOpen(true)}
        title="中继配对"
        aria-label="中继配对"
      >
        <Link2 className="h-4 w-4" />
        {pairs.length > 0 && (
          <Circle
            className={cn(
              "absolute right-1.5 top-1.5 h-2 w-2 fill-current",
              anyOnline ? "text-green-500" : "text-muted-foreground/50",
            )}
          />
        )}
      </Button>

      {open && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
          onClick={() => setOpen(false)}
          role="presentation"
        >
          <div
            className="relative max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-2xl border bg-background p-6 shadow-lg"
            onClick={(event) => event.stopPropagation()}
            role="dialog"
            aria-modal="true"
            aria-label="中继配对"
          >
            <button
              type="button"
              className="absolute right-4 top-4 rounded-full p-1 text-muted-foreground hover:bg-muted"
              onClick={() => setOpen(false)}
              aria-label="关闭"
            >
              <X className="h-4 w-4" />
            </button>
            <div className="mb-5 flex items-center gap-2 pr-8">
              <Link2 className="h-5 w-5" />
              <h2 className="text-base font-semibold">中继配对</h2>
              <span className="text-xs text-muted-foreground">
                {pairs.length} 台 PC
              </span>
              <Button
                size="sm"
                className="ml-auto"
                onClick={handleCreate}
                disabled={creating}
              >
                {creating ? (
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                ) : (
                  <Plus className="h-3.5 w-3.5" />
                )}
                新增配对
              </Button>
            </div>
            {toast && (
              <p className="mb-3 text-center text-xs text-muted-foreground">
                {toast}
              </p>
            )}

            {pairs.length === 0 ? (
              <div className="py-10 text-center text-sm text-muted-foreground">
                尚未创建配对
              </div>
            ) : (
              <div className="space-y-4">
                {pairs.map((pair) => {
                  const credentials = storedPairs[pair.pair_id];
                  const qr = credentials?.qr_payload;
                  const qrForScan =
                    qr && frontendWsBase ? { ...qr, ws: frontendWsBase } : qr;
                  const busy = busyPairId === pair.pair_id;
                  return (
                    <section
                      key={pair.pair_id}
                      className="rounded-xl border p-4"
                    >
                      <div className="mb-4 flex items-start gap-3">
                        <span
                          className={cn(
                            "mt-1 h-2.5 w-2.5 rounded-full",
                            pair.pc_online
                              ? "bg-green-500"
                              : "bg-muted-foreground/30",
                          )}
                        />
                        <div className="min-w-0 flex-1">
                          <p className="font-medium">
                            {pair.device_name || "未命名 PC"}
                          </p>
                          <p className="break-all font-mono text-xs text-muted-foreground">
                            {pair.pair_id}
                          </p>
                        </div>
                        <span className="text-xs text-muted-foreground">
                          {pair.pc_online ? "在线" : "离线"}
                        </span>
                      </div>
                      <div className="grid gap-4 sm:grid-cols-[160px_1fr]">
                        <div className="flex min-h-40 items-center justify-center rounded-lg border bg-white p-2">
                          {busy ? (
                            <Loader2 className="h-7 w-7 animate-spin text-muted-foreground" />
                          ) : qrForScan ? (
                            <QRCodeSVG
                              value={JSON.stringify(qrForScan)}
                              size={144}
                              level="M"
                            />
                          ) : (
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => handleRefreshToken(pair)}
                            >
                              生成二维码
                            </Button>
                          )}
                        </div>
                        <div className="min-w-0 space-y-2 text-xs">
                          {credentials?.agent_token ? (
                            <>
                              <p className="break-all">
                                <span className="text-muted-foreground">
                                  relay_agent_url：
                                </span>
                                <span className="font-mono">
                                  {credentials.relay_agent_url}
                                </span>
                              </p>
                              <p className="break-all">
                                <span className="text-muted-foreground">
                                  pair_id：
                                </span>
                                <span className="font-mono">
                                  {pair.pair_id}
                                </span>
                              </p>
                              <p className="break-all">
                                <span className="text-muted-foreground">
                                  agent_token：
                                </span>
                                <span className="font-mono">
                                  {credentials.agent_token}
                                </span>
                              </p>
                            </>
                          ) : (
                            <p className="text-muted-foreground">
                              此浏览器未保存该配对的一次性 Agent
                              token；如已遗失，请删除后重新创建。
                            </p>
                          )}
                          <div className="flex gap-2 pt-2">
                            <Button
                              variant="outline"
                              size="sm"
                              disabled={!credentials?.agent_token}
                              onClick={() =>
                                credentials && copyAgentInfo(credentials)
                              }
                              title="复制 Agent 连接信息"
                            >
                              <Copy className="h-3.5 w-3.5" />
                            </Button>
                            <Button
                              variant="outline"
                              size="sm"
                              disabled={busy}
                              onClick={() => handleRefreshToken(pair)}
                              title="重新生成二维码"
                            >
                              <RefreshCw className="h-3.5 w-3.5" />
                            </Button>
                            <Button
                              variant="outline"
                              size="sm"
                              className="text-destructive"
                              disabled={busy}
                              onClick={() => handleRevoke(pair.pair_id)}
                              title="吊销配对"
                            >
                              <Trash2 className="h-3.5 w-3.5" />
                            </Button>
                          </div>
                        </div>
                      </div>
                    </section>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      )}
    </>
  );
}
