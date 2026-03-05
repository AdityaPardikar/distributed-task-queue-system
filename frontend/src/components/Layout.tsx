import React, { useState, useEffect, useCallback } from "react";
import {
  Outlet,
  NavLink as RouterNavLink,
  useNavigate,
  useLocation,
} from "react-router-dom";
import {
  Menu,
  X,
  Search,
  LayoutDashboard,
  ClipboardList,
  Mail,
  FileText,
  Cpu,
  BarChart3,
  Zap,
  Bell,
  Settings,
  LogOut,
  ChevronRight,
} from "lucide-react";
import { useAuth } from "../context/AuthContext";
import NotificationCenter from "./NotificationCenter";
import GlobalSearch from "./GlobalSearch";

// ── nav items ──────────────────────────────────────────────────────────────
const NAV_ITEMS = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/tasks", label: "Tasks", icon: ClipboardList },
  { to: "/campaigns", label: "Campaigns", icon: Mail },
  { to: "/templates", label: "Templates", icon: FileText },
  { to: "/workers", label: "Workers", icon: Cpu },
  { to: "/monitoring", label: "Monitoring", icon: BarChart3 },
  { to: "/workflows", label: "Workflows", icon: Zap },
  { to: "/alerts", label: "Alerts", icon: Bell },
  { to: "/settings", label: "Settings", icon: Settings },
] as const;

// ── sidebar nav link ───────────────────────────────────────────────────────
interface SideNavLinkProps {
  to: string;
  label: string;
  icon: React.FC<{ size?: number; className?: string }>;
  onClick?: () => void;
}

const SideNavLink: React.FC<SideNavLinkProps> = ({
  to,
  label,
  icon: Icon,
  onClick,
}) => {
  const location = useLocation();
  const isActive =
    location.pathname === to || location.pathname.startsWith(to + "/");

  return (
    <RouterNavLink
      to={to}
      onClick={onClick}
      className={`group flex items-center gap-3 px-3 py-2.5 rounded-xl text-[13px] font-medium transition-all duration-200
        ${
          isActive
            ? "bg-primary-50 text-primary-700 shadow-sm shadow-primary-100"
            : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
        }`}
    >
      <Icon
        size={18}
        className={`flex-shrink-0 transition-colors ${
          isActive
            ? "text-primary-600"
            : "text-slate-400 group-hover:text-slate-600"
        }`}
      />
      <span className="flex-1">{label}</span>
      {isActive && <ChevronRight size={14} className="text-primary-400" />}
    </RouterNavLink>
  );
};

