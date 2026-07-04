"use client";

import { Button } from "@/components/ui/button";

export function PrintButton() {
  const handlePrint = async () => {
    try {
      // 调用PDF生成API
      const response = await fetch("/api/test-pdf");

      if (!response.ok) {
        throw new Error("PDF生成失败");
      }

      // 获取PDF blob
      const blob = await response.blob();

      // 创建下载链接
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = "hello.pdf";

      // 触发下载
      document.body.appendChild(link);
      link.click();

      // 清理
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error("打印失败:", error);
      alert("打印失败，请重试");
    }
  };

  return (
    <Button
      variant="outline"
      className="text-lg px-4 py-2"
      onClick={handlePrint}
    >
      Print
    </Button>
  );
}
