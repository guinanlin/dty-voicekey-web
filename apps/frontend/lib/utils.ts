import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function getErrorMessage(error: { detail?: unknown }): string {
  let errorMessage = "发生未知错误";

  if (typeof error.detail === "string") {
    errorMessage = error.detail;
  } else if (
    typeof error.detail === "object" &&
    error.detail !== null &&
    "reason" in error.detail
  ) {
    errorMessage = String((error.detail as { reason: unknown }).reason);
  }

  return errorMessage;
}

/** 固定东八区，避免 SSR（UTC）与浏览器（本地时区）hydration 不一致 */
export function formatDateTimeZhCn(iso: string | Date): string {
  const date = typeof iso === "string" ? new Date(iso) : iso;
  return date.toLocaleString("zh-CN", {
    timeZone: "Asia/Shanghai",
    year: "numeric",
    month: "numeric",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  });
}
