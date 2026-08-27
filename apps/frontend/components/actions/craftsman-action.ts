"use server";

import { cookies } from "next/headers";
import { revalidatePath } from "next/cache";
import type {
  RelayMessageListResponse,
  RelayMessageRead,
  RelayMessageStatsResponse,
  RelayPairCreateResponse,
  RelayPairListResponse,
  RelayPairRefreshResponse,
  RelayPairStatusResponse,
} from "@/lib/relay-types";

const API_BASE = process.env.API_BASE_URL ?? "http://localhost:8600";

async function authHeaders() {
  const token = (await cookies()).get("accessToken")?.value;
  if (!token) return null;
  return {
    Authorization: `Bearer ${token}`,
    "Content-Type": "application/json",
  };
}

async function relayFetch<T>(
  path: string,
  init?: RequestInit,
): Promise<T | null> {
  const headers = await authHeaders();
  if (!headers) return null;

  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { ...headers, ...(init?.headers ?? {}) },
    cache: "no-store",
  });

  if (!response.ok) return null;
  if (response.status === 204) return null;
  return (await response.json()) as T;
}

export async function fetchRelayMessages(params: {
  page?: number;
  page_size?: number;
  search?: string;
  sort?: "newest" | "oldest";
}) {
  const query = new URLSearchParams();
  query.set("page", String(params.page ?? 1));
  query.set("page_size", String(params.page_size ?? 50));
  if (params.search) query.set("search", params.search);
  if (params.sort) query.set("sort", params.sort);

  return relayFetch<RelayMessageListResponse>(`/relay/messages?${query}`);
}

export async function fetchRelayMessageDetail(id: string) {
  return relayFetch<RelayMessageRead>(`/relay/messages/${id}`);
}

export async function fetchRelayMessageStats() {
  return relayFetch<RelayMessageStatsResponse>("/relay/messages/stats");
}

export async function fetchRelayPairs() {
  return relayFetch<RelayPairListResponse>("/api/v1/pairs");
}

export async function fetchRelayPairStatus(pairId: string) {
  return relayFetch<RelayPairStatusResponse>(`/api/v1/pairs/${pairId}/status`);
}

export async function createRelayPair(deviceName?: string) {
  const headers = await authHeaders();
  if (!headers) return { error: "未登录" as const };

  const response = await fetch(`${API_BASE}/api/v1/pairs`, {
    method: "POST",
    headers,
    body: JSON.stringify({ device_name: deviceName ?? "Web 配对" }),
    cache: "no-store",
  });

  if (!response.ok) return { error: "创建配对失败" as const };
  const data = (await response.json()) as RelayPairCreateResponse;
  revalidatePath("/craftsman");
  return { data };
}

export async function refreshRelayPairToken(pairId: string) {
  const headers = await authHeaders();
  if (!headers) return { error: "未登录" as const };

  const response = await fetch(
    `${API_BASE}/api/v1/pairs/${pairId}/refresh-token`,
    {
      method: "POST",
      headers,
      cache: "no-store",
    },
  );

  if (!response.ok) return { error: "刷新令牌失败" as const };
  const data = (await response.json()) as RelayPairRefreshResponse;
  revalidatePath("/craftsman");
  return { data };
}

export async function revokeRelayPair(pairId: string) {
  const headers = await authHeaders();
  if (!headers) return { error: "未登录" as const };

  const response = await fetch(`${API_BASE}/api/v1/pairs/${pairId}`, {
    method: "DELETE",
    headers,
    cache: "no-store",
  });

  if (!response.ok) return { error: "吊销配对失败" as const };
  revalidatePath("/craftsman");
  return { success: true as const };
}

export async function deleteRelayMessage(id: string) {
  const headers = await authHeaders();
  if (!headers) return { error: "未登录" as const };

  const response = await fetch(`${API_BASE}/relay/messages/${id}`, {
    method: "DELETE",
    headers,
    cache: "no-store",
  });

  if (!response.ok) return { error: "删除失败" as const };
  revalidatePath("/craftsman");
  return { success: true as const };
}

export async function refreshCraftsmanData(params: {
  page?: number;
  search?: string;
  sort?: "newest" | "oldest";
}) {
  revalidatePath("/craftsman");
  const [messages, stats, pairs] = await Promise.all([
    fetchRelayMessages(params),
    fetchRelayMessageStats(),
    fetchRelayPairs(),
  ]);
  return { messages, stats, pairs };
}
