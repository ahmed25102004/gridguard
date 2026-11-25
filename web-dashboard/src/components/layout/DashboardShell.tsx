"use client";

import React, { useState } from "react";
import { useDashboard, NavTab } from "./DashboardContext";
import {
  Zap,
  Layers,
  MapPin,
  Sparkles,
  BookOpen,
  History,
  ShieldCheck,
  Search,
  Bell,
  Sun,
  Moon,
  ChevronDown,
  Activity,
  Menu,
  X,
  Radio,
  SlidersHorizontal,
} from "lucide-react";

export function DashboardShell({ children }: { children: React.ReactNode }) {
  const {
    sidebarOpen,
    toggleSidebar,
    theme,
    toggleTheme,
    activeTab,
    setActiveTab,
    searchQuery,
    setSearchQuery,
  } = useDashboard();

  const [substationMenuOpen, setSubstationMenuOpen] = useState(false);
  const [selectedSubstation, setSelectedSubstation] = useState("Cairo North Primary (220kV)");
  const [notificationsOpen, setNotificationsOpen] = useState(false);

  const navItems: { id: NavTab; label: string; icon: React.ReactNode; group: "operations" | "intelligence"; badge?: string; badgeColor?: string }[] = [
    {
      id: "solutions",
      label: "Solutions Architecture",
      icon: <ShieldCheck className="w-4 h-4" />,
      group: "operations",
      badge: "Smart APM",
      badgeColor: "bg-amber-500/10 text-amber-400 border-amber-500/20",
    },
    {
      id: "inventory",
      label: "Asset Inventory",
      icon: <Layers className="w-4 h-4" />,
      group: "operations",
      badge: "524",
      badgeColor: "bg-blue-500/10 text-blue-400 border-blue-500/20",
    },
    {
      id: "gis",
      label: "Spatial Radar (GIS)",
      icon: <MapPin className="w-4 h-4" />,
      group: "operations",
      badge: "PostGIS",
      badgeColor: "bg-cyan-500/10 text-cyan-400 border-cyan-500/20",
    },
    {
      id: "scada",
      label: "SCADA Telemetry",
      icon: <Activity className="w-4 h-4" />,
      group: "operations",
      badge: "Live",
      badgeColor: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
    },
    {
      id: "rag",
      label: "RAG Manuals AI",
      icon: <Sparkles className="w-4 h-4" />,
      group: "intelligence",
      badge: "3072d",
      badgeColor: "bg-indigo-500/20 text-indigo-300 border-indigo-500/30",
    },
    {
      id: "manuals",
      label: "OEM K-Base (ABB/Siemens)",
      icon: <BookOpen className="w-4 h-4" />,
      group: "intelligence",
      badge: "PDFs",
      badgeColor: "bg-slate-800 text-slate-400 border-slate-700",
    },
    {
      id: "audit",
      label: "Audit & Dispatch",
      icon: <History className="w-4 h-4" />,
      group: "intelligence",
      badge: "3 Alerts",
      badgeColor: "bg-rose-500/15 text-rose-400 border-rose-500/30",
    },
  ];

  return (
    <div className={`min-h-screen flex w-full transition-colors duration-200 ${theme === "dark" ? "bg-[#070b14] text-slate-100" : "bg-slate-50 text-slate-900"}`}>
      {/* Collapsible Left Sidebar */}
      <aside
        className={`fixed inset-y-0 left-0 z-40 flex flex-col justify-between shrink-0 transition-all duration-300 ease-in-out border-r ${
          sidebarOpen ? "w-72 translate-x-0" : "-translate-x-full lg:translate-x-0 lg:w-0 lg:border-transparent lg:overflow-hidden"
        } ${
          theme === "dark"
            ? "bg-[#090d16] border-slate-800"
            : "bg-white border-slate-200"
        }`}
      >
        <div className="p-4 space-y-5 overflow-y-auto w-72">
          {/* Brand Header */}
          <div className="flex items-center justify-between px-2 pt-1">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-xl bg-blue-600 flex items-center justify-center text-white shadow-sm shrink-0">
                <Zap className="w-5 h-5 fill-white text-white" />
              </div>
              <div>
                <div className="flex items-center gap-1.5">
                  <span className={`font-bold tracking-tight text-base ${theme === "dark" ? "text-white" : "text-slate-900"}`}>
                    GridGuard
                  </span>
                  <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-700">
                    APM
                  </span>
                </div>
                <p className="text-[11px] text-slate-500 dark:text-slate-400 font-normal">
                  Substation Asset Intelligence
                </p>
              </div>
            </div>

            {/* Mobile close sidebar button */}
            <button
              onClick={toggleSidebar}
              className="lg:hidden p-1.5 rounded-lg text-slate-400 hover:text-white"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Substation Scope Selector Dropdown */}
          <div className="relative">
            <button
              onClick={() => setSubstationMenuOpen(!substationMenuOpen)}
              className={`w-full p-2.5 rounded-xl border flex items-center justify-between transition cursor-pointer text-left ${
                theme === "dark"
                  ? "bg-slate-900/90 border-slate-800 hover:border-slate-700"
                  : "bg-slate-50 border-slate-200 hover:border-slate-300"
              }`}
            >
              <div className="flex items-center gap-2.5 min-w-0">
                <div className="w-8 h-8 rounded-lg bg-blue-600/20 border border-blue-500/30 text-blue-400 font-bold text-xs flex items-center justify-center font-mono shrink-0">
                  CA
                </div>
                <div className="truncate">
                  <h4 className={`text-xs font-bold truncate ${theme === "dark" ? "text-slate-200" : "text-slate-900"}`}>
                    {selectedSubstation}
                  </h4>
                  <p className="text-[10px] text-slate-400 font-mono">
                    524 assets · 2 zones
                  </p>
                </div>
              </div>
              <ChevronDown className={`w-3.5 h-3.5 text-slate-400 shrink-0 transition-transform ${substationMenuOpen ? "rotate-180" : ""}`} />
            </button>

            {/* Dropdown Options */}
            {substationMenuOpen && (
              <div className={`absolute top-full left-0 right-0 mt-1.5 p-1 rounded-xl border shadow-xl z-50 text-xs ${
                theme === "dark" ? "bg-slate-900 border-slate-700 text-slate-200" : "bg-white border-slate-200 text-slate-800"
              }`}>
                <button
                  onClick={() => {
                    setSelectedSubstation("Cairo North Primary (220kV)");
                    setSubstationMenuOpen(false);
                  }}
                  className={`w-full px-3 py-2 text-left rounded-lg transition font-medium flex items-center justify-between ${
                    selectedSubstation.includes("Cairo")
                      ? "bg-blue-600 text-white font-bold"
                      : "hover:bg-slate-800/40"
                  }`}
                >
                  <span>Cairo North Primary (SUB-CAI-01)</span>
                  <span className="font-mono text-[10px]">220kV</span>
                </button>
                <button
                  onClick={() => {
                    setSelectedSubstation("Alexandria Industrial (132kV)");
                    setSubstationMenuOpen(false);
                  }}
                  className={`w-full px-3 py-2 text-left rounded-lg transition font-medium flex items-center justify-between ${
                    selectedSubstation.includes("Alexandria")
                      ? "bg-blue-600 text-white font-bold"
                      : "hover:bg-slate-800/40"
                  }`}
                >
                  <span>Alexandria Industrial (SUB-ALX-02)</span>
                  <span className="font-mono text-[10px]">132kV</span>
                </button>
              </div>
            )}
          </div>

          {/* Navigation Menus */}
          <nav className="space-y-5 text-xs font-semibold">
            {/* Grid Operations Group */}
            <div className="space-y-1">
              <span className="px-2.5 text-[10px] font-bold tracking-wider uppercase text-slate-500">
                Grid Operations
              </span>
              {navItems.filter((i) => i.group === "operations").map((item) => {
                const isActive = activeTab === item.id;
                return (
                  <button
                    key={item.id}
                    onClick={() => setActiveTab(item.id)}
                    className={`w-full flex items-center justify-between px-3 py-2.5 rounded-xl transition text-left ${
                      isActive
                        ? "bg-gradient-to-r from-blue-600/20 to-blue-500/10 text-blue-400 border border-blue-500/30 shadow-sm font-bold"
                        : theme === "dark"
                        ? "text-slate-400 hover:text-slate-200 hover:bg-slate-900/60"
                        : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
                    }`}
                  >
                    <div className="flex items-center gap-2.5">
                      {item.icon}
                      <span>{item.label}</span>
                    </div>
                    {item.badge && (
                      <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded border ${item.badgeColor}`}>
                        {item.badge}
                      </span>
                    )}
                  </button>
                );
              })}
            </div>

            {/* AI & Diagnostics Group */}
            <div className="space-y-1">
              <span className="px-2.5 text-[10px] font-bold tracking-wider uppercase text-slate-500">
                Intelligence & Safety
              </span>
              {navItems.filter((i) => i.group === "intelligence").map((item) => {
                const isActive = activeTab === item.id;
                return (
                  <button
                    key={item.id}
                    onClick={() => setActiveTab(item.id)}
                    className={`w-full flex items-center justify-between px-3 py-2.5 rounded-xl transition text-left ${
                      isActive
                        ? "bg-gradient-to-r from-blue-600/20 to-blue-500/10 text-blue-400 border border-blue-500/30 shadow-sm font-bold"
                        : theme === "dark"
                        ? "text-slate-400 hover:text-slate-200 hover:bg-slate-900/60"
                        : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
                    }`}
                  >
                    <div className="flex items-center gap-2.5">
                      {item.icon}
                      <span>{item.label}</span>
                    </div>
                    {item.badge && (
                      <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded border ${item.badgeColor}`}>
                        {item.badge}
                      </span>
                    )}
                  </button>
                );
              })}
            </div>
          </nav>
        </div>

        {/* Bottom Platform Card */}
        <div className="p-4 border-t border-slate-800/60">
          <div className={`p-3 rounded-2xl border ${
            theme === "dark" ? "bg-slate-950 border-slate-800/80" : "bg-slate-100 border-slate-200"
          }`}>
            <div className="flex items-center gap-2 font-bold text-xs mb-1">
              <ShieldCheck className="w-4 h-4 text-blue-500" />
              <span className={theme === "dark" ? "text-white" : "text-slate-900"}>GridGuard 2.0</span>
            </div>
            <p className="text-[11px] text-slate-400 leading-relaxed">
              Autonomous grid defense and AI asset health verification.
            </p>
          </div>
        </div>
      </aside>

      {/* Main Container (Expands when sidebar is toggled!) */}
      <div
        className={`flex-1 flex flex-col min-w-0 transition-all duration-300 ease-in-out ${
          sidebarOpen ? "lg:pl-72" : "pl-0"
        }`}
      >
        {/* Top Header Bar */}
        <header
          className={`sticky top-0 z-30 h-16 border-b px-4 lg:px-8 flex items-center justify-between gap-4 transition-colors ${
            theme === "dark"
              ? "bg-[#070b14]/90 border-slate-800/80 backdrop-blur-md"
              : "bg-white/90 border-slate-200 backdrop-blur-md shadow-sm"
          }`}
        >
          {/* Left: Sidebar Toggle Hamburger Button + Active Tab Badge */}
          <div className="flex items-center gap-3">
            <button
              onClick={toggleSidebar}
              className={`p-2 rounded-xl border transition ${
                theme === "dark"
                  ? "border-slate-800 bg-slate-900/80 text-slate-300 hover:text-white hover:bg-slate-800"
                  : "border-slate-200 bg-slate-100 text-slate-700 hover:text-slate-950 hover:bg-slate-200"
              }`}
              title={sidebarOpen ? "Hide sidebar" : "Show sidebar"}
            >
              <Menu className="w-4 h-4" />
            </button>

            <div className="hidden sm:flex items-center gap-2 text-xs font-semibold">
              <span className="text-slate-400">View:</span>
              <span className="capitalize px-2 py-0.5 rounded-md bg-blue-500/10 text-blue-400 border border-blue-500/20 font-mono">
                {activeTab}
              </span>
            </div>
          </div>

          {/* Middle: Active Global Search Bar */}
          <div className="relative max-w-lg w-full flex-1 mx-2">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              id="global-search-input"
              type="text"
              placeholder="Search assets, telemetry, manuals, or press ⌘K..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className={`w-full pl-10 pr-12 py-2 text-xs rounded-xl border focus:outline-none focus:ring-1 focus:ring-blue-500 transition ${
                theme === "dark"
                  ? "bg-slate-950/80 border-slate-800 text-slate-200 focus:border-blue-500"
                  : "bg-slate-100 border-slate-200 text-slate-900 focus:border-blue-600 focus:bg-white"
              }`}
            />
            <span className="absolute right-3 top-1/2 -translate-y-1/2 text-[10px] font-mono text-slate-400 bg-slate-800/80 px-1.5 py-0.5 rounded border border-slate-700/60 hidden sm:inline-block">
              ⌘K
            </span>
          </div>

          {/* Right: Actions, Notifications, Theme Toggle & Avatar */}
          <div className="flex items-center gap-2.5">
            {/* Quick Tab Switcher Button */}
            <button
              onClick={() => setActiveTab(activeTab === "rag" ? "inventory" : "rag")}
              className="hidden md:flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-xs font-medium shadow-sm transition"
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>{activeTab === "rag" ? "View Inventory" : "RAG Assistant"}</span>
            </button>

            {/* Notification Bell with Toggleable Popover */}
            <div className="relative">
              <button
                onClick={() => setNotificationsOpen(!notificationsOpen)}
                className={`relative p-2 rounded-xl border transition ${
                  theme === "dark"
                    ? "border-slate-800 bg-slate-900/80 text-slate-300 hover:text-white"
                    : "border-slate-200 bg-slate-100 text-slate-700 hover:text-slate-950"
                }`}
                title="Notifications"
              >
                <Bell className="w-4 h-4" />
                <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-blue-500"></span>
              </button>

              {notificationsOpen && (
                <div className={`absolute right-0 mt-2 w-80 p-3 rounded-2xl border shadow-2xl z-50 text-xs space-y-2 ${
                  theme === "dark" ? "bg-slate-900 border-slate-700 text-slate-200" : "bg-white border-slate-200 text-slate-900"
                }`}>
                  <div className="flex items-center justify-between border-b pb-2 border-slate-800 font-bold">
                    <span>Substation Notifications</span>
                    <span className="text-[10px] text-blue-400 font-mono">3 New</span>
                  </div>
                  <div className="space-y-1.5">
                    <div className="p-2 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-300">
                      <strong>Critical:</strong> SF6 gas low pressure on AST-SWT-010.
                    </div>
                    <div className="p-2 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-300">
                      <strong>Maintenance:</strong> OTI/WTI calibration due for AST-TRF-002.
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Working Light / Dark Theme Toggle! */}
            <button
              onClick={toggleTheme}
              className={`p-2 rounded-xl border transition ${
                theme === "dark"
                  ? "border-slate-800 bg-slate-900/80 text-amber-400 hover:text-amber-300 hover:bg-slate-800"
                  : "border-slate-200 bg-slate-100 text-slate-700 hover:text-slate-950 hover:bg-slate-200"
              }`}
              title={theme === "dark" ? "Switch to Light Mode" : "Switch to Dark Mode"}
            >
              {theme === "dark" ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
            </button>

            {/* User Profile Avatar Pill */}
            <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-cyan-500 to-blue-600 text-white font-bold text-xs flex items-center justify-center shadow-md">
              AM
            </div>
          </div>
        </header>

        {/* Page Content Viewport */}
        <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-[1700px] w-full mx-auto">
          {children}
        </main>
      </div>
    </div>
  );
}
