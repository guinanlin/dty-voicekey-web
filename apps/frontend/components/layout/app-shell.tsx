import type { UserRead } from "@/app/openapi-client";
import { AppSidebar } from "./app-sidebar";
import { AppHeader } from "./app-header";

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
      <div className="ml-56 flex min-h-screen flex-col">
        <AppHeader user={user} />
        <main className="flex-1 p-6">
          <div className="mx-auto max-w-5xl">{children}</div>
        </main>
      </div>
    </div>
  );
}
