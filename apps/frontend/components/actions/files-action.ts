"use server";

import { cookies } from "next/headers";
import { revalidatePath } from "next/cache";

export async function uploadDashboardFile(formData: FormData) {
  const cookieStore = await cookies();
  const token = cookieStore.get("accessToken")?.value;

  if (!token) {
    return { success: false as const, message: "未登录，请先登录" };
  }

  const file = formData.get("file");
  if (!file || !(file instanceof Blob) || file.size === 0) {
    return { success: false as const, message: "请选择要上传的文件" };
  }

  const baseURL = process.env.API_BASE_URL;
  if (!baseURL) {
    return { success: false as const, message: "API_BASE_URL 未配置" };
  }

  const uploadForm = new FormData();
  const filename = file instanceof File && file.name ? file.name : "upload";
  uploadForm.append("file", file, filename);

  const response = await fetch(`${baseURL}/files/upload`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
    },
    body: uploadForm,
  });

  if (!response.ok) {
    let message = "上传失败";
    try {
      const payload = (await response.json()) as { detail?: unknown };
      if (typeof payload.detail === "string") {
        message = payload.detail;
      }
    } catch {
      message = response.statusText || message;
    }
    return { success: false as const, message };
  }

  const data = (await response.json()) as {
    file_id: string;
    filename: string;
    size: number;
    mime_type: string;
    status: string;
    download_url: string;
  };

  revalidatePath("/dashboard");
  return { success: true as const, data };
}
