"use client";

import React, { useState } from "react";
import {
  ShieldCheck,
  Zap,
  Activity,
  Layers,
  Sparkles,
  BookOpen,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Gauge,
  Thermometer,
  Wrench,
  Download,
  ExternalLink,
  ChevronRight,
  Flame,
  Wind,
  Sun,
  Train,
  Factory,
  Cpu,
  ArrowUpRight,
  FileText,
  SlidersHorizontal,
} from "lucide-react";

type SolutionCategory = "transmission" | "distribution" | "renewable" | "industrial";

interface SolutionItem {
  id: string;
  category: SolutionCategory;
  title: string;
  subtitle: string;
  voltageRating: string;
  oemPartners: string[];
  imagePlaceholder: string;
  coreChallenge: string;
  diagnosticAction: string;
  ragProcedure: {
    oem: string;
    manualName: string;
    page: number;
    citation: string;
    procedureText: string;
    tableSummary: string;
  };
  metrics: {
    healthIndex: number;
    failureProbability: number;
    recommendedMaintenanceDays: number;
  };
  defaultTelemetry: {
    temperature: number; // °C
    pressure: number; // MPa (for SF6) or bar
    bdvVoltage: number; // kV
    loadPercentage: number; // %
  };
}

const SOLUTIONS_DATA: SolutionItem[] = [
  {
    id: "sol-1",
    category: "transmission",
    title: "High-Voltage Power Transformer Diagnostics (110kV – 500kV)",
    subtitle: "Oil-Immersed Step-Down & Generator Step-Up (GSU) Transformers",
    voltageRating: "220 / 33 kV • 40 MVA – 125 MVA",
    oemPartners: ["ABB", "Siemens Energy", "Hitachi Energy"],
    imagePlaceholder: "transformer",
    coreChallenge:
      "Dielectric degradation of mineral oil under high thermal and electrical stress, accompanied by dissolved combustible gases (Hydrogen, Acetylene, Methane) and winding overheating.",
    diagnosticAction:
      "Continuously computes Dielectric Health Index, OTI/WTI thermal stress, and predicts flashover risks using Random Forest baseline regressors.",
    ragProcedure: {
      oem: "ABB",
      manualName: "ABB_DIST_TRAFO_01_distribution-transformer-installation-manual.pdf",
      page: 13,
      citation: "ABB Transformer Manual (Page 13, Commissioning Section)",
      procedureText:
        "Perform oil sampling according to IEC 60422. If Breakdown Voltage (BDV) falls below 50 kV or moisture exceeds 20 ppm, isolate unit and initiate online filtration. Maintain mandatory settling time as per table specifications.",
      tableSummary: "kV Class vs. Required Settling Time (hrs) following oil filtration.",
    },
    metrics: {
      healthIndex: 88,
      failureProbability: 12.4,
      recommendedMaintenanceDays: 45,
    },
    defaultTelemetry: {
      temperature: 68,
      pressure: 1.2,
      bdvVoltage: 58,
      loadPercentage: 74,
    },
  },
  {
    id: "sol-2",
    category: "transmission",
    title: "Gas-Insulated Switchgear (GIS) & Vacuum Circuit Breakers",
    subtitle: "SF6 High-Voltage Enclosed Substation Switchgear",
    voltageRating: "Up to 40.5 kV / 220 kV Single-Pole Enclosed",
    oemPartners: ["Siemens 8DA10", "ABB", "Schneider Electric"],
    imagePlaceholder: "gis",
    coreChallenge:
      "SF6 gas density loss due to micro-leakages around busbar compartment seals and rupture diaphragms, leading to circuit breaker trip lockout.",
    diagnosticAction:
      "Real-time temperature-compensated density tracking and automated stage-1 alarm (0.55 MPa) and stage-2 lockout threshold (0.50 MPa) enforcement.",
    ragProcedure: {
      oem: "Siemens",
      manualName: "861-96019-en-07-11-17.pdf",
      page: 24,
      citation: "Siemens 8DA10 Installation & Operating Instructions (Page 24)",
      procedureText:
        "Inspect gas compartment rupture disks and density monitors immediately. Do not manually trip breaker if pressure drops below 0.50 MPa lockout. Top up SF6 using clean gas handling cart according to Section 11 specifications.",
      tableSummary: "Mounting Locations, Disconnector Types (4MT3 / 4MU4), and Pressure Limits.",
    },
    metrics: {
      healthIndex: 94,
      failureProbability: 6.2,
      recommendedMaintenanceDays: 90,
    },
    defaultTelemetry: {
      temperature: 42,
      pressure: 0.56,
      bdvVoltage: 70,
      loadPercentage: 62,
    },
  },
  {
    id: "sol-3",
    category: "distribution",
    title: "Medium-Voltage Distribution Substations & RMU",
    subtitle: "Cast Resin Dry-Type & Compact Distribution Transformers",
    voltageRating: "11 kV / 22 kV • 500 kVA – 2500 kVA",
    oemPartners: ["Schneider Electric", "Elsewedy Electric", "ABB Resibloc"],
    imagePlaceholder: "distribution",
    coreChallenge:
      "Harmonic distortion from nonlinear urban loads, phase load imbalances, and localized thermal hotspots in compact enclosures.",
    diagnosticAction:
      "Analyzes load ratios, ambient-to-winding temperature gradients, and predicts thermal insulation degradation across distribution clusters.",
    ragProcedure: {
      oem: "Schneider Electric",
      manualName: "Schneider_SM6_Medium_Voltage_Switchboard.pdf",
      page: 18,
      citation: "Schneider Electric SM6 Technical Guidelines (Page 18)",
      procedureText:
        "Verify torque tightening on all cable termination bushings. Ensure forced ventilation louvers are unobstructed. Test PT100 temperature sensors at 90°C alarm and 115°C trip thresholds.",
      tableSummary: "Permissible Overload Curves vs. Ambient Temperature (IEC 60076-7).",
    },
    metrics: {
      healthIndex: 82,
      failureProbability: 18.5,
      recommendedMaintenanceDays: 30,
    },
    defaultTelemetry: {
      temperature: 78,
      pressure: 1.0,
      bdvVoltage: 52,
      loadPercentage: 86,
    },
  },
  {
    id: "sol-4",
    category: "renewable",
    title: "Solar PV & Wind Inverter-Duty Substation Transformers",
    subtitle: "Step-Up Transformers for Clean Energy Farms & BESS",
    voltageRating: "0.69 kV / 33 kV Step-Up • Cyclic Load Resilient",
    oemPartners: ["Hitachi Energy", "Siemens Energy", "GE Vernova"],
    imagePlaceholder: "renewable",
    coreChallenge:
      "Extreme thermal cycling caused by intermittent solar irradiance and wind gusts, inducing rapid cyclic expansion of insulating oil and gaskets.",
    diagnosticAction:
      "Integrates weather forecasting with thermal dynamics to dynamically derate transformers during high-ambient heatwaves.",
    ragProcedure: {
      oem: "Hitachi Energy",
      manualName: "Hitachi_Solar_Inverter_StepUp_Transformer.pdf",
      page: 32,
      citation: "Hitachi Energy Inverter-Duty Technical Manual (Page 32)",
      procedureText:
        "Check de-aeration valves and oil level indicator daily during peak solar hours. Inspect silica gel breather color (blue to pink indicating moisture saturation). Regenerate silica at 150°C if pink exceeds 50%.",
      tableSummary: "Cyclic Loading Derating Coefficients for Solar PV Interconnections.",
    },
    metrics: {
      healthIndex: 91,
      failureProbability: 9.1,
      recommendedMaintenanceDays: 60,
    },
    defaultTelemetry: {
      temperature: 62,
      pressure: 1.1,
      bdvVoltage: 64,
      loadPercentage: 68,
    },
  },
];

