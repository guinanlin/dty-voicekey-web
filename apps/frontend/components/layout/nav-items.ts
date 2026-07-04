import { LayoutDashboard, MessageSquare, FlaskConical, Hammer } from "lucide-react";
import type { LucideIcon } from "lucide-react";

export type NavItem = {
  title: string;
  href: string;
  icon: LucideIcon;
};

export const navItems: NavItem[] = [
  { title: "首页", href: "/home", icon: LayoutDashboard },
  { title: "短信管理", href: "/sms", icon: MessageSquare },
  { title: "工匠", href: "/craftsman", icon: Hammer },
  { title: "开发演示", href: "/dashboard", icon: FlaskConical },
];
