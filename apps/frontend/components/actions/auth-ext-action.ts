"use server";

import {
  loginWithPhone,
  registerWithCode,
  sendEmailCode,
  sendPhoneCode,
} from "@/app/clientService";
import { getErrorMessage } from "@/lib/utils";

export async function sendRegisterEmailCode(email: string) {
  const { error } = await sendEmailCode({
    body: { email, scene: "register" },
  });
  if (error) {
    return { error: getErrorMessage(error) };
  }
  return { success: true };
}

export async function sendLoginPhoneCode(phone: string) {
  const { error } = await sendPhoneCode({
    body: { phone },
  });
  if (error) {
    return { error: getErrorMessage(error) };
  }
  return { success: true, message: "验证码已发送（开发环境请查看后端日志）" };
}

export async function registerWithVerificationCode(
  prevState: unknown,
  formData: FormData,
) {
  const email = formData.get("email") as string;
  const password = formData.get("password") as string;
  const code = formData.get("code") as string;

  const { data, error } = await registerWithCode({
    body: { email, password, code },
  });

  if (error) {
    return { server_validation_error: getErrorMessage(error) };
  }

  const { cookies } = await import("next/headers");
  const { redirect } = await import("next/navigation");
  (await cookies()).set("accessToken", data.access_token);
  redirect("/home");
}

export async function phoneLogin(prevState: unknown, formData: FormData) {
  const phone = formData.get("phone") as string;
  const code = formData.get("code") as string;

  const { data, error } = await loginWithPhone({
    body: { phone, code },
  });

  if (error) {
    return { server_validation_error: getErrorMessage(error) };
  }

  const { cookies } = await import("next/headers");
  const { redirect } = await import("next/navigation");
  (await cookies()).set("accessToken", data.access_token);
  redirect("/home");
}
