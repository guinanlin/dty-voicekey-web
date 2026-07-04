import type { UserRead } from "@/app/openapi-client";
import { AppSidebar } from "./app-sidebar";
import { AppHeader } from "./app-header";
import { AppMain } from "./app-main";

export function AppShell({
  children,
  user,
}: {
  children: React.ReactNode;
  user: UserRead | null;
}) {
  return (
    <div className="min-h-screen bg-muted/40">
      <AppSidebar />
      <div className="ml-56 flex h-screen flex-col">
        <AppHeader user={user} />
        <AppMain>{children}</AppMain>
      </div>
    </div>
  );
}
