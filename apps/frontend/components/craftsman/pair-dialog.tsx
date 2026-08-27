"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { QRCodeSVG } from "qrcode.react";
import {
  Copy,
  Link2,
  Loader2,
  RefreshCw,
  Trash2,
  X,
  Circle,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import type { RelayPairCreateResponse, RelayPairRead } from "@/lib/relay-types";
import {
  createRelayPair,
  refreshRelayPairToken,
  revokeRelayPair,
} from "@/components/actions/craftsman-action";
import { cn } from "@/lib/utils";

const STORAGE_KEY = "dty_relay_pair";

type Props = {
  pairs: RelayPairRead[];
  onPairCreated: (data: RelayPairCreateResponse) => void;
  onRefresh: () => void;
};

function loadStoredPair(pairId: string): RelayPairCreateResponse | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const data = JSON.parse(raw) as RelayPairCreateResponse;
    return data.pair_id === pairId ? data : null;
  } catch {
    return null;
  }
}

function saveStoredPair(data: RelayPairCreateResponse) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
}

export function PairDialog({ pairs, onPairCreated, onRefresh }: Props) {
  const [open, setOpen] = useState(false);
  const [creating, setCreating] = useState(false);
  const [loadingQr, setLoadingQr] = useState(false);
  const [toast, setToast] = useState("");
  const [latestPair, setLatestPair] = useState<RelayPairCreateResponse | null>(
    null,
  );
  const [frontendWsOrigin, setFrontendWsOrigin] = useState("");

  const activePair = pairs[0];
  const activePairId = activePair?.pair_id;
  const loadStartedRef = useRef<string | null>(null);

  const showToast = (text: string) => {
    setToast(text);
    setTimeout(() => setToast(""), 2000);
  };

  const fetchQrForPair = useCallback(
    async (pair: RelayPairRead, prev: RelayPairCreateResponse | null) => {
      setLoadingQr(true);
      const result = await refreshRelayPairToken(pair.pair_id);
      setLoadingQr(false);
      if ("error" in result && result.error) {
        showToast(result.error);
        return null;
      }
      if (!result.data) return null;

      const next: RelayPairCreateResponse = {
        pair_id: pair.pair_id,
        pair_token: result.data.pair_token,
        agent_token: prev?.agent_token ?? "",
        relay_ws_url: result.data.qr_payload.ws,
        relay_agent_url: prev?.relay_agent_url ?? "",
        expires_at: result.data.expires_at,
        qr_payload: result.data.qr_payload,
      };
      saveStoredPair(next);
      setLatestPair(next);
      return next;
    },
    [],
  );

  const ensureQrLoaded = useCallback(
    async (pair: RelayPairRead) => {
      const stored = loadStoredPair(pair.pair_id);
      if (stored?.qr_payload) {
        setLatestPair(stored);
        return;
      }

      if (loadStartedRef.current === pair.pair_id) return;
      loadStartedRef.current = pair.pair_id;
      await fetchQrForPair(pair, stored);
    },
    [fetchQrForPair],
  );

  useEffect(() => {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    setFrontendWsOrigin(`${protocol}//${window.location.host}`);
  }, []);

  useEffect(() => {
    loadStartedRef.current = null;
    // This effect intentionally synchronizes component state from localStorage.
    /* eslint-disable react-hooks/set-state-in-effect */
    if (!activePairId) {
      setLatestPair(null);
      return;
    }
    const stored = loadStoredPair(activePairId);
    if (stored?.qr_payload) {
      setLatestPair((prev) =>
        prev?.qr_payload?.pair === stored.qr_payload.pair ? prev : stored,
      );
    }
    /* eslint-enable react-hooks/set-state-in-effect */
  }, [activePairId]);

  const handleCreate = async () => {
    setCreating(true);
    const result = await createRelayPair();
    setCreating(false);
    if ("error" in result && result.error) {
      showToast(result.error);
      return;
    }
    if (result.data) {
      saveStoredPair(result.data);
      setLatestPair(result.data);
      onPairCreated(result.data);
      onRefresh();
      setOpen(true);
    }
  };

  const handleRefreshToken = async () => {
    if (!activePair) return;
    loadStartedRef.current = null;
    await fetchQrForPair(activePair, latestPair);
    showToast("已更新");
  };

  const handleRevoke = async () => {
    if (!activePair) return;
    const result = await revokeRelayPair(activePair.pair_id);
    if ("error" in result && result.error) {
      showToast(result.error);
      return;
    }
    localStorage.removeItem(STORAGE_KEY);
    setLatestPair(null);
    setOpen(false);
    onRefresh();
  };

  const copyUrl = async () => {
    if (!latestPair) return;
    const backendUrl = `${latestPair.qr_payload.ws}?pair=${latestPair.qr_payload.pair}`;
    const frontendUrl = frontendWsOrigin
      ? `${frontendWsOrigin}/api/ws?pair=${latestPair.qr_payload.pair}`
      : null;
    await navigator.clipboard.writeText(
      frontendUrl ? `${backendUrl}\n${frontendUrl}` : backendUrl,
    );
    showToast("已复制");
  };

  const openDialog = () => {
    if (!activePair) {
      void handleCreate();
      return;
    }
    loadStartedRef.current = null;
    setOpen(true);
    void ensureQrLoaded(activePair);
  };

  const displayQr = latestPair?.qr_payload ?? null;
  const frontendWsBase = frontendWsOrigin ? `${frontendWsOrigin}/api/ws` : null;
  const qrForScan =
    displayQr && frontendWsBase
      ? { ...displayQr, ws: frontendWsBase }
      : displayQr;
  const wsUrl = displayQr ? `${displayQr.ws}?pair=${displayQr.pair}` : null;
  const frontendWsUrl =
    displayQr && frontendWsBase
      ? `${frontendWsBase}?pair=${displayQr.pair}`
      : null;

  return (
    <>
      <Button
        variant="ghost"
        size="icon"
        className="relative h-9 w-9"
        onClick={openDialog}
        disabled={creating}
        title={activePair ? "中继配对" : "创建配对"}
        aria-label={activePair ? "中继配对" : "创建配对"}
      >
        <Link2 className="h-4 w-4" />
        {activePair && (
          <Circle
            className={cn(
              "absolute right-1.5 top-1.5 h-2 w-2 fill-current",
              activePair.pc_online
                ? "text-green-500"
                : "text-muted-foreground/50",
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
            className="relative w-full max-w-sm rounded-2xl border bg-background p-6 shadow-lg"
            onClick={(e) => e.stopPropagation()}
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

            <div className="mb-5 flex items-center gap-2">
              <Link2 className="h-5 w-5" />
              <h2 className="text-base font-semibold">中继配对</h2>
              {activePair && (
                <span
                  className={cn(
                    "ml-auto mr-8 h-2 w-2 rounded-full",
                    activePair.pc_online
                      ? "bg-green-500"
                      : "bg-muted-foreground/30",
                  )}
                  title={activePair.pc_online ? "PC 在线" : "PC 离线"}
                />
              )}
            </div>

            {toast && (
              <p className="mb-3 text-center text-xs text-muted-foreground">
                {toast}
              </p>
            )}

            {loadingQr || creating ? (
              <div className="flex flex-col items-center gap-3 py-10">
                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
              </div>
            ) : displayQr ? (
              <div className="flex flex-col items-center gap-4">
                <div className="rounded-xl border bg-white p-3">
                  <QRCodeSVG
                    value={JSON.stringify(qrForScan)}
                    size={180}
                    level="M"
                  />
                </div>
                {(wsUrl || frontendWsUrl) && (
                  <div className="flex w-full flex-col gap-2">
                    {wsUrl && (
                      <p className="w-full break-all text-center font-mono text-xs text-muted-foreground">
                        <span className="mr-1 font-sans text-[10px] text-muted-foreground/80">
                          后端
                        </span>
                        {wsUrl}
                      </p>
                    )}
                    {frontendWsUrl && (
                      <p className="w-full break-all text-center font-mono text-xs text-muted-foreground">
                        <span className="mr-1 font-sans text-[10px] text-muted-foreground/80">
                          前端
                        </span>
                        {frontendWsUrl}
                      </p>
                    )}
                  </div>
                )}
                <div className="flex w-full gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    className="flex-1"
                    onClick={copyUrl}
                    title="复制连接地址"
                  >
                    <Copy className="h-3.5 w-3.5" />
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    className="flex-1"
                    onClick={handleRefreshToken}
                    title="重新生成二维码"
                  >
                    <RefreshCw className="h-3.5 w-3.5" />
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    className="flex-1 text-destructive"
                    onClick={handleRevoke}
                    title="吊销配对"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </Button>
                </div>
              </div>
            ) : !activePair ? (
              <div className="text-center">
                <Button size="sm" onClick={handleCreate} disabled={creating}>
                  创建配对
                </Button>
              </div>
            ) : (
              <div className="flex flex-col items-center gap-3 py-6">
                <p className="text-sm text-muted-foreground">加载失败</p>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={handleRefreshToken}
                >
                  <RefreshCw className="h-3.5 w-3.5" />
                </Button>
              </div>
            )}
          </div>
        </div>
      )}
    </>
  );
}
