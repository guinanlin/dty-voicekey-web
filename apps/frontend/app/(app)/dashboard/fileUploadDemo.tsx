"use client";

import { useState } from "react";
import { uploadDashboardFile } from "@/components/actions/files-action";
import { Button } from "@/components/ui/button";
import type { FileUploadResponse } from "@/app/openapi-client";

export function FileUploadDemo() {
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [result, setResult] = useState<FileUploadResponse | null>(null);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setMessage(null);

    const formData = new FormData(event.currentTarget);
    const response = await uploadDashboardFile(formData);

    setLoading(false);

    if (response.success) {
      setResult(response.data);
      setMessage(`上传成功：${response.data.filename}`);
      event.currentTarget.reset();
      return;
    }

    setResult(null);
    setMessage(response.message);
  }

  return (
    <section className="p-6 bg-white rounded-lg shadow-lg mt-8">
      <h2 className="text-xl font-semibold mb-2">文件上传 Demo</h2>
      <p className="text-sm text-muted-foreground mb-4">
        模式 C：浏览器只请求 Core Backend，Core 内部编排 OSS Gateway （presign →
        上传 → complete）。
      </p>

      <form onSubmit={handleSubmit} className="flex flex-col gap-4 max-w-md">
        <input
          type="file"
          name="file"
          required
          className="block w-full text-sm file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:bg-secondary file:text-secondary-foreground hover:file:bg-secondary/80"
        />
        <Button type="submit" disabled={loading}>
          {loading ? "上传中..." : "上传文件"}
        </Button>
      </form>

      {message && (
        <p
          className={`mt-4 text-sm ${result ? "text-green-600" : "text-red-600"}`}
        >
          {message}
        </p>
      )}

      {result && (
        <div className="mt-4 rounded-md border p-4 text-sm space-y-2">
          <p>
            <span className="font-medium">File ID：</span>
            {result.file_id}
          </p>
          <p>
            <span className="font-medium">大小：</span>
            {result.size} bytes
          </p>
          <p>
            <span className="font-medium">类型：</span>
            {result.mime_type}
          </p>
          <p>
            <span className="font-medium">状态：</span>
            {result.status}
          </p>
          <a
            href={result.download_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-600 hover:underline inline-block"
          >
            下载文件
          </a>
        </div>
      )}
    </section>
  );
}
