"use client";

import React, { useState } from "react";
import {
  ShieldCheck,
  Zap,
  Activity,
  Layers,
  Sparkles,
  BookOpen,
  AlertCircle,
  CheckCircle2,
  Sliders,
  ChevronRight,
  ArrowUpRight,
  FileText,
  RotateCcw,
} from "lucide-react";

type SolutionCategory = "transmission" | "distribution" | "renewable" | "industrial";

interface SolutionItem {
  id: string;
  category: SolutionCategory;
  title: string;
  subtitle: string;
  voltageRating: string;
  oemPartners: string[];
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
    pressure: number; // MPa
    bdvVoltage: number; // kV
    loadPercentage: number; // %
  };
}

const SOLUTIONS_DATA: SolutionItem[] = [
  {
    id: "sol-1",
    category: "transmission",
    title: "High-Voltage Power Transformer Diagnostics",
    subtitle: "Oil-Immersed Step-Down & Generator Step-Up (GSU) Transformers",
    voltageRating: "220 / 33 kV • 40 – 125 MVA",
    oemPartners: ["ABB", "Siemens Energy", "Hitachi Energy"],
    coreChallenge:
      "Dielectric degradation of mineral oil under thermal and electrical stress, accompanied by combustible gas buildup (Hydrogen, Acetylene) and winding overheating.",
    diagnosticAction:
      "Continuously monitors dielectric breakdown voltage (BDV), winding temperature gradient (WTI), and computes failure probability using validated regression models.",
    ragProcedure: {
      oem: "ABB",
      manualName: "ABB_DIST_TRAFO_01_distribution-transformer-installation-manual.pdf",
      page: 13,
      citation: "ABB Transformer Installation & Maintenance Manual (Page 13)",
      procedureText:
        "Perform oil sampling according to IEC 60422. If Breakdown Voltage (BDV) falls below 50 kV or moisture exceeds 20 ppm, isolate unit and initiate oil filtration. Adhere strictly to the settling time matrix.",
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
    subtitle: "Single-Pole Enclosed High-Voltage Gas Compartments",
    voltageRating: "Up to 40.5 kV / 220 kV Enclosed",
    oemPartners: ["Siemens 8DA10", "ABB", "Schneider Electric"],
    coreChallenge:
      "SF6 gas density loss due to seal degradation around busbar compartments and rupture diaphragms, triggering circuit breaker lockout.",
    diagnosticAction:
      "Real-time temperature-compensated density tracking enforcing stage-1 alarm (0.55 MPa) and stage-2 lockout threshold (0.50 MPa).",
    ragProcedure: {
      oem: "Siemens",
      manualName: "861-96019-en-07-11-17.pdf",
      page: 24,
      citation: "Siemens 8DA10 Installation & Operating Instructions (Page 24)",
      procedureText:
        "Inspect rupture disks and density monitors immediately. Do not manually trip breaker if pressure drops below 0.50 MPa lockout. Top up SF6 using clean gas handling cart according to Section 11 specifications.",
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
    voltageRating: "11 kV / 22 kV • 500 – 2500 kVA",
    oemPartners: ["Schneider Electric", "Elsewedy Electric", "ABB Resibloc"],
    coreChallenge:
      "Harmonic distortion from nonlinear urban loads, phase load imbalances, and localized hotspots in compact enclosures.",
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
    title: "Solar PV & Wind Inverter-Duty Transformers",
    subtitle: "Step-Up Transformers for Clean Energy Farms & BESS",
    voltageRating: "0.69 kV / 33 kV Step-Up",
    oemPartners: ["Hitachi Energy", "Siemens Energy", "GE Vernova"],
    coreChallenge:
      "Extreme thermal cycling caused by intermittent solar irradiance and wind gusts, inducing cyclic mechanical strain on insulating oil and gaskets.",
    diagnosticAction:
      "Integrates weather forecasting with thermal dynamics to dynamically calculate thermal stress and prevent insulation aging.",
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
  const [simTemp, setSimTemp] = useState<number>(68);
  const [simPressure, setSimPressure] = useState<number>(0.56);
  const [simBdv, setSimBdv] = useState<number>(58);
  const [simLoad, setSimLoad] = useState<number>(75);

  const activeSolution =
    SOLUTIONS_DATA.find((s) => s.id === activeSolutionId) || SOLUTIONS_DATA[0];

  // Calculate live dynamic risk
  const calcRiskScore = () => {
    let risk = 8;
    if (simTemp > 75) risk += (simTemp - 75) * 1.8;
    if (simPressure < 0.52) risk += (0.52 - simPressure) * 350;
    if (simBdv < 50) risk += (50 - simBdv) * 2.2;
    if (simLoad > 85) risk += (simLoad - 85) * 1.2;
    return Math.min(Math.round(risk), 98);
  };

  const dynamicRisk = calcRiskScore();
  const dynamicHealth = Math.max(100 - dynamicRisk, 5);

  const filteredSolutions = SOLUTIONS_DATA.filter(
    (s) => s.category === selectedCategory
  );

  const isLight = theme === "light";

  return (
    <div className="space-y-10 max-w-7xl mx-auto pb-12">
      {/* 1. Page Header (Quiet, Clean, Architectural) */}
      <div className="space-y-3 pb-6 border-b border-slate-200 dark:border-slate-800">
        <div className="flex items-center gap-2 text-xs font-semibold tracking-wide uppercase text-slate-500 dark:text-slate-400">
          <ShieldCheck className="w-4 h-4 text-blue-600 dark:text-blue-400" />
          <span>Asset Performance Management (APM)</span>
        </div>
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900 dark:text-white">
              Substation Equipment Diagnostic Solutions
            </h1>
            <p className="text-sm text-slate-600 dark:text-slate-400 mt-1 max-w-2xl leading-relaxed">
              Standardized engineering diagnostics mapping real-time electrical telemetry to predictive
              failure models and verified OEM troubleshooting procedures.
            </p>
          </div>

          <div className="flex items-center gap-6 text-xs text-slate-600 dark:text-slate-400 shrink-0 font-medium">
            <div>
              <span className="block text-lg font-bold text-slate-900 dark:text-white">99.9%</span>
              <span className="text-[11px] text-slate-500">Uptime Benchmark</span>
            </div>
            <div className="h-8 w-px bg-slate-200 dark:bg-slate-800" />
            <div>
              <span className="block text-lg font-bold text-slate-900 dark:text-white">-45%</span>
              <span className="text-[11px] text-slate-500">Mean Time to Repair</span>
            </div>
            <div className="h-8 w-px bg-slate-200 dark:bg-slate-800" />
            <div>
              <span className="block text-lg font-bold text-slate-900 dark:text-white">5 OEMs</span>
              <span className="text-[11px] text-slate-500">Manual Libraries</span>
            </div>
          </div>
        </div>
      </div>

      {/* 2. Clean Segmented Category Tabs (No neon rainbow badges) */}
      <div className="flex items-center gap-1.5 p-1 rounded-xl bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 max-w-fit overflow-x-auto">
        {[
          { id: "transmission", label: "High-Voltage Transmission (110kV–500kV)" },
          { id: "distribution", label: "Medium-Voltage Distribution (11kV–33kV)" },
          { id: "renewable", label: "Renewable & BESS Interconnections" },
        ].map((tab) => {
          const isActive = selectedCategory === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => {
                setSelectedCategory(tab.id as SolutionCategory);
                const first = SOLUTIONS_DATA.find((s) => s.category === tab.id);
                if (first) setActiveSolutionId(first.id);
              }}
              className={`px-4 py-2 rounded-lg text-xs font-medium transition whitespace-nowrap ${
                isActive
                  ? "bg-white dark:bg-slate-800 text-slate-900 dark:text-white shadow-sm font-semibold"
                  : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
              }`}
            >
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* 3. Main Solution Details Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Column: Solution Cards (4 Cols) */}
        <div className="lg:col-span-4 space-y-3">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 block px-1">
            Configurations
          </span>

          <div className="space-y-2.5">
            {filteredSolutions.map((item) => {
              const isSelected = item.id === activeSolutionId;
              return (
                <div
                  key={item.id}
                  onClick={() => setActiveSolutionId(item.id)}
                  className={`p-4 rounded-xl border text-left cursor-pointer transition ${
                    isSelected
                      ? "bg-white dark:bg-slate-800/90 border-blue-600 dark:border-blue-500 shadow-sm ring-1 ring-blue-600/20 dark:ring-blue-500/20"
                      : "bg-white dark:bg-slate-900/40 border-slate-200 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700"
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="space-y-1">
                      <span className="text-[11px] font-mono text-slate-500 dark:text-slate-400 block">
                        {item.voltageRating}
                      </span>
                      <h4 className="text-sm font-semibold text-slate-900 dark:text-white">
                        {item.title}
                      </h4>
                      <p className="text-xs text-slate-500 dark:text-slate-400 line-clamp-2 leading-relaxed">
                        {item.coreChallenge}
                      </p>
                    </div>
                    <ChevronRight
                      className={`w-4 h-4 shrink-0 mt-1 transition ${
                        isSelected
                          ? "text-blue-600 dark:text-blue-400 translate-x-0.5"
                          : "text-slate-400"
                      }`}
                    />
                  </div>

                  <div className="mt-3 pt-2.5 border-t border-slate-100 dark:border-slate-800/80 flex items-center justify-between text-[11px] font-mono">
                    <span className="text-slate-600 dark:text-slate-400">
                      Health: <strong className="text-slate-900 dark:text-white">{item.metrics.healthIndex}%</strong>
                    </span>
                    <span className="text-slate-600 dark:text-slate-400">
                      Failure Risk: <strong className="text-slate-900 dark:text-white">{item.metrics.failureProbability}%</strong>
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right Column: Deep-Dive Solution Architecture (8 Cols) */}
        <div className="lg:col-span-8 space-y-6">
          <div className="p-6 sm:p-7 rounded-2xl border bg-white dark:bg-slate-900/60 border-slate-200 dark:border-slate-800 shadow-sm space-y-6">
            {/* Header */}
            <div className="flex flex-wrap items-center justify-between gap-4 pb-5 border-b border-slate-100 dark:border-slate-800">
              <div>
                <span className="text-xs font-mono text-blue-600 dark:text-blue-400 font-semibold block">
                  {activeSolution.voltageRating}
                </span>
                <h3 className="text-lg sm:text-xl font-bold text-slate-900 dark:text-white mt-0.5">
                  {activeSolution.title}
                </h3>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  OEM Partners: {activeSolution.oemPartners.join(" • ")}
                </p>
              </div>

              <button
                onClick={() =>
                  onOpenRag(
                    `What are the mandatory troubleshooting steps for ${activeSolution.title} in the official OEM manual?`
                  )
                }
                className="flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-xs font-medium shadow-sm transition"
              >
                <Sparkles className="w-3.5 h-3.5" />
                <span>Consult RAG Assistant</span>
              </button>
            </div>

            {/* 2 Blocks: Challenge vs Diagnostic Action */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
              <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 space-y-1.5">
                <span className="font-semibold text-slate-900 dark:text-white block">
                  Failure Mode & Operating Risk
                </span>
                <p className="text-slate-600 dark:text-slate-400 leading-relaxed">
                  {activeSolution.coreChallenge}
                </p>
              </div>

              <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 space-y-1.5">
                <span className="font-semibold text-slate-900 dark:text-white block">
                  GridGuard Telemetry Protocol
                </span>
                <p className="text-slate-600 dark:text-slate-400 leading-relaxed">
                  {activeSolution.diagnosticAction}
                </p>
              </div>
            </div>

            {/* Verified OEM Citation (Clean Document Style) */}
            <div className="p-5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/40 space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <BookOpen className="w-4 h-4 text-slate-700 dark:text-slate-300" />
                  <span className="text-xs font-semibold text-slate-900 dark:text-white">
                    {activeSolution.ragProcedure.citation}
                  </span>
                </div>
                <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-200/60 dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-medium">
                  Page {activeSolution.ragProcedure.page}
                </span>
              </div>

              <p className="text-xs text-slate-700 dark:text-slate-300 font-mono leading-relaxed bg-white dark:bg-slate-950 p-3 rounded-lg border border-slate-200 dark:border-slate-800/80">
                {activeSolution.ragProcedure.procedureText}
              </p>

              <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400 pt-1">
                <span className="flex items-center gap-1.5 text-[11px]">
                  <FileText className="w-3.5 h-3.5" />
                  <span>Table: {activeSolution.ragProcedure.tableSummary}</span>
                </span>
                <button
                  onClick={() =>
                    onOpenRag(
                      `Explain table on page ${activeSolution.ragProcedure.page} from ${activeSolution.ragProcedure.manualName}`
                    )
                  }
                  className="text-blue-600 dark:text-blue-400 hover:underline inline-flex items-center gap-1 text-[11px] font-medium"
                >
                  <span>Inspect Table</span>
                  <ArrowUpRight className="w-3 h-3" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 4. Minimalist Telemetry Simulation Workbench */}
      <div className="p-6 sm:p-7 rounded-2xl border bg-white dark:bg-slate-900/60 border-slate-200 dark:border-slate-800 shadow-sm space-y-6">
        <div className="flex flex-wrap items-center justify-between gap-4 pb-5 border-b border-slate-100 dark:border-slate-800">
          <div>
            <div className="flex items-center gap-2 text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide">
              <Sliders className="w-3.5 h-3.5 text-blue-600 dark:text-blue-400" />
              <span>Interactive Telemetry Simulator</span>
            </div>
            <h3 className="text-lg font-bold text-slate-900 dark:text-white mt-0.5">
              Substation Asset Stress Test & Diagnostic Evaluation
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Adjust sensory variables to observe the dynamic reaction of the Health Score and Failure Probability.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => {
                setSimTemp(88);
                setSimPressure(0.48);
                setSimBdv(42);
                setSimLoad(95);
              }}
              className="px-3 py-1.5 rounded-lg text-xs font-medium border border-rose-200 dark:border-rose-900/50 bg-rose-50 dark:bg-rose-950/30 text-rose-700 dark:text-rose-300 hover:bg-rose-100 dark:hover:bg-rose-900/40 transition"
            >
              Simulate Critical Outage
            </button>
            <button
              onClick={() => {
                setSimTemp(68);
                setSimPressure(0.56);
                setSimBdv(58);
                setSimLoad(75);
              }}
              className="px-3 py-1.5 rounded-lg text-xs font-medium border border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition inline-flex items-center gap-1"
            >
              <RotateCcw className="w-3 h-3" />
              <span>Reset Baseline</span>
            </button>
          </div>
        </div>

        {/* 4 Sliders + Health Index Panel */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
          {/* Sliders Grid (8 Cols) */}
          <div className="lg:col-span-8 grid grid-cols-1 sm:grid-cols-2 gap-4">
            {/* Slider 1: Temperature */}
            <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="font-medium text-slate-700 dark:text-slate-300">
                  Top Oil / Winding Temp
                </span>
                <span className="font-mono font-semibold text-slate-900 dark:text-white">
                  {simTemp} °C
                </span>
              </div>
              <input
                type="range"
                min="40"
                max="115"
                value={simTemp}
                onChange={(e) => setSimTemp(Number(e.target.value))}
                className="w-full accent-blue-600 cursor-pointer"
              />
              <div className="flex justify-between text-[10px] text-slate-400 font-mono">
                <span>40°C</span>
                <span>75°C (Alarm)</span>
                <span>115°C</span>
              </div>
            </div>

            {/* Slider 2: SF6 Gas Pressure */}
            <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="font-medium text-slate-700 dark:text-slate-300">
                  SF6 Gas Pressure
                </span>
                <span className="font-mono font-semibold text-slate-900 dark:text-white">
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
                className="w-full accent-blue-600 cursor-pointer"
              />
              <div className="flex justify-between text-[10px] text-slate-400 font-mono">
                <span>0.48 MPa (Lockout)</span>
                <span>0.55 MPa</span>
                <span>0.60 MPa</span>
              </div>
            </div>

            {/* Slider 3: BDV Dielectric */}
            <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="font-medium text-slate-700 dark:text-slate-300">
                  Dielectric BDV Breakdown
                </span>
                <span className="font-mono font-semibold text-slate-900 dark:text-white">
                  {simBdv} kV
                </span>
              </div>
              <input
                type="range"
                min="30"
                max="80"
                value={simBdv}
                onChange={(e) => setSimBdv(Number(e.target.value))}
                className="w-full accent-blue-600 cursor-pointer"
              />
              <div className="flex justify-between text-[10px] text-slate-400 font-mono">
                <span>30 kV</span>
                <span>50 kV (IEC Minimum)</span>
                <span>80 kV</span>
              </div>
            </div>

            {/* Slider 4: Load Ratio */}
            <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="font-medium text-slate-700 dark:text-slate-300">
                  Substation Load Ratio
                </span>
                <span className="font-mono font-semibold text-slate-900 dark:text-white">
                  {simLoad} %
                </span>
              </div>
              <input
                type="range"
                min="30"
                max="125"
                value={simLoad}
                onChange={(e) => setSimLoad(Number(e.target.value))}
                className="w-full accent-blue-600 cursor-pointer"
              />
              <div className="flex justify-between text-[10px] text-slate-400 font-mono">
                <span>50%</span>
                <span>85% (Nominal)</span>
                <span>120%</span>
              </div>
            </div>
          </div>

          {/* Result Panel (4 Cols) */}
          <div className="lg:col-span-4 p-5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950/60 space-y-4">
            <div>
              <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block">
                Calculated Health Index
              </span>
              <div className="flex items-baseline gap-2 mt-1">
                <span className="text-4xl font-bold font-mono text-slate-900 dark:text-white">
                  {dynamicHealth}
                </span>
                <span className="text-xs text-slate-400 font-mono">/ 100</span>
              </div>

              {/* Minimal Progress Bar */}
              <div className="mt-3 space-y-1">
                <div className="flex justify-between text-[11px] text-slate-500 font-mono">
                  <span>Failure Probability</span>
                  <span className="font-semibold text-slate-900 dark:text-white">{dynamicRisk}%</span>
                </div>
                <div className="w-full h-1.5 rounded-full bg-slate-200 dark:bg-slate-800 overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all duration-200 ${
                      dynamicRisk > 60
                        ? "bg-rose-500"
                        : dynamicRisk > 30
                        ? "bg-amber-500"
                        : "bg-blue-600"
                    }`}
                    style={{ width: `${dynamicRisk}%` }}
                  />
                </div>
              </div>
            </div>

            {dynamicRisk > 30 ? (
              <div className="pt-2">
                <button
                  onClick={() =>
                    onOpenRag(
                      `High risk alert: Temperature is ${simTemp}°C, SF6 pressure is ${simPressure} MPa, BDV is ${simBdv} kV. What are the emergency actions in ${activeSolution.ragProcedure.manualName}?`
                    )
                  }
                  className="w-full py-2 px-3 rounded-lg bg-slate-900 dark:bg-white text-white dark:text-slate-900 font-medium text-xs hover:bg-slate-800 dark:hover:bg-slate-100 transition shadow-sm"
                >
                  Consult Emergency Protocol
                </button>
              </div>
            ) : (
              <div className="text-[11px] text-slate-500 flex items-center gap-1.5 pt-1">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400 shrink-0" />
                <span>Operating within nominal parameters.</span>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
