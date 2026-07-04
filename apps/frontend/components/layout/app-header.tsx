"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Home, LogOut } from "lucide-react";
import type { UserRead } from "@/app/openapi-client";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { logoutFormAction } from "@/components/actions/logout-action";

type Crumb = { label: string; href?: string };

function getBreadcrumbs(pathname: string): Crumb[] {
  if (pathname === "/home") {
    return [{ label: "首页" }];
  }
  if (pathname === "/sms") {
    return [
      { label: "首页", href: "/home" },
      { label: "短信管理" },
    ];
  }
  if (pathname.startsWith("/sms/")) {
    return [
      { label: "首页", href: "/home" },
      { label: "短信管理", href: "/sms" },
      { label: "详情" },
    ];
  }
  if (pathname.startsWith("/dashboard")) {
    return [
      { label: "首页", href: "/home" },
      { label: "开发演示" },
    ];
  }
  return [{ label: "首页", href: "/home" }];
}

function getUserInitial(user: UserRead | null) {
  if (!user?.email) return "U";
  return user.email.charAt(0).toUpperCase();
}

export function AppHeader({ user }: { user: UserRead | null }) {
  const pathname = usePathname();
  const crumbs = getBreadcrumbs(pathname);

  return (
    <header className="relative z-20 flex h-16 items-center justify-between border-b bg-background px-6">
      <Breadcrumb>
        <BreadcrumbList>
          {crumbs.map((crumb, index) => (
            <span key={crumb.label} className="contents">
              {index > 0 && <BreadcrumbSeparator />}
              <BreadcrumbItem>
                {crumb.href ? (
                  <BreadcrumbLink asChild>
                    <Link
                      href={crumb.href}
                      className="flex items-center gap-1"
                    >
                      {index === 0 && <Home className="h-4 w-4" />}
                      {crumb.label}
                    </Link>
                  </BreadcrumbLink>
                ) : (
                  <BreadcrumbPage>{crumb.label}</BreadcrumbPage>
                )}
              </BreadcrumbItem>
            </span>
          ))}
        </BreadcrumbList>
      </Breadcrumb>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <button
            type="button"
            aria-label="用户菜单"
            className="rounded-full outline-none ring-offset-background transition-colors hover:bg-muted focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
          >
            <Avatar className="h-10 w-10">
              <AvatarFallback>{getUserInitial(user)}</AvatarFallback>
            </Avatar>
          </button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="z-50 w-52">
          <DropdownMenuLabel className="font-normal">
            <div className="flex flex-col gap-1">
              <p className="text-sm font-medium leading-none">账户</p>
              {user?.email ? (
                <p className="truncate text-xs text-muted-foreground">
                  {user.email}
                </p>
              ) : (
                <p className="text-xs text-muted-foreground">当前用户</p>
              )}
            </div>
          </DropdownMenuLabel>
          <DropdownMenuSeparator />
          <DropdownMenuItem asChild>
            <form action={logoutFormAction} className="w-full">
              <button
                type="submit"
                className="flex w-full cursor-pointer items-center gap-2 text-destructive"
              >
                <LogOut className="h-4 w-4" />
                退出登录
              </button>
            </form>
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </header>
  );
}
