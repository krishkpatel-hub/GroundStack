"use client";

import {
  Bot,
  BookOpenText,
  ChartNoAxesCombined,
  ChevronLeft,
  ChevronRight,
  FileText,
  History,
  Home,
  Menu,
  MessageSquare,
  Settings,
  ShieldCheck,
  UploadCloud,
  X,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { type ReactNode, useEffect, useMemo, useState } from "react";

import { BrandMark } from "@/components/brand-mark";
import { StatusIndicator } from "@/components/status-indicator";
import { fetchAuthInfo, type AuthInfo } from "@/lib/auth";

type AppFrameProps = {
  title: string;
  description: string;
  actions?: ReactNode;
  children: ReactNode;
};

const publicItems = [
  { href: "/", label: "Overview", icon: Home },
  { href: "/ask", label: "Ask GroundStack", icon: MessageSquare },
  { href: "/sources", label: "Sources", icon: BookOpenText },
  { href: "/about", label: "Docs and about", icon: FileText },
];

const userItems = [{ href: "/conversations", label: "History", icon: History }];

const adminItems = [
  { href: "/knowledge", label: "Knowledge admin", icon: UploadCloud },
  { href: "/activity", label: "Ingestion activity", icon: ShieldCheck },
  { href: "/evaluation", label: "Evaluation", icon: ChartNoAxesCombined },
  { href: "/training", label: "Training review", icon: FileText },
  { href: "/discord", label: "Discord integration", icon: Bot },
  { href: "/settings", label: "System settings", icon: Settings },
];

export function AppFrame({
  title,
  description,
  actions,
  children,
}: AppFrameProps) {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [auth, setAuth] = useState<AuthInfo>({
    authenticated: false,
    anonymous: true,
    roles: [],
    admin: false,
  });

  useEffect(() => {
    const controller = new AbortController();
    void fetchAuthInfo(controller.signal)
      .then(setAuth)
      .catch(() => {
        setAuth({
          authenticated: false,
          anonymous: true,
          roles: [],
          admin: false,
        });
      });
    return () => controller.abort();
  }, []);

  const navGroups = useMemo(() => {
    const groups = [{ label: "Product", items: publicItems }];
    if (auth.authenticated)
      groups.push({ label: "Workspace", items: userItems });
    if (auth.admin) groups.push({ label: "Administration", items: adminItems });
    return groups;
  }, [auth]);

  return (
    <div className="app-layout">
      <a className="skip-link" href="#main-content">
        Skip to content
      </a>
      {mobileOpen && (
        <button
          className="mobile-backdrop md:hidden"
          type="button"
          aria-label="Close navigation"
          onClick={() => setMobileOpen(false)}
        />
      )}
      <aside
        className={`sidebar ${collapsed ? "sidebar-collapsed" : ""} ${
          mobileOpen ? "sidebar-open" : ""
        }`}
        aria-label="Primary navigation"
      >
        <div className="flex h-14 items-center justify-between border-b border-[var(--border)] px-3">
          <Link
            href="/"
            className="min-w-0 text-inherit no-underline"
            onClick={() => setMobileOpen(false)}
          >
            <BrandMark compact={collapsed} />
          </Link>
          <button
            className="button desktop-only-control h-9 min-h-9 w-9 p-0"
            type="button"
            aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
            onClick={() => setCollapsed((value) => !value)}
          >
            {collapsed ? (
              <ChevronRight className="h-4 w-4" />
            ) : (
              <ChevronLeft className="h-4 w-4" />
            )}
          </button>
          <button
            className="button mobile-only-control h-9 min-h-9 w-9 p-0"
            type="button"
            aria-label="Close navigation"
            onClick={() => setMobileOpen(false)}
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <nav className="flex-1 overflow-y-auto px-2 py-3">
          {navGroups.map((group) => (
            <section
              key={group.label}
              className="mb-5"
              aria-labelledby={`${group.label}-nav`}
            >
              {!collapsed && (
                <h2
                  id={`${group.label}-nav`}
                  className="px-3 pb-2 text-xs font-semibold uppercase tracking-normal text-[var(--graphite)]"
                >
                  {group.label}
                </h2>
              )}
              {group.items.map((item) => {
                const Icon = item.icon;
                const active = pathname === item.href;
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    onClick={() => setMobileOpen(false)}
                    className={`nav-link ${active ? "nav-link-active" : ""}`}
                    title={item.label}
                    aria-current={active ? "page" : undefined}
                  >
                    <Icon className="h-4 w-4 shrink-0" aria-hidden />
                    {!collapsed && <span>{item.label}</span>}
                  </Link>
                );
              })}
            </section>
          ))}
        </nav>

        <div className="border-t border-[var(--border)] p-3">
          {!collapsed && (
            <div className="space-y-3">
              <StatusIndicator />
              <p className="text-xs leading-5 text-[var(--graphite)]">
                {auth.admin
                  ? "Admin controls visible"
                  : auth.authenticated
                    ? "Signed-in workspace"
                    : "Public demo access"}
              </p>
            </div>
          )}
        </div>
      </aside>

      <div className="main-workspace">
        <header className="page-header">
          <div className="workspace-inner flex flex-wrap items-start justify-between gap-4 py-4">
            <div className="flex min-w-0 gap-3">
              <button
                className="button mobile-only-control h-10 min-h-10 w-10 p-0"
                type="button"
                aria-label="Open navigation"
                onClick={() => setMobileOpen(true)}
              >
                <Menu className="h-4 w-4" />
              </button>
              <div className="min-w-0">
                <h1 className="page-title">{title}</h1>
                <p className="page-description mt-1">{description}</p>
              </div>
            </div>
            {actions && (
              <div className="flex shrink-0 flex-wrap gap-2">{actions}</div>
            )}
          </div>
        </header>
        <main id="main-content" className="workspace-inner" tabIndex={-1}>
          {children}
        </main>
      </div>
    </div>
  );
}
