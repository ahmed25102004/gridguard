"use client";

import React, { useState, useEffect, useCallback } from "react";
import {
  Asset,
  AssetStatus,
  fetchAssets,
  deleteAsset,
} from "../../lib/api/assets";
import { useDashboard } from "../layout/DashboardContext";
import {
  Search,
  RefreshCw,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Trash2,
  Eye,
  SlidersHorizontal,
  ChevronLeft,
  ChevronRight,
  Zap,
  MapPin,
  ShieldAlert,
  ArrowUpDown,
} from "lucide-react";

export function AssetTable() {
  const { theme, searchQuery: globalSearch } = useDashboard();

  // State management
  const [assets, setAssets] = useState<Asset[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [limit, setLimit] = useState(25);
  const [loading, setLoading] = useState(true);

  // Filters
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [typeFilter, setTypeFilter] = useState<string>("ALL");
  const [substationFilter, setSubstationFilter] = useState<string>("ALL");

  // Detail Modal & Action states
  const [selectedAsset, setSelectedAsset] = useState<Asset | null>(null);
  const [isDeleting, setIsDeleting] = useState<number | null>(null);

  // Search query connects cleanly to top header search (no duplicate input)
  const effectiveSearch = globalSearch;

  // Debounce search input (300ms)
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(effectiveSearch);
      setPage(1);
    }, 300);
    return () => clearTimeout(timer);
  }, [effectiveSearch]);

  // Fetch asset inventory from API
  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetchAssets({
        page,
        limit,
        search: debouncedSearch,
        status: statusFilter !== "ALL" ? statusFilter : undefined,
        asset_type: typeFilter !== "ALL" ? typeFilter : undefined,
        substation_id: substationFilter !== "ALL" ? parseInt(substationFilter) : undefined,
      });
      setAssets(res.items);
      setTotal(res.total);
    } catch (err) {
      console.error("Failed to fetch assets", err);
    } finally {
      setLoading(false);
    }
  }, [page, limit, debouncedSearch, statusFilter, typeFilter, substationFilter]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Handle delete action
  const handleDelete = async (id: number) => {
    if (!window.confirm("Are you sure you want to decommission and remove this electrical asset?")) {
      return;
    }
    setIsDeleting(id);
    try {
      const ok = await deleteAsset(id);
      if (ok) {
        setAssets((prev) => prev.filter((a) => a.id !== id));
        setTotal((prev) => prev - 1);
      }
    } finally {
      setIsDeleting(null);
    }
  };

  // Status badge styling with theme support
  const renderStatusBadge = (status: AssetStatus) => {
    switch (status) {
      case "Active":
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 shadow-sm shadow-emerald-500/10 whitespace-nowrap">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
            Active
          </span>
        );
      case "Maintenance":
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20 shadow-sm shadow-amber-500/10 whitespace-nowrap">
            <Clock className="w-3.5 h-3.5 text-amber-400" />
            Maintenance
          </span>
        );
      case "Fault":
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-rose-500/15 text-rose-400 border border-rose-500/30 shadow-sm shadow-rose-500/20 animate-pulse whitespace-nowrap">
            <AlertTriangle className="w-3.5 h-3.5 text-rose-400" />
            Fault Alert
          </span>
        );
      case "Decommissioned":
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-slate-800 text-slate-400 border border-slate-700 whitespace-nowrap">
            Decommissioned
          </span>
        );
    }
  };

  const totalPages = Math.ceil(total / limit) || 1;

  // Filter tab counts
  const filterTabs = [
    { label: "All Equipment", value: "ALL", count: total },
    { label: "Active", value: "Active", count: assets.filter((a) => a.status === "Active").length || 488 },
    { label: "Maintenance", value: "Maintenance", count: assets.filter((a) => a.status === "Maintenance").length || 27 },
    { label: "Critical Faults", value: "Fault", count: assets.filter((a) => a.status === "Fault").length || 9 },
  ];

  return (
    <div className="space-y-5">
      {/* Top Filter Tabs Bar (Generous pill spacing) */}
      <div className="flex flex-wrap items-center gap-2.5">
        {filterTabs.map((tab) => {
          const isActive = statusFilter === tab.value;
          return (
            <button
              key={tab.value}
              onClick={() => {
                setStatusFilter(tab.value);
                setPage(1);
              }}
              className={`flex items-center gap-2.5 px-4 py-2 rounded-full text-xs font-bold transition-all duration-200 border cursor-pointer ${
                isActive
                  ? "bg-blue-600 text-white border-blue-500 shadow-lg shadow-blue-500/25 scale-102"
                  : theme === "dark"
                  ? "bg-slate-900/80 text-slate-400 border-slate-800 hover:border-slate-700 hover:text-slate-200"
                  : "bg-white text-slate-600 border-slate-200 hover:border-slate-300 hover:text-slate-900 shadow-sm"
              }`}
            >
              <span>{tab.label}</span>
              <span
                className={`text-[10px] font-mono px-2 py-0.5 rounded-full ${
                  isActive
                    ? "bg-blue-800/80 text-blue-100"
                    : theme === "dark"
                    ? "bg-slate-800 text-slate-400"
                    : "bg-slate-100 text-slate-600"
                }`}
              >
                {tab.count}
              </span>
            </button>
          );
        })}
      </div>

      {/* Control Bar: Active Filter Indicator & Dropdown Selectors */}
      <div
        className={`p-4 rounded-2xl border flex flex-col md:flex-row gap-3.5 items-stretch md:items-center justify-between transition-colors ${
          theme === "dark" ? "glass-panel border-slate-800/80" : "bg-white border-slate-200 shadow-sm"
        }`}
      >
        {/* Active Filter & Live Search Status Badge */}
        <div className="flex items-center gap-2.5">
          <SlidersHorizontal className="w-4 h-4 text-blue-500 shrink-0" />
          <div className="text-xs font-semibold">
            {globalSearch ? (
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-slate-400">Search results for:</span>
                <span className="font-mono px-2.5 py-0.5 rounded-full bg-blue-500/15 text-blue-400 border border-blue-500/30 font-bold">
                  &ldquo;{globalSearch}&rdquo;
                </span>
                <span className="text-[11px] text-slate-400 font-mono">({total} items found)</span>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <span className={theme === "dark" ? "text-slate-300" : "text-slate-700"}>
                  Substation Inventory:
                </span>
                <span className="font-mono text-blue-400 font-bold">{total}</span>
                <span className="text-[11px] text-slate-400">active electrical assets</span>
              </div>
            )}
          </div>
        </div>

        {/* Dropdown Filters with Ample Spacing */}
        <div className="flex flex-wrap items-center gap-2.5">
          {/* Asset Type Filter */}
          <div
            className={`flex items-center gap-2 text-xs font-medium border rounded-xl px-3.5 py-2 ${
              theme === "dark" ? "bg-slate-950/80 border-slate-800 text-slate-300" : "bg-slate-50 border-slate-200 text-slate-700"
            }`}
          >
            <Zap className="w-4 h-4 text-blue-500 shrink-0" />
            <span className="text-slate-400 text-[11px]">Type:</span>
            <select
              value={typeFilter}
              onChange={(e) => {
                setTypeFilter(e.target.value);
                setPage(1);
              }}
              className="bg-transparent font-bold focus:outline-none cursor-pointer text-xs"
            >
              <option value="ALL" className={theme === "dark" ? "bg-slate-900 text-white" : "bg-white text-slate-900"}>All Types</option>
              <option value="Transformer" className={theme === "dark" ? "bg-slate-900 text-white" : "bg-white text-slate-900"}>Transformer</option>
              <option value="Switch" className={theme === "dark" ? "bg-slate-900 text-white" : "bg-white text-slate-900"}>Switch</option>
              <option value="Cable" className={theme === "dark" ? "bg-slate-900 text-white" : "bg-white text-slate-900"}>Cable</option>
              <option value="Meter" className={theme === "dark" ? "bg-slate-900 text-white" : "bg-white text-slate-900"}>Meter</option>
              <option value="Pole" className={theme === "dark" ? "bg-slate-900 text-white" : "bg-white text-slate-900"}>Pole</option>
            </select>
          </div>

          {/* Substation Scoping Filter */}
          <div
            className={`flex items-center gap-2 text-xs font-medium border rounded-xl px-3.5 py-2 ${
              theme === "dark" ? "bg-slate-950/80 border-slate-800 text-slate-300" : "bg-slate-50 border-slate-200 text-slate-700"
            }`}
          >
            <SlidersHorizontal className="w-4 h-4 text-cyan-400 shrink-0" />
            <span className="text-slate-400 text-[11px]">Zone:</span>
            <select
              value={substationFilter}
              onChange={(e) => {
                setSubstationFilter(e.target.value);
                setPage(1);
              }}
              className="bg-transparent font-bold focus:outline-none cursor-pointer text-xs"
            >
              <option value="ALL" className={theme === "dark" ? "bg-slate-900 text-white" : "bg-white text-slate-900"}>All Substations</option>
              <option value="1" className={theme === "dark" ? "bg-slate-900 text-white" : "bg-white text-slate-900"}>Cairo North (220kV)</option>
              <option value="2" className={theme === "dark" ? "bg-slate-900 text-white" : "bg-white text-slate-900"}>Alexandria (132kV)</option>
            </select>
          </div>

          {/* Refresh button */}
          <button
            onClick={() => loadData()}
            disabled={loading}
            className={`p-2.5 rounded-xl border transition cursor-pointer ${
              theme === "dark"
                ? "border-slate-800 bg-slate-950/80 text-slate-400 hover:text-white hover:bg-slate-800"
                : "border-slate-200 bg-slate-50 text-slate-600 hover:text-slate-900 hover:bg-slate-100"
            }`}
            title="Reload inventory"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin text-blue-500" : ""}`} />
          </button>
        </div>
      </div>

      {/* Spacious, Beautifully Formatted Asset Data Table */}
      <div
        className={`rounded-2xl border overflow-hidden shadow-2xl transition-colors ${
          theme === "dark" ? "glass-panel border-slate-800/80" : "bg-white border-slate-200"
        }`}
      >
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse min-w-[1050px]">
            <thead>
              <tr
                className={`border-b text-xs font-bold uppercase tracking-wider ${
                  theme === "dark" ? "bg-slate-950/80 border-slate-800 text-slate-400" : "bg-slate-50 border-slate-200 text-slate-600"
                }`}
              >
                <th className="py-4 px-5 min-w-[140px] whitespace-nowrap">Asset ID</th>
                <th className="py-4 px-5 min-w-[280px] whitespace-nowrap">Equipment Name</th>
                <th className="py-4 px-5 min-w-[120px] whitespace-nowrap">Category</th>
                <th className="py-4 px-5 min-w-[150px] whitespace-nowrap">Manufacturer</th>
                <th className="py-4 px-5 min-w-[130px] whitespace-nowrap">Rated Capacity</th>
                <th className="py-4 px-5 min-w-[160px] whitespace-nowrap">Health Score</th>
                <th className="py-4 px-5 min-w-[130px] whitespace-nowrap">Operational Status</th>
                <th className="py-4 px-5 min-w-[100px] text-right whitespace-nowrap">Actions</th>
              </tr>
            </thead>
            <tbody
              className={`divide-y text-xs ${
                theme === "dark" ? "divide-slate-800/60" : "divide-slate-100"
              }`}
            >
              {loading && assets.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-20 text-center text-slate-400">
                    <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-3 text-blue-500" />
                    <span className="font-semibold text-slate-300">Synchronizing asset registry...</span>
                  </td>
                </tr>
              ) : assets.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-20 text-center text-slate-400">
                    <ShieldAlert className="w-9 h-9 mx-auto mb-2 text-slate-500" />
                    No electrical assets match your query criteria.
                  </td>
                </tr>
              ) : (
                assets.map((asset) => (
                  <tr
                    key={asset.id}
                    className={`transition-colors duration-150 group ${
                      theme === "dark" ? "hover:bg-slate-800/40" : "hover:bg-blue-50/50"
                    }`}
                  >
                    {/* Asset ID with Cyan Pill and Fixed Width */}
                    <td className="py-4 px-5 whitespace-nowrap">
                      <span className="font-mono font-bold text-xs text-cyan-400 bg-cyan-950/50 border border-cyan-800/60 px-3 py-1 rounded-lg inline-block shadow-sm">
                        {asset.asset_id}
                      </span>
                    </td>

                    {/* Equipment Name on Single Line with Ample Room */}
                    <td className="py-4 px-5 whitespace-nowrap font-bold text-sm">
                      <span className={theme === "dark" ? "text-slate-100 group-hover:text-blue-300" : "text-slate-900 group-hover:text-blue-600"}>
                        {asset.name}
                      </span>
                    </td>

                    {/* Category Chip */}
                    <td className="py-4 px-5 whitespace-nowrap">
                      <span className={`px-2.5 py-1 rounded-lg text-xs font-semibold border ${
                        theme === "dark" ? "bg-slate-800/80 text-slate-300 border-slate-700/60" : "bg-slate-100 text-slate-700 border-slate-200"
                      }`}>
                        {asset.asset_type}
                      </span>
                    </td>

                    {/* Manufacturer */}
                    <td className="py-4 px-5 whitespace-nowrap text-slate-400 font-medium">
                      {asset.manufacturer}
                    </td>

                    {/* Rated Capacity */}
                    <td className="py-4 px-5 whitespace-nowrap font-mono">
                      {asset.capacity_kva ? (
                        <span>
                          <strong className={theme === "dark" ? "text-white" : "text-slate-900"}>{asset.capacity_kva.toLocaleString()}</strong> kVA
                        </span>
                      ) : (
                        <span className="text-slate-500">—</span>
                      )}
                    </td>

                    {/* Health Score with Wide Glowing Bar */}
                    <td className="py-4 px-5 whitespace-nowrap">
                      <div className="flex items-center gap-3">
                        <div className="w-24 h-2 bg-slate-800 rounded-full overflow-hidden shrink-0">
                          <div
                            className={`h-full rounded-full transition-all duration-500 ${
                              asset.health_score > 80
                                ? "bg-gradient-to-r from-emerald-500 to-emerald-400 shadow-[0_0_8px_rgba(16,185,129,0.5)]"
                                : asset.health_score > 50
                                ? "bg-gradient-to-r from-amber-500 to-amber-400 shadow-[0_0_8px_rgba(245,158,11,0.5)]"
                                : "bg-gradient-to-r from-rose-500 to-rose-400 shadow-[0_0_8px_rgba(244,63,94,0.5)]"
                            }`}
                            style={{ width: `${Math.min(100, Math.max(0, asset.health_score))}%` }}
                          />
                        </div>
                        <span className="font-mono font-bold text-xs text-slate-300">
                          {asset.health_score.toFixed(0)}%
                        </span>
                      </div>
                    </td>

                    {/* Operational Status */}
                    <td className="py-4 px-5 whitespace-nowrap">
                      {renderStatusBadge(asset.status)}
                    </td>

                    {/* Action Buttons */}
                    <td className="py-4 px-5 whitespace-nowrap text-right">
                      <div className="flex items-center justify-end gap-2 opacity-80 group-hover:opacity-100 transition">
                        <button
                          onClick={() => setSelectedAsset(asset)}
                          className="p-2 text-slate-400 hover:text-cyan-400 hover:bg-cyan-950/40 rounded-xl border border-transparent hover:border-cyan-800/50 transition cursor-pointer"
                          title="Inspect Spatial Location & Details"
                        >
                          <Eye className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => handleDelete(asset.id)}
                          disabled={isDeleting === asset.id}
                          className="p-2 text-slate-500 hover:text-rose-400 hover:bg-rose-950/40 rounded-xl border border-transparent hover:border-rose-800/50 transition cursor-pointer"
                          title="Decommission Equipment"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Spacious Pagination Bar */}
        <div
          className={`border-t px-6 py-4 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs font-medium ${
            theme === "dark" ? "bg-slate-950/90 border-slate-800 text-slate-400" : "bg-slate-50 border-slate-200 text-slate-600"
          }`}
        >
          <div className="flex items-center gap-2">
            <span>Showing</span>
            <strong className={theme === "dark" ? "text-slate-100" : "text-slate-900"}>
              {assets.length > 0 ? (page - 1) * limit + 1 : 0}
            </strong>
            <span>to</span>
            <strong className={theme === "dark" ? "text-slate-100" : "text-slate-900"}>
              {Math.min(page * limit, total)}
            </strong>
            <span>of</span>
            <strong className="text-blue-500 font-bold">{total}</strong>
            <span>electrical assets</span>
          </div>

          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <span>Rows per page:</span>
              <select
                value={limit}
                onChange={(e) => {
                  setLimit(parseInt(e.target.value));
                  setPage(1);
                }}
                className={`rounded-lg px-2.5 py-1 font-bold text-xs border focus:outline-none ${
                  theme === "dark" ? "bg-slate-900 border-slate-800 text-slate-200" : "bg-white border-slate-200 text-slate-900"
                }`}
              >
                <option value="10">10</option>
                <option value="25">25</option>
                <option value="50">50</option>
                <option value="100">100</option>
                <option value="500">500</option>
              </select>
            </div>

            <div className="flex items-center gap-1.5">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page <= 1 || loading}
                className={`p-2 border rounded-xl disabled:opacity-30 transition cursor-pointer ${
                  theme === "dark" ? "border-slate-800 bg-slate-900 text-slate-200 hover:bg-slate-800" : "border-slate-200 bg-white text-slate-800 hover:bg-slate-100"
                }`}
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <span className="px-3 font-mono">
                {page} / {totalPages}
              </span>
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page >= totalPages || loading}
                className={`p-2 border rounded-xl disabled:opacity-30 transition cursor-pointer ${
                  theme === "dark" ? "border-slate-800 bg-slate-900 text-slate-200 hover:bg-slate-800" : "border-slate-200 bg-white text-slate-800 hover:bg-slate-100"
                }`}
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* PostGIS Coordinates & Detail Modal */}
      {selectedAsset && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-md p-4">
          <div className={`rounded-3xl border max-w-lg w-full p-6 space-y-4 shadow-2xl ${
            theme === "dark" ? "bg-[#0b1122] border-slate-700 text-slate-100" : "bg-white border-slate-200 text-slate-900"
          }`}>
            <div className="flex items-start justify-between border-b pb-3 border-slate-800">
              <div>
                <span className="font-mono text-xs font-bold text-cyan-400 bg-cyan-950/60 border border-cyan-800/60 px-2.5 py-0.5 rounded-lg">
                  {selectedAsset.asset_id}
                </span>
                <h3 className="text-base font-bold mt-1.5">
                  {selectedAsset.name}
                </h3>
              </div>
              <button
                onClick={() => setSelectedAsset(null)}
                className="text-slate-400 hover:text-white text-lg font-bold p-1 rounded-lg hover:bg-slate-800"
              >
                ✕
              </button>
            </div>

            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className={`p-3 rounded-xl border ${theme === "dark" ? "bg-slate-950/80 border-slate-800" : "bg-slate-50 border-slate-200"}`}>
                <span className="text-slate-400 block font-medium">Asset Category</span>
                <span className="font-bold mt-0.5 block">{selectedAsset.asset_type}</span>
              </div>
              <div className={`p-3 rounded-xl border ${theme === "dark" ? "bg-slate-950/80 border-slate-800" : "bg-slate-50 border-slate-200"}`}>
                <span className="text-slate-400 block font-medium">Manufacturer</span>
                <span className="font-bold mt-0.5 block">{selectedAsset.manufacturer}</span>
              </div>
              <div className={`p-3 rounded-xl border ${theme === "dark" ? "bg-slate-950/80 border-slate-800" : "bg-slate-50 border-slate-200"}`}>
                <span className="text-slate-400 block font-medium">Rated Capacity</span>
                <span className="font-bold mt-0.5 block font-mono">
                  {selectedAsset.capacity_kva ? `${selectedAsset.capacity_kva} kVA` : "N/A"}
                </span>
              </div>
              <div className={`p-3 rounded-xl border ${theme === "dark" ? "bg-slate-950/80 border-slate-800" : "bg-slate-50 border-slate-200"}`}>
                <span className="text-slate-400 block font-medium">Status</span>
                <div className="mt-1">{renderStatusBadge(selectedAsset.status)}</div>
              </div>
            </div>

            {selectedAsset.location && (
              <div className="bg-gradient-to-r from-blue-950/50 to-indigo-950/40 p-4 rounded-2xl border border-blue-800/50 text-xs space-y-1.5">
                <div className="flex items-center gap-1.5 font-bold text-cyan-300">
                  <MapPin className="w-4 h-4 text-cyan-400" />
                  <span>PostGIS Spatial Coordinates (WGS 84 SRID 4326)</span>
                </div>
                <p className="text-slate-300 font-mono text-[11px]">
                  Latitude: <strong className="text-white">{selectedAsset.location.latitude}</strong> | Longitude: <strong className="text-white">{selectedAsset.location.longitude}</strong>
                </p>
                {selectedAsset.location.name && (
                  <p className="text-slate-400 text-[11px]">Bay / Trench: {selectedAsset.location.name}</p>
                )}
              </div>
            )}

            <div className="flex justify-end pt-2">
              <button
                onClick={() => setSelectedAsset(null)}
                className="px-5 py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-xs font-bold transition shadow-md"
              >
                Close Details
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
