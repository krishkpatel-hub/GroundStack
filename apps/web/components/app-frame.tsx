"use client";

import {
  ChevronLeft,
  ChevronRight,
  FileText,
  History,
  Home,
  Menu,
  MessageSquare,
  Settings,
  UploadCloud,
  X,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { type ReactNode, useEffect, useMemo, useRef, useState } from "react";

import { BrandMark } from "@/components/brand-mark";
import { fetchAuthInfo, type AuthInfo } from "@/lib/auth";

type AppFrameProps = {
  title: string;
  description: string;
  actions?: ReactNode;
  children: ReactNode;
  requireAdmin?: boolean;
};

const publicItems = [
  { href: "/", label: "Overview", icon: Home },
  { href: "/ask", label: "Ask", icon: MessageSquare },
  { href: "/about", label: "How it works", icon: FileText },
];

const userItems = [{ href: "/conversations", label: "History", icon: History }];

const adminItems = [
  { href: "/knowledge", label: "Documents", icon: UploadCloud },
  { href: "/settings", label: "Health", icon: Settings },
];

export function AppFrame({
  title,
  description,
  actions,
  children,
  requireAdmin = false,
}: AppFrameProps) {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [mobileViewport, setMobileViewport] = useState(false);
  const sidebarRef = useRef<HTMLElement | null>(null);
  const menuButtonRef = useRef<HTMLButtonElement | null>(null);
  const [auth, setAuth] = useState<AuthInfo>({
    authenticated: false,
    anonymous: true,
    roles: [],
    admin: false,
  });
  const [authLoaded, setAuthLoaded] = useState(false);

  useEffect(() => {
    const controller = new AbortController();
    void fetchAuthInfo(controller.signal)
      .then((nextAuth) => {
        setAuth(nextAuth);
        setAuthLoaded(true);
      })
      .catch(() => {
        setAuth({
          authenticated: false,
          anonymous: true,
          roles: [],
          admin: false,
        });
        setAuthLoaded(true);
      });
    return () => controller.abort();
  }, []);

  useEffect(() => {
    const media = window.matchMedia("(max-width: 767px)");
    const updateViewport = () => setMobileViewport(media.matches);
    updateViewport();
    media.addEventListener("change", updateViewport);
    return () => media.removeEventListener("change", updateViewport);
  }, []);

  useEffect(() => {
    if (!mobileOpen || !mobileViewport) return;
    const sidebar = sidebarRef.current;
    const focusable = Array.from(
      sidebar?.querySelectorAll<HTMLElement>(
        'a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])',
      ) ?? [],
    );
    focusable[0]?.focus();
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setMobileOpen(false);
        window.requestAnimationFrame(() => menuButtonRef.current?.focus());
        return;
      }
      if (event.key !== "Tab" || focusable.length === 0) return;
      const first = focusable[0];
      const last = focusable.at(-1);
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last?.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    }
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [mobileOpen, mobileViewport]);

  function closeMobileNavigation() {
    setMobileOpen(false);
    window.requestAnimationFrame(() => menuButtonRef.current?.focus());
  }

  const navGroups = useMemo(() => {
    const groups = [{ label: "Product", items: publicItems }];
    if (auth.authenticated) groups.push({ label: "Account", items: userItems });
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
          onClick={closeMobileNavigation}
        />
      )}
      <aside
        ref={sidebarRef}
        className={`sidebar ${collapsed ? "sidebar-collapsed" : ""} ${
          mobileOpen ? "sidebar-open" : ""
        }`}
        aria-label="Primary navigation"
        inert={mobileViewport && !mobileOpen ? true : undefined}
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
            onClick={closeMobileNavigation}
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
            <p className="text-xs leading-5 text-[var(--graphite)]">
              {auth.admin
                ? "Admin controls visible"
                : auth.authenticated
                  ? "Signed-in workspace"
                  : "Guest access"}
            </p>
          )}
        </div>
      </aside>

      <div className="main-workspace">
        <header className="page-header">
          <div className="workspace-inner page-header-inner">
            <div className="page-heading">
              <button
                ref={menuButtonRef}
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
            {actions && (!requireAdmin || auth.admin) && (
              <div className="page-actions">{actions}</div>
            )}
          </div>
        </header>
        <main
          id="main-content"
          className="workspace-inner workspace-content"
          tabIndex={-1}
        >
          {requireAdmin && !authLoaded ? (
            <div className="empty-chat">
              <h2 className="text-xl font-semibold">Checking access</h2>
              <p className="mt-2 max-w-2xl text-sm leading-6 text-[var(--graphite)]">
                GroundStack is verifying whether this session can manage
                documents.
              </p>
            </div>
          ) : requireAdmin && !auth.admin ? (
            <div className="empty-chat" role="alert">
              <h2 className="text-xl font-semibold">Admin access required</h2>
              <p className="mt-2 max-w-2xl text-sm leading-6 text-[var(--graphite)]">
                Document management is available only to administrators. You can
                still ask questions from approved documentation.
              </p>
              <div className="mt-4 flex flex-wrap gap-2">
                <Link
                  className="button button-primary no-underline"
                  href="/ask"
                >
                  Return to Ask
                </Link>
              </div>
            </div>
          ) : (
            children
          )}
        </main>
      </div>
    </div>
  );
}
