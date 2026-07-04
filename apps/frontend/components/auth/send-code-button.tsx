"use client";

import { useState, useTransition } from "react";
import { Button } from "@/components/ui/button";

type SendCodeAction = (
  value: string,
) => Promise<{ error?: string; success?: boolean; message?: string }>;

export function SendCodeButton({
  label = "发送验证码",
  getValue,
  onSend,
  cooldown = 60,
}: {
  label?: string;
  getValue: () => string;
  onSend: SendCodeAction;
  cooldown?: number;
}) {
  const [seconds, setSeconds] = useState(0);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [pending, startTransition] = useTransition();

  const handleSend = () => {
    const value = getValue().trim();
    if (!value) {
      setError("请先填写完整信息");
      return;
    }
    setError("");
    setMessage("");
    startTransition(async () => {
      const result = await onSend(value);
      if (result.error) {
        setError(result.error);
        return;
      }
      setMessage(result.message ?? "验证码已发送");
      setSeconds(cooldown);
      const timer = setInterval(() => {
        setSeconds((s) => {
          if (s <= 1) {
            clearInterval(timer);
            return 0;
          }
          return s - 1;
        });
      }, 1000);
    });
  };

  return (
    <div className="space-y-1">
      <Button
        type="button"
        variant="outline"
        className="w-full"
        disabled={pending || seconds > 0}
        onClick={handleSend}
      >
        {seconds > 0 ? `${seconds}s 后重发` : pending ? "发送中..." : label}
      </Button>
      {error && <p className="text-sm text-red-500">{error}</p>}
      {message && <p className="text-sm text-green-600">{message}</p>}
    </div>
  );
}
