"use client";

import Link from "next/link";
import { useRef, useActionState } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  registerWithVerificationCode,
  sendRegisterEmailCode,
} from "@/components/actions/auth-ext-action";
import { SubmitButton } from "@/components/ui/submitButton";
import { FieldError, FormError } from "@/components/ui/FormError";
import { SendCodeButton } from "@/components/auth/send-code-button";

export default function RegisterPage() {
  const [state, dispatch] = useActionState(
    registerWithVerificationCode,
    undefined,
  );
  const emailRef = useRef<HTMLInputElement>(null);

  return (
    <div className="flex h-screen w-full items-center justify-center bg-gray-50 dark:bg-gray-900 px-4">
      <form action={dispatch}>
        <Card className="w-full max-w-sm rounded-lg shadow-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 md:min-w-[450px]">
          <CardHeader className="text-center">
            <CardTitle className="text-2xl font-semibold">
              传声筒 · 注册
            </CardTitle>
            <CardDescription>输入邮箱、密码并完成验证码验证</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-4 p-6">
            <div className="grid gap-2">
              <Label htmlFor="email">邮箱</Label>
              <Input
                id="email"
                name="email"
                ref={emailRef}
                type="email"
                placeholder="user@example.com"
                required
              />
              <FieldError state={state} field="email" />
            </div>
            <SendCodeButton
              getValue={() => emailRef.current?.value ?? ""}
              onSend={(email) => sendRegisterEmailCode(email)}
            />
            <div className="grid gap-2">
              <Label htmlFor="code">验证码</Label>
              <Input id="code" name="code" placeholder="6 位验证码" required />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="password">密码</Label>
              <Input id="password" name="password" type="password" required />
              <FieldError state={state} field="password" />
            </div>
            <SubmitButton text="注册" />
            <FormError state={state} />
            <div className="text-center text-sm">
              <Link href="/login" className="text-blue-500">
                返回登录
              </Link>
            </div>
          </CardContent>
        </Card>
      </form>
    </div>
  );
}
