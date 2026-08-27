"use client";

import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { MainContent } from "./main-content";

export function AppMain({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const isCraftsman =
    pathname === "/craftsman" || pathname.startsWith("/craftsman/");

  return (
    <main
      className={cn(
        "flex-1 min-h-0",
        isCraftsman ? "flex flex-col overflow-hidden" : "overflow-y-auto p-6",
      )}
    >
      <MainContent>{children}</MainContent>
    </main>
  );
}
