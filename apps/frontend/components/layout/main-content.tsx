"use client";

import { usePathname } from "next/navigation";

export function MainContent({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const fullWidth =
    pathname === "/craftsman" ||
    pathname.startsWith("/craftsman/") ||
    pathname === "/sms" ||
    pathname.startsWith("/sms/");

  return (
    <div
      className={
        fullWidth ? "flex h-full min-h-0 w-full flex-col" : "mx-auto max-w-5xl"
      }
    >
      {children}
    </div>
  );
}
