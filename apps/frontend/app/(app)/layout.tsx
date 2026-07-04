import { cookies } from "next/headers";
import { usersCurrentUser } from "@/app/clientService";
import type { UserRead } from "@/app/openapi-client";
import { AppShell } from "@/components/layout/app-shell";

async function getCurrentUser(): Promise<UserRead | null> {
  const token = (await cookies()).get("accessToken")?.value;
  if (!token) return null;

  const { data } = await usersCurrentUser({
    headers: { Authorization: `Bearer ${token}` },
  });
  return data ?? null;
}

export default async function AppLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const user = await getCurrentUser();
  return <AppShell user={user}>{children}</AppShell>;
}
