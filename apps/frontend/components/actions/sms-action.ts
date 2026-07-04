"use server";

import { cookies } from "next/headers";
import { revalidatePath } from "next/cache";
import {
  batchDeleteSms,
  batchStarSms,
  deleteSms,
  getSms,
  listSms,
  smsPhones,
  smsStats,
  starSms,
} from "@/app/clientService";

async function authHeaders() {
  const token = (await cookies()).get("accessToken")?.value;
  if (!token) return null;
  return { Authorization: `Bearer ${token}` };
}

export async function fetchSmsList(params: {
  page?: number;
  page_size?: number;
  search?: string;
  phone?: string;
  starred?: boolean;
}) {
  const headers = await authHeaders();
  if (!headers) return null;

  const { data, error } = await listSms({
    headers,
    query: {
      page: params.page ?? 1,
      page_size: params.page_size ?? 20,
      search: params.search || undefined,
      phone: params.phone || undefined,
      starred: params.starred,
    },
  });

  if (error) return null;
  return data;
}

export async function fetchSmsDetail(id: string) {
  const headers = await authHeaders();
  if (!headers) return null;

  const { data, error } = await getSms({
    headers,
    path: { sms_id: id },
  });

  if (error) return null;
  return data;
}

export async function fetchSmsPhones() {
  const headers = await authHeaders();
  if (!headers) return [];

  const { data, error } = await smsPhones({ headers });
  if (error) return [];
  return data;
}

export async function fetchSmsStats() {
  const headers = await authHeaders();
  if (!headers) return null;

  const { data, error } = await smsStats({ headers });
  if (error) return null;
  return data;
}

export async function refreshSmsData(params: {
  page?: number;
  page_size?: number;
  search?: string;
  phone?: string;
}) {
  const headers = await authHeaders();
  if (!headers) return null;

  revalidatePath("/sms");

  const [listRes, phonesRes, statsRes] = await Promise.all([
    listSms({
      headers,
      query: {
        page: params.page ?? 1,
        page_size: params.page_size ?? 20,
        search: params.search || undefined,
        phone: params.phone || undefined,
      },
    }),
    smsPhones({ headers }),
    smsStats({ headers }),
  ]);

  if (listRes.error || !listRes.data) return null;

  return {
    list: listRes.data,
    phones: phonesRes.error ? [] : (phonesRes.data ?? []),
    stats: statsRes.error ? null : (statsRes.data ?? null),
  };
}

export async function toggleSmsStar(id: string, starred: boolean) {
  const headers = await authHeaders();
  if (!headers) return { error: "未登录" };

  const { error } = await starSms({
    headers,
    path: { sms_id: id },
    body: { starred },
  });

  if (error) return { error: "操作失败" };
  revalidatePath("/sms");
  revalidatePath(`/sms/${id}`);
  return { success: true };
}

export async function removeSms(id: string) {
  const headers = await authHeaders();
  if (!headers) return { error: "未登录" };

  const { error } = await deleteSms({
    headers,
    path: { sms_id: id },
  });

  if (error) return { error: "删除失败" };
  revalidatePath("/sms");
  return { success: true };
}

export async function batchStar(ids: string[], starred: boolean) {
  const headers = await authHeaders();
  if (!headers) return { error: "未登录" };

  const { error } = await batchStarSms({
    headers,
    body: { ids, starred },
  });

  if (error) return { error: "批量标记失败" };
  revalidatePath("/sms");
  return { success: true };
}

export async function batchRemove(ids: string[]) {
  const headers = await authHeaders();
  if (!headers) return { error: "未登录" };

  const { error } = await batchDeleteSms({
    headers,
    body: { ids },
  });

  if (error) return { error: "批量删除失败" };
  revalidatePath("/sms");
  return { success: true };
}