// ═══════════════════════════════════════════════════════════ Layout ═════════
const Layout: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [searchOpen, setSearchOpen] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const closeSidebar = () => setSidebarOpen(false);

  const handleGlobalKeyDown = useCallback((e: KeyboardEvent) => {
    if ((e.metaKey || e.ctrlKey) && e.key === "k") {
      e.preventDefault();
      setSearchOpen((v) => !v);
    }
    if (e.key === "Escape") setSidebarOpen(false);
  }, []);

  useEffect(() => {
    document.addEventListener("keydown", handleGlobalKeyDown);
    return () => document.removeEventListener("keydown", handleGlobalKeyDown);
  }, [handleGlobalKeyDown]);

  useEffect(() => {
    document.body.style.overflow = sidebarOpen ? "hidden" : "";
    return () => {
      document.body.style.overflow = "";
    };
  }, [sidebarOpen]);

  const roleBadge = (role?: string) => {
    const map: Record<string, string> = {
      admin: "bg-violet-100 text-violet-700",
      operator: "bg-sky-100 text-sky-700",
    };
    return map[role ?? ""] ?? "bg-slate-100 text-slate-600";
  };

  const SidebarContent = (
    <div className="flex flex-col h-full">
      {/* Logo area */}
      <div className="flex items-center justify-between px-5 py-5 flex-shrink-0">
        <div className="flex items-center gap-2.5">
          <div className="w-9 h-9 bg-gradient-to-br from-primary-500 to-violet-600 rounded-xl flex items-center justify-center shadow-md shadow-primary-500/20">
            <Zap className="w-[18px] h-[18px] text-white" />
          </div>
          <div>
            <h1 className="text-[15px] font-bold text-slate-900 tracking-tight leading-none">
              TaskFlow
            </h1>
            <p className="text-[10px] text-slate-400 mt-0.5 leading-none">
              Task Queue System
            </p>
          </div>
        </div>
        <button
          className="lg:hidden p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors"
          onClick={closeSidebar}
          aria-label="Close sidebar"
        >
          <X size={18} />
        </button>
      </div>

      {/* Divider */}
      <div className="mx-5 border-t border-slate-100" />

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto">
        <p className="px-3 mb-2 text-[10px] font-bold text-slate-400 uppercase tracking-widest">
          Navigation
        </p>
        {NAV_ITEMS.slice(0, 5).map((item) => (
          <SideNavLink key={item.to} {...item} onClick={closeSidebar} />
        ))}

        <div className="pt-4 pb-2">
          <p className="px-3 mb-2 text-[10px] font-bold text-slate-400 uppercase tracking-widest">
            Operations
          </p>
        </div>
        {NAV_ITEMS.slice(5).map((item) => (
          <SideNavLink key={item.to} {...item} onClick={closeSidebar} />
        ))}
      </nav>

      {/* User section */}
      <div className="px-4 py-4 border-t border-slate-100 flex-shrink-0">
        <div className="flex items-center gap-3 mb-3">
          <div className="w-9 h-9 bg-gradient-to-br from-primary-500 to-violet-600 rounded-full flex items-center justify-center text-white font-semibold text-sm flex-shrink-0 shadow-sm">
            {user?.username?.charAt(0).toUpperCase() ?? "?"}
          </div>
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-1.5 flex-wrap">
              <p className="text-sm font-semibold text-slate-900 truncate">
                {user?.username}
              </p>
              <span
                className={`px-1.5 py-0.5 text-[10px] font-bold rounded-md ${roleBadge(user?.role)}`}
              >
                {user?.role}
              </span>
            </div>
            <p className="text-xs text-slate-400 truncate">{user?.email}</p>
          </div>
        </div>
        <button
          onClick={handleLogout}
          className="w-full flex items-center gap-2 px-3 py-2 text-sm text-slate-500 hover:text-red-600 hover:bg-red-50 rounded-xl transition-colors"
        >
          <LogOut size={16} />
          Sign out
        </button>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-20 bg-slate-900/50 backdrop-blur-sm lg:hidden"
          onClick={closeSidebar}
          aria-hidden="true"
        />
      )}

      {/* Desktop sidebar */}
      <aside className="hidden lg:flex fixed inset-y-0 left-0 w-[260px] bg-white border-r border-slate-200/80 flex-col z-30">
        {SidebarContent}
      </aside>

      {/* Mobile sidebar */}
      <aside
        className={`lg:hidden fixed inset-y-0 left-0 w-[280px] bg-white shadow-2xl z-30 transform transition-transform duration-300 ease-out
          ${sidebarOpen ? "translate-x-0" : "-translate-x-full"}`}
        aria-label="Sidebar"
      >
        {SidebarContent}
      </aside>

      {/* Main content */}
      <div className="lg:ml-[260px] flex flex-col min-h-screen">
        {/* Header */}
        <header className="sticky top-0 z-10 bg-white/80 backdrop-blur-lg border-b border-slate-200/60">
          <div className="flex items-center justify-between px-4 sm:px-8 py-3">
            <div className="flex items-center gap-3">
              <button
                className="lg:hidden p-2 rounded-xl text-slate-500 hover:bg-slate-100 transition-colors"
                onClick={() => setSidebarOpen(true)}
                aria-label="Open sidebar"
              >
                <Menu size={20} />
              </button>
              <div className="hidden sm:block">
                <h2 className="text-lg font-bold text-slate-900">
                  Distributed Task Queue
                </h2>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={() => setSearchOpen(true)}
                className="flex items-center gap-2 px-3.5 py-2 text-sm text-slate-400
                           bg-slate-100/80 rounded-xl hover:bg-slate-200/80 transition-colors border border-transparent hover:border-slate-200"
                aria-label="Open search"
              >
                <Search size={15} />
                <span className="hidden md:inline text-slate-400">Search…</span>
                <kbd className="hidden md:inline-flex px-1.5 py-0.5 text-[10px] bg-white border border-slate-200 rounded-md font-mono text-slate-400 ml-2">
                  Ctrl+K
                </kbd>
              </button>
              <NotificationCenter />
            </div>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 p-4 sm:p-6 lg:p-8">
          <Outlet />
        </main>
      </div>

      <GlobalSearch isOpen={searchOpen} onClose={() => setSearchOpen(false)} />
    </div>
  );
};

export default Layout;