export function SolutionsView({
  theme,
  onOpenRag,
}: {
  theme: "dark" | "light";
  onOpenRag: (prefilledQuery: string) => void;
}) {
  const [selectedCategory, setSelectedCategory] = useState<SolutionCategory>("transmission");
  const [activeSolutionId, setActiveSolutionId] = useState<string>("sol-1");

  // Interactive Live Workbench State
  const [simTemp, setSimTemp] = useState<number>(72);
  const [simPressure, setSimPressure] = useState<number>(0.54);
  const [simBdv, setSimBdv] = useState<number>(54);
  const [simLoad, setSimLoad] = useState<number>(82);

  const activeSolution =
    SOLUTIONS_DATA.find((s) => s.id === activeSolutionId) || SOLUTIONS_DATA[0];

  // Calculate live dynamic risk based on simulation
  const calcRiskScore = () => {
    let risk = 10;
    if (simTemp > 75) risk += (simTemp - 75) * 1.8;
    if (simPressure < 0.52) risk += (0.52 - simPressure) * 350;
    if (simBdv < 50) risk += (50 - simBdv) * 2.5;
    if (simLoad > 85) risk += (simLoad - 85) * 1.2;
    return Math.min(Math.round(risk), 98);
  };

  const dynamicRisk = calcRiskScore();
  const dynamicHealth = Math.max(100 - dynamicRisk, 5);

  const filteredSolutions = SOLUTIONS_DATA.filter(
    (s) => s.category === selectedCategory
  );

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* 1. Header Hero Banner - Inspired by ZDBYQ High-Tech Energy Aesthetic */}
      <div
        className={`relative overflow-hidden rounded-3xl p-6 sm:p-10 border transition-all duration-300 shadow-2xl ${
          theme === "dark"
            ? "bg-gradient-to-br from-[#0c1427] via-[#09101f] to-[#060a14] border-slate-800/80"
            : "bg-gradient-to-br from-blue-50/80 via-white to-indigo-50/60 border-blue-100 shadow-blue-500/5"
        }`}
      >
        {/* Glow Accent Circles */}
        <div className="absolute -top-24 -right-24 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -bottom-24 -left-24 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="relative z-10 max-w-4xl space-y-4">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-semibold bg-blue-500/10 text-blue-400 border border-blue-500/20 backdrop-blur-md">
            <ShieldCheck className="w-4 h-4 text-blue-400" />
            <span>Enterprise Substation Asset Solutions & APM Architecture</span>
          </div>

          <h1 className="text-3xl sm:text-5xl font-extrabold tracking-tight">
            Next-Gen Power Grid Diagnostic &{" "}
            <span className="bg-gradient-to-r from-blue-400 via-indigo-400 to-cyan-400 bg-clip-text text-transparent">
              Maintenance Intelligence
            </span>
          </h1>

          <p className="text-sm sm:text-base text-slate-400 leading-relaxed max-w-3xl">
            Bridging heavy electrical substation engineering with AI telemetry analytics.
            GridGuard continuously calculates transformer and switchgear health indices,
            simulates failure probabilities, and delivers instant, multimodal citations from
            official OEM manuals (ABB, Siemens, Schneider Electric).
          </p>

          {/* Quick Metrics KPI Bar */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-4">
            <div
              className={`p-3.5 rounded-2xl border text-center transition ${
                theme === "dark"
                  ? "bg-slate-900/60 border-slate-800"
                  : "bg-white/80 border-slate-200 shadow-sm"
              }`}
            >
              <div className="text-2xl font-black text-blue-400">99.9%</div>
              <div className="text-[11px] text-slate-400 font-medium">Grid Uptime Target</div>
            </div>
            <div
              className={`p-3.5 rounded-2xl border text-center transition ${
                theme === "dark"
                  ? "bg-slate-900/60 border-slate-800"
                  : "bg-white/80 border-slate-200 shadow-sm"
              }`}
            >
              <div className="text-2xl font-black text-emerald-400">-45%</div>
              <div className="text-[11px] text-slate-400 font-medium">MTTR (Repair Time)</div>
            </div>
            <div
              className={`p-3.5 rounded-2xl border text-center transition ${
                theme === "dark"
                  ? "bg-slate-900/60 border-slate-800"
                  : "bg-white/80 border-slate-200 shadow-sm"
              }`}
            >
              <div className="text-2xl font-black text-indigo-400">5 OEMs</div>
              <div className="text-[11px] text-slate-400 font-medium">Curated Technical K-Base</div>
            </div>
            <div
              className={`p-3.5 rounded-2xl border text-center transition ${
                theme === "dark"
                  ? "bg-slate-900/60 border-slate-800"
                  : "bg-white/80 border-slate-200 shadow-sm"
              }`}
            >
              <div className="text-2xl font-black text-cyan-400">IEC / IEEE</div>
              <div className="text-[11px] text-slate-400 font-medium">Standards Compliant</div>
            </div>
          </div>
        </div>
      </div>

      {/* 2. Categorized Solution Selector Tabs (Like ZDBYQ Sector Navigation) */}
      <div className="flex items-center gap-2 overflow-x-auto pb-2 scrollbar-none">
        {[
          { id: "transmission", label: "High-Voltage Transmission (110kV – 500kV)", icon: <Zap className="w-4 h-4" /> },
          { id: "distribution", label: "Medium-Voltage Distribution (11kV – 33kV)", icon: <Layers className="w-4 h-4" /> },
          { id: "renewable", label: "Solar & Wind Substation (Renewables)", icon: <Sun className="w-4 h-4" /> },
          { id: "industrial", label: "Critical Industrial & Rail Power", icon: <Factory className="w-4 h-4" /> },
        ].map((cat) => (
          <button
            key={cat.id}
            onClick={() => {
              setSelectedCategory(cat.id as SolutionCategory);
              const firstInCat = SOLUTIONS_DATA.find((s) => s.category === cat.id);
              if (firstInCat) setActiveSolutionId(firstInCat.id);
            }}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-2xl text-xs font-bold transition whitespace-nowrap border shrink-0 ${
              selectedCategory === cat.id
                ? "bg-blue-600 text-white border-blue-500 shadow-lg shadow-blue-500/25"
                : theme === "dark"
                ? "bg-slate-900/70 border-slate-800 text-slate-400 hover:text-white hover:bg-slate-800"
                : "bg-white border-slate-200 text-slate-700 hover:text-slate-900 hover:bg-slate-50"
            }`}
          >
            {cat.icon}
            <span>{cat.label}</span>
          </button>
        ))}
      </div>

      {/* 3. Main Solution Details Grid & Action Hub */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Solution Cards List (5 Cols) */}
        <div className="lg:col-span-5 space-y-4">
          <h3 className="text-xs font-bold tracking-wider uppercase text-slate-400 px-1">
            Available Equipment Configurations
          </h3>

          <div className="space-y-3">
            {filteredSolutions.map((item) => {
              const isSelected = item.id === activeSolutionId;
              return (
                <div
                  key={item.id}
                  onClick={() => setActiveSolutionId(item.id)}
                  className={`p-5 rounded-2xl border transition-all cursor-pointer relative overflow-hidden ${
                    isSelected
                      ? theme === "dark"
                        ? "bg-[#0d162d] border-blue-500/60 shadow-lg shadow-blue-500/10"
                        : "bg-blue-50/70 border-blue-300 shadow-md shadow-blue-500/5"
                      : theme === "dark"
                      ? "bg-slate-900/40 border-slate-800 hover:border-slate-700 hover:bg-slate-900/80"
                      : "bg-white border-slate-200 hover:border-slate-300 hover:bg-slate-50"
                  }`}
                >
                  {isSelected && (
                    <div className="absolute top-0 left-0 bottom-0 w-1.5 bg-blue-500 rounded-l" />
                  )}

                  <div className="flex items-start justify-between gap-3">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-blue-500/15 text-blue-400 border border-blue-500/20">
                          {item.voltageRating.split("•")[0]}
                        </span>
                        <span className="text-[11px] font-medium text-slate-400">
                          {item.oemPartners.join(" • ")}
                        </span>
                      </div>
                      <h4 className="text-sm font-bold text-slate-100 dark:text-white">
                        {item.title}
                      </h4>
                      <p className="text-xs text-slate-400 line-clamp-2">
                        {item.coreChallenge}
                      </p>
                    </div>

                    <ChevronRight
                      className={`w-4 h-4 shrink-0 mt-1 transition ${
                        isSelected ? "text-blue-400 translate-x-1" : "text-slate-500"
                      }`}
                    />
                  </div>

                  <div className="mt-4 pt-3 border-t border-slate-800/60 flex items-center justify-between text-xs font-mono">
                    <span className="text-emerald-400 font-bold">
                      Health Index: {item.metrics.healthIndex}%
                    </span>
                    <span className="text-amber-400">
                      PoF Risk: {item.metrics.failureProbability}%
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right Column: Deep-Dive Solution Architecture & Live Actions (7 Cols) */}
        <div className="lg:col-span-7 space-y-6">
          <div
            className={`p-6 sm:p-7 rounded-3xl border shadow-xl transition-all ${
              theme === "dark"
                ? "bg-[#0b1120] border-slate-800"
                : "bg-white border-slate-200 shadow-slate-200/50"
            }`}
          >
            {/* Header of Selected Solution */}
            <div className="flex flex-wrap items-center justify-between gap-3 pb-5 border-b border-slate-800">
              <div>
                <span className="text-[11px] font-bold text-blue-400 uppercase tracking-wider">
                  Technical Architecture Specification
                </span>
                <h3 className="text-xl font-black text-white">{activeSolution.title}</h3>
                <p className="text-xs text-slate-400">{activeSolution.subtitle}</p>
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={() =>
                    onOpenRag(
                      `What are the mandatory troubleshooting steps for ${activeSolution.title} from the OEM manual?`
                    )
                  }
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold shadow-md shadow-blue-500/20 transition"
                >
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>Consult RAG Assistant</span>
                </button>
              </div>
            </div>

            {/* Core Sections: Challenge vs. AI Diagnostic Action */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 my-5">
              <div
                className={`p-4 rounded-2xl border ${
                  theme === "dark"
                    ? "bg-rose-500/5 border-rose-500/20 text-rose-200"
                    : "bg-rose-50 border-rose-200 text-rose-900"
                }`}
              >
                <div className="flex items-center gap-2 text-rose-400 font-bold text-xs mb-1.5">
                  <AlertTriangle className="w-4 h-4" />
                  <span>Failure Mode & Engineering Risk</span>
                </div>
                <p className="text-xs leading-relaxed opacity-90">
                  {activeSolution.coreChallenge}
                </p>
              </div>

              <div
                className={`p-4 rounded-2xl border ${
                  theme === "dark"
                    ? "bg-emerald-500/5 border-emerald-500/20 text-emerald-200"
                    : "bg-emerald-50 border-emerald-200 text-emerald-900"
                }`}
              >
                <div className="flex items-center gap-2 text-emerald-400 font-bold text-xs mb-1.5">
                  <Activity className="w-4 h-4" />
                  <span>GridGuard Diagnostic Protocol</span>
                </div>
                <p className="text-xs leading-relaxed opacity-90">
                  {activeSolution.diagnosticAction}
                </p>
              </div>
            </div>

            {/* Prescriptive OEM Manual Card (Direct RAG Citation) */}
            <div
              className={`p-5 rounded-2xl border space-y-3 ${
                theme === "dark"
                  ? "bg-slate-900/80 border-slate-800"
                  : "bg-slate-50 border-slate-200"
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-7 h-7 rounded-lg bg-indigo-500/15 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
                    <BookOpen className="w-4 h-4" />
                  </div>
                  <div>
                    <h5 className="text-xs font-bold text-white">
                      Verified OEM Maintenance Citation
                    </h5>
                    <span className="text-[11px] text-indigo-400 font-mono">
                      {activeSolution.ragProcedure.citation}
                    </span>
                  </div>
                </div>

                <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-300 border border-indigo-500/20">
                  Page {activeSolution.ragProcedure.page}
                </span>
              </div>

              <p className="text-xs text-slate-300 leading-relaxed bg-slate-950/50 p-3 rounded-xl border border-slate-800/80 font-mono">
                {activeSolution.ragProcedure.procedureText}
              </p>

              <div className="flex items-center justify-between text-[11px] text-slate-400">
                <span className="flex items-center gap-1.5">
                  <FileText className="w-3.5 h-3.5 text-blue-400" />
                  <span>Indexed Table: {activeSolution.ragProcedure.tableSummary}</span>
                </span>
                <button
                  onClick={() =>
                    onOpenRag(
                      `Explain table on page ${activeSolution.ragProcedure.page} from ${activeSolution.ragProcedure.manualName}`
                    )
                  }
                  className="text-blue-400 hover:text-blue-300 font-bold inline-flex items-center gap-1"
                >
                  <span>Inspect Table</span>
                  <ArrowUpRight className="w-3 h-3" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 4. Interactive Live Diagnostic Sandbox (ZDBYQ Action Simulation) */}
      <div
        className={`p-6 sm:p-8 rounded-3xl border shadow-2xl transition ${
          theme === "dark"
            ? "bg-[#090f1d] border-slate-800"
            : "bg-white border-slate-200 shadow-slate-200/60"
        }`}
      >
        <div className="flex flex-wrap items-center justify-between gap-4 pb-6 border-b border-slate-800">
          <div>
            <div className="inline-flex items-center gap-2 text-xs font-bold text-cyan-400 uppercase tracking-wider">
              <SlidersHorizontal className="w-4 h-4" />
              <span>Interactive Telemetry Simulation Workbench</span>
            </div>
            <h3 className="text-xl sm:text-2xl font-black text-white mt-1">
              Live Substation Diagnostic & Fault Stress Simulator
            </h3>
            <p className="text-xs text-slate-400">
              Adjust telemetry values to simulate severe high-voltage operational stress and observe
              the live Failure Probability and Health Score reaction.
            </p>
          </div>

          {/* Quick Preset Buttons */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => {
                setSimTemp(88);
                setSimPressure(0.48);
                setSimBdv(42);
                setSimLoad(95);
              }}
              className="px-3 py-1.5 rounded-xl text-xs font-bold bg-rose-500/15 text-rose-300 border border-rose-500/30 hover:bg-rose-500/25 transition"
            >
              Trigger Severe Fault
            </button>
            <button
              onClick={() => {
                setSimTemp(60);
                setSimPressure(0.56);
                setSimBdv(65);
                setSimLoad(70);
              }}
              className="px-3 py-1.5 rounded-xl text-xs font-bold bg-slate-800 text-slate-300 hover:bg-slate-700 transition"
            >
              Reset Normal Baseline
            </button>
          </div>
        </div>

        {/* 4 Telemetry Sliders + Live Diagnostic Indicators */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 pt-6">
          {/* Sliders Area (8 Cols) */}
          <div className="lg:col-span-8 grid grid-cols-1 sm:grid-cols-2 gap-6">
            {/* Slider 1: Temperature */}
            <div className="p-4 rounded-2xl bg-slate-900/50 border border-slate-800 space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="font-bold text-slate-300 flex items-center gap-1.5">
                  <Thermometer className="w-4 h-4 text-rose-400" />
                  Top Oil / Winding Temp
                </span>
                <span
                  className={`font-mono font-bold ${
                    simTemp > 75 ? "text-rose-400" : "text-emerald-400"
                  }`}
                >
                  {simTemp} °C
                </span>
              </div>
              <input
                type="range"
                min="40"
                max="115"
                value={simTemp}
                onChange={(e) => setSimTemp(Number(e.target.value))}
                className="w-full accent-blue-500 cursor-pointer"
              />
              <div className="flex justify-between text-[10px] text-slate-500 font-mono">
                <span>40°C (Normal)</span>
                <span>75°C (Alarm)</span>
                <span>115°C (Trip)</span>
              </div>
            </div>

            {/* Slider 2: SF6 Gas Pressure */}
            <div className="p-4 rounded-2xl bg-slate-900/50 border border-slate-800 space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="font-bold text-slate-300 flex items-center gap-1.5">
                  <Gauge className="w-4 h-4 text-cyan-400" />
                  SF6 Gas Density Pressure
                </span>
                <span
                  className={`font-mono font-bold ${
                    simPressure < 0.52 ? "text-rose-400" : "text-emerald-400"
                  }`}
                >
                  {simPressure.toFixed(2)} MPa
                </span>
              </div>
              <input
                type="range"
                min="0.45"
                max="0.65"
                step="0.01"
                value={simPressure}
                onChange={(e) => setSimPressure(Number(e.target.value))}
                className="w-full accent-cyan-500 cursor-pointer"
              />
              <div className="flex justify-between text-[10px] text-slate-500 font-mono">
                <span>0.48 MPa (Lockout)</span>
                <span>0.55 MPa (Alarm)</span>
                <span>0.60 MPa (Rated)</span>
              </div>
            </div>

            {/* Slider 3: BDV Dielectric */}
            <div className="p-4 rounded-2xl bg-slate-900/50 border border-slate-800 space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="font-bold text-slate-300 flex items-center gap-1.5">
                  <Zap className="w-4 h-4 text-amber-400" />
                  Insulating Oil BDV Test
                </span>
                <span
                  className={`font-mono font-bold ${
                    simBdv < 50 ? "text-rose-400" : "text-emerald-400"
                  }`}
                >
                  {simBdv} kV
                </span>
              </div>
              <input
                type="range"
                min="30"
                max="80"
                value={simBdv}
                onChange={(e) => setSimBdv(Number(e.target.value))}
                className="w-full accent-amber-500 cursor-pointer"
              />
              <div className="flex justify-between text-[10px] text-slate-500 font-mono">
                <span>&lt;40 kV (Critical)</span>
                <span>50 kV (IEC Minimum)</span>
                <span>&gt;70 kV (Fresh Oil)</span>
              </div>
            </div>

            {/* Slider 4: Load Ratio */}
            <div className="p-4 rounded-2xl bg-slate-900/50 border border-slate-800 space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="font-bold text-slate-300 flex items-center gap-1.5">
                  <Activity className="w-4 h-4 text-indigo-400" />
                  Substation Load Ratio
                </span>
                <span
                  className={`font-mono font-bold ${
                    simLoad > 85 ? "text-amber-400" : "text-emerald-400"
                  }`}
                >
                  {simLoad} %
                </span>
              </div>
              <input
                type="range"
                min="30"
                max="125"
                value={simLoad}
                onChange={(e) => setSimLoad(Number(e.target.value))}
                className="w-full accent-indigo-500 cursor-pointer"
              />
              <div className="flex justify-between text-[10px] text-slate-500 font-mono">
                <span>50% (Eco)</span>
                <span>80% (Nominal)</span>
                <span>120% (Overload)</span>
              </div>
            </div>
          </div>

          {/* Real-Time Result Gauge & Predictive Card (4 Cols) */}
          <div className="lg:col-span-4 p-5 rounded-2xl bg-gradient-to-b from-slate-900 to-slate-950 border border-slate-800 flex flex-col justify-between space-y-4">
            <div>
              <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
                <span>Predicted Asset Health Index</span>
                <span
                  className={`font-bold px-2 py-0.5 rounded text-[10px] ${
                    dynamicHealth > 75
                      ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                      : dynamicHealth > 45
                      ? "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                      : "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                  }`}
                >
                  {dynamicHealth > 75 ? "Optimal" : dynamicHealth > 45 ? "Warning" : "Critical"}
                </span>
              </div>

              {/* Huge Health Score Number */}
              <div className="flex items-baseline gap-2">
                <span
                  className={`text-5xl font-black font-mono ${
                    dynamicHealth > 75
                      ? "text-emerald-400"
                      : dynamicHealth > 45
                      ? "text-amber-400"
                      : "text-rose-500"
                  }`}
                >
                  {dynamicHealth}
                </span>
                <span className="text-slate-500 font-mono text-sm">/ 100</span>
              </div>

              {/* Failure Probability Bar */}
              <div className="mt-4 space-y-1.5">
                <div className="flex justify-between text-[11px] text-slate-400 font-mono">
                  <span>Random Forest Failure Risk</span>
                  <span className="font-bold text-rose-400">{dynamicRisk}%</span>
                </div>
                <div className="w-full h-2 rounded-full bg-slate-800 overflow-hidden">
                  <div
                    className={`h-full transition-all duration-300 rounded-full ${
                      dynamicRisk > 60
                        ? "bg-rose-500"
                        : dynamicRisk > 30
                        ? "bg-amber-500"
                        : "bg-emerald-500"
                    }`}
                    style={{ width: `${dynamicRisk}%` }}
                  />
                </div>
              </div>
            </div>

            {/* Prescriptive Trigger CTA */}
            {dynamicRisk > 30 ? (
              <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs space-y-2">
                <div className="flex items-center gap-1.5 font-bold">
                  <Flame className="w-4 h-4 text-rose-400" />
                  <span>Immediate Anomaly Detected</span>
                </div>
                <p className="text-[11px] leading-relaxed text-slate-300">
                  Telemetry parameters exceed IEEE C57 limits. Click below to consult the official
                  OEM repair procedure.
                </p>
                <button
                  onClick={() =>
                    onOpenRag(
                      `High risk alert: Temperature is ${simTemp}°C, SF6 pressure is ${simPressure} MPa, BDV is ${simBdv} kV. What are the emergency actions in ${activeSolution.ragProcedure.manualName}?`
                    )
                  }
                  className="w-full py-2 rounded-lg bg-rose-600 hover:bg-rose-500 text-white font-bold text-xs transition shadow-md shadow-rose-500/20"
                >
                  Open Emergency Manual Protocol
                </button>
              </div>
            ) : (
              <div className="p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                <span>All parameters within safe operating thresholds.</span>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
