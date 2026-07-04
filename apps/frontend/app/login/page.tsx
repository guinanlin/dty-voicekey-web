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
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { login } from "@/components/actions/login-action";
import {
  phoneLogin,
  sendLoginPhoneCode,
} from "@/components/actions/auth-ext-action";
import { SubmitButton } from "@/components/ui/submitButton";
import { FieldError, FormError } from "@/components/ui/FormError";
import { SendCodeButton } from "@/components/auth/send-code-button";

export default function LoginPage() {
  const [emailState, emailDispatch] = useActionState(login, undefined);
  const [phoneState, phoneDispatch] = useActionState(phoneLogin, undefined);
  const phoneRef = useRef<HTMLInputElement>(null);

  return (
    <div className="flex h-screen w-full items-center justify-center bg-gray-50 dark:bg-gray-900 px-4">
      <Card className="w-full max-w-sm rounded-lg shadow-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 md:min-w-[450px]">
        <CardHeader className="text-center">
          <CardTitle className="text-2xl font-semibold text-gray-800 dark:text-white">
            传声筒 · 登录
          </CardTitle>
          <CardDescription className="text-sm text-gray-600 dark:text-gray-400">
            邮箱密码或手机验证码登录
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="email">
            <TabsList className="grid w-full grid-cols-2 mb-4">
              <TabsTrigger value="email">邮箱登录</TabsTrigger>
              <TabsTrigger value="phone">手机登录</TabsTrigger>
            </TabsList>

            <TabsContent value="email">
              <form action={emailDispatch} className="grid gap-4">
                <div className="grid gap-2">
                  <Label htmlFor="username">邮箱</Label>
                  <Input
                    id="username"
                    name="username"
                    type="email"
                    placeholder="admin@dty.com"
                    required
                  />
                  <FieldError state={emailState} field="username" />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="password">密码</Label>
                  <Input
                    id="password"
                    name="password"
                    type="password"
                    required
                  />
                  <FieldError state={emailState} field="password" />
                  <Link
                    href="/password-recovery"
                    className="ml-auto inline-block text-sm text-blue-500"
                  >
                    忘记密码？
                  </Link>
                </div>
                <SubmitButton text="登录" />
                <FormError state={emailState} />
              </form>
            </TabsContent>

            <TabsContent value="phone">
              <form action={phoneDispatch} className="grid gap-4">
                <div className="grid gap-2">
                  <Label htmlFor="phone">手机号</Label>
                  <Input
                    id="phone"
                    name="phone"
                    ref={phoneRef}
                    type="tel"
                    placeholder="13800138000"
                    required
                  />
                </div>
                <SendCodeButton
                  getValue={() => phoneRef.current?.value ?? ""}
                  onSend={(phone) => sendLoginPhoneCode(phone)}
                />
                <div className="grid gap-2">
                  <Label htmlFor="code">验证码</Label>
                  <Input
                    id="code"
                    name="code"
                    placeholder="6 位验证码"
                    required
                  />
                </div>
                <SubmitButton text="登录" />
                <FormError state={phoneState} />
              </form>
            </TabsContent>
          </Tabs>

          <div className="mt-4 text-center text-sm text-gray-600">
            没有帐户？{" "}
            <Link href="/register" className="text-blue-500">
              注册
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
