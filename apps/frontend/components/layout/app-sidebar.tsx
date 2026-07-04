"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { MessageSquare } from "lucide-react";
import { cn } from "@/lib/utils";
import { navItems } from "./nav-items";

export function AppSidebar() {
  const pathname = usePathname();

  const isActive = (href: string) => {
    if (href === "/home") return pathname === "/home";
    return pathname === href || pathname.startsWith(`${href}/`);
  };

  return (
    <aside className="fixed inset-y-0 left-0 z-10 flex w-56 flex-col border-r bg-background">
      <div className="flex h-16 items-center gap-2 border-b px-5">
        <MessageSquare className="h-6 w-6 text-primary" />
        <span className="text-lg font-semibold">传声筒</span>
      </div>
      <nav className="flex flex-1 flex-col gap-1 p-3">
        {navItems.map((item) => {
          const Icon = item.icon;
          const active = isActive(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                active
                  ? "bg-primary/10 text-primary"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground",
              )}
            >
              <Icon className="h-4 w-4" />
              {item.title}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
