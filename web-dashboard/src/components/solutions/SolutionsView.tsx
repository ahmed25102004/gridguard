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
  Sun,
  Flame,
  Factory,
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

  return (
    <div className="space-y-8 max-w-7xl mx-auto pb-12 font-sans">
      {/* 1. Header Hero - ZDBYQ Style Clean Warm Engineering Header */}
      <div className="p-6 sm:p-8 rounded-2xl border transition-all duration-200 bg-white dark:bg-slate-900 border-[#EAEAEA] dark:border-slate-800 shadow-sm">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div className="space-y-2 max-w-3xl">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-md text-xs font-bold uppercase tracking-wider bg-[#FFF1E9] dark:bg-[#FF6E00]/15 text-[#FF6E00] border border-[#FFD8C2] dark:border-[#FF6E00]/30">
              <ShieldCheck className="w-4 h-4 text-[#FF6E00]" />
              <span>Tailored Substation & Grid Solutions</span>
            </div>

            <h1 className="text-2xl sm:text-4xl font-extrabold tracking-tight text-[#212121] dark:text-white">
              Power Grid Diagnostic & Asset Performance Solutions
            </h1>

            <p className="text-sm text-[#767676] dark:text-slate-400 leading-relaxed max-w-2xl">
              High-reliability predictive maintenance, real-time sensory health index calculations,
              and multimodal RAG assistance grounded in verified OEM technical manuals.
            </p>
          </div>

          {/* Quick Metrics (ZDBYQ Style clean numbers with orange accent) */}
          <div className="grid grid-cols-3 gap-4 border-t lg:border-t-0 lg:border-l border-[#EAEAEA] dark:border-slate-800 pt-4 lg:pt-0 lg:pl-6 shrink-0">
            <div>
              <span className="text-2xl font-black text-[#FF6E00] block">99.9%</span>
              <span className="text-xs text-[#767676] dark:text-slate-400 font-medium">Grid Uptime</span>
            </div>
            <div>
              <span className="text-2xl font-black text-[#212121] dark:text-white block">-45%</span>
              <span className="text-xs text-[#767676] dark:text-slate-400 font-medium">Repair Time</span>
            </div>
            <div>
              <span className="text-2xl font-black text-[#212121] dark:text-white block">5 OEMs</span>
              <span className="text-xs text-[#767676] dark:text-slate-400 font-medium">K-Base Manuals</span>
            </div>
          </div>
        </div>
      </div>

      {/* 2. ZDBYQ Tab Navigation Bar (#FF6E00 Brand Accent) */}
      <div className="flex items-center gap-2 border-b border-[#EAEAEA] dark:border-slate-800 pb-3 overflow-x-auto scrollbar-none">
        {[
          { id: "transmission", label: "Power Transmission (110kV – 500kV)" },
          { id: "distribution", label: "Distribution & RMU (11kV – 33kV)" },
          { id: "renewable", label: "Solar & Wind Substation (BESS)" },
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
              className={`px-4 py-2.5 rounded-lg text-xs font-bold transition whitespace-nowrap border ${
                isActive
                  ? "bg-[#FF6E00] text-white border-[#FF6E00] shadow-sm"
                  : "bg-white dark:bg-slate-900 text-[#767676] dark:text-slate-400 border-[#EAEAEA] dark:border-slate-800 hover:text-[#212121] dark:hover:text-white hover:border-[#d9d9d9]"
              }`}
            >
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* 3. Main Solution Details Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: Solution Selector Cards (4 Cols) */}
        <div className="lg:col-span-4 space-y-3">
          <span className="text-xs font-bold uppercase tracking-wider text-[#767676] dark:text-slate-400 block px-1">
            Equipment Configurations
          </span>

          <div className="space-y-2.5">
            {filteredSolutions.map((item) => {
              const isSelected = item.id === activeSolutionId;
              return (
                <div
                  key={item.id}
                  onClick={() => setActiveSolutionId(item.id)}
                  className={`p-4 rounded-xl border text-left cursor-pointer transition relative ${
                    isSelected
                      ? "bg-white dark:bg-slate-800/90 border-[#FF6E00] shadow-sm ring-1 ring-[#FF6E00]/30"
                      : "bg-white dark:bg-slate-900 border-[#EAEAEA] dark:border-slate-800 hover:border-[#d9d9d9] dark:hover:border-slate-700"
                  }`}
                >
                  {isSelected && (
                    <div className="absolute top-0 left-0 bottom-0 w-1 bg-[#FF6E00] rounded-l" />
                  )}

                  <div className="flex items-start justify-between gap-2">
                    <div className="space-y-1">
                      <span className="text-[11px] font-mono text-[#767676] dark:text-slate-400 block">
                        {item.voltageRating}
                      </span>
                      <h4 className="text-sm font-bold text-[#212121] dark:text-white">
                        {item.title}
                      </h4>
                      <p className="text-xs text-[#767676] dark:text-slate-400 line-clamp-2 leading-relaxed">
                        {item.coreChallenge}
                      </p>
                    </div>
                    <ChevronRight
                      className={`w-4 h-4 shrink-0 mt-1 transition ${
                        isSelected ? "text-[#FF6E00] translate-x-0.5" : "text-[#767676]"
                      }`}
                    />
                  </div>

                  <div className="mt-3 pt-2.5 border-t border-[#EAEAEA] dark:border-slate-800 flex items-center justify-between text-[11px] font-mono">
                    <span className="text-[#767676] dark:text-slate-400">
                      Health Index: <strong className="text-[#212121] dark:text-white">{item.metrics.healthIndex}%</strong>
                    </span>
                    <span className="text-[#767676] dark:text-slate-400">
                      Risk: <strong className="text-[#FF6E00]">{item.metrics.failureProbability}%</strong>
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right Column: Deep-Dive Solution Architecture (8 Cols) */}
        <div className="lg:col-span-8 space-y-6">
          <div className="p-6 sm:p-7 rounded-2xl border bg-white dark:bg-slate-900 border-[#EAEAEA] dark:border-slate-800 shadow-sm space-y-6">
            {/* Header */}
            <div className="flex flex-wrap items-center justify-between gap-4 pb-5 border-b border-[#EAEAEA] dark:border-slate-800">
              <div>
                <span className="text-xs font-mono text-[#FF6E00] font-bold block">
                  {activeSolution.voltageRating}
                </span>
                <h3 className="text-lg sm:text-xl font-bold text-[#212121] dark:text-white mt-0.5">
                  {activeSolution.title}
                </h3>
                <p className="text-xs text-[#767676] dark:text-slate-400">
                  OEM Equipment Partners: {activeSolution.oemPartners.join(" • ")}
                </p>
              </div>

              <button
                onClick={() =>
                  onOpenRag(
                    `What are the mandatory troubleshooting steps for ${activeSolution.title} in the official OEM manual?`
                  )
                }
                className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-[#FF6E00] hover:bg-[#ef5816] text-white text-xs font-bold shadow-sm transition"
              >
                <Sparkles className="w-3.5 h-3.5" />
                <span>Consult RAG Assistant</span>
              </button>
            </div>

            {/* 2 Blocks: Challenge vs Diagnostic Action */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
              <div className="p-4 rounded-xl bg-[#F9F9F9] dark:bg-slate-800/40 border border-[#EAEAEA] dark:border-slate-800 space-y-1.5">
                <span className="font-bold text-[#212121] dark:text-white block">
                  Failure Mode & Operating Risk
                </span>
                <p className="text-[#767676] dark:text-slate-400 leading-relaxed">
                  {activeSolution.coreChallenge}
                </p>
              </div>

              <div className="p-4 rounded-xl bg-[#F9F9F9] dark:bg-slate-800/40 border border-[#EAEAEA] dark:border-slate-800 space-y-1.5">
                <span className="font-bold text-[#212121] dark:text-white block">
                  GridGuard Telemetry Protocol
                </span>
                <p className="text-[#767676] dark:text-slate-400 leading-relaxed">
                  {activeSolution.diagnosticAction}
                </p>
              </div>
            </div>

            {/* Verified OEM Citation (Clean Document Style) */}
            <div className="p-5 rounded-xl border border-[#EAEAEA] dark:border-slate-800 bg-[#F9F9F9] dark:bg-slate-800/30 space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <BookOpen className="w-4 h-4 text-[#FF6E00]" />
                  <span className="text-xs font-bold text-[#212121] dark:text-white">
                    {activeSolution.ragProcedure.citation}
                  </span>
                </div>
                <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-white dark:bg-slate-800 text-[#FF6E00] border border-[#FFD8C2] dark:border-slate-700 font-bold">
                  Page {activeSolution.ragProcedure.page}
                </span>
              </div>

              <p className="text-xs text-[#212121] dark:text-slate-300 font-mono leading-relaxed bg-white dark:bg-slate-950 p-3 rounded-lg border border-[#EAEAEA] dark:border-slate-800">
                {activeSolution.ragProcedure.procedureText}
              </p>

              <div className="flex items-center justify-between text-xs text-[#767676] dark:text-slate-400 pt-1">
                <span className="flex items-center gap-1.5 text-[11px]">
                  <FileText className="w-3.5 h-3.5 text-[#FF6E00]" />
                  <span>Table: {activeSolution.ragProcedure.tableSummary}</span>
                </span>
                <button
                  onClick={() =>
                    onOpenRag(
                      `Explain table on page ${activeSolution.ragProcedure.page} from ${activeSolution.ragProcedure.manualName}`
                    )
                  }
                  className="text-[#FF6E00] hover:underline inline-flex items-center gap-1 text-[11px] font-bold"
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
      <div className="p-6 sm:p-7 rounded-2xl border bg-white dark:bg-slate-900 border-[#EAEAEA] dark:border-slate-800 shadow-sm space-y-6">
        <div className="flex flex-wrap items-center justify-between gap-4 pb-5 border-b border-[#EAEAEA] dark:border-slate-800">
          <div>
            <div className="flex items-center gap-2 text-xs font-bold text-[#FF6E00] uppercase tracking-wider">
              <Sliders className="w-3.5 h-3.5" />
              <span>Interactive Telemetry Simulator</span>
            </div>
            <h3 className="text-lg font-bold text-[#212121] dark:text-white mt-0.5">
              Substation Asset Stress Test & Diagnostic Evaluation
            </h3>
            <p className="text-xs text-[#767676] dark:text-slate-400">
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
              className="px-3 py-1.5 rounded-lg text-xs font-bold border border-rose-200 dark:border-rose-900/50 bg-rose-50 dark:bg-rose-950/30 text-rose-700 dark:text-rose-300 hover:bg-rose-100 dark:hover:bg-rose-900/40 transition"
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
              className="px-3 py-1.5 rounded-lg text-xs font-bold border border-[#EAEAEA] dark:border-slate-800 text-[#767676] dark:text-slate-300 hover:bg-[#F9F9F9] dark:hover:bg-slate-800 transition inline-flex items-center gap-1"
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
            <div className="p-4 rounded-xl bg-[#F9F9F9] dark:bg-slate-800/40 border border-[#EAEAEA] dark:border-slate-800 space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="font-bold text-[#212121] dark:text-slate-300">
                  Top Oil / Winding Temp
                </span>
                <span className="font-mono font-bold text-[#212121] dark:text-white">
                  {simTemp} °C
                </span>
              </div>
              <input
                type="range"
                min="40"
                max="115"
                value={simTemp}
                onChange={(e) => setSimTemp(Number(e.target.value))}
                className="w-full accent-[#FF6E00] cursor-pointer"
              />
              <div className="flex justify-between text-[10px] text-[#767676] font-mono">
                <span>40°C</span>
                <span>75°C (Alarm)</span>
                <span>115°C</span>
              </div>
            </div>

            {/* Slider 2: SF6 Gas Pressure */}
            <div className="p-4 rounded-xl bg-[#F9F9F9] dark:bg-slate-800/40 border border-[#EAEAEA] dark:border-slate-800 space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="font-bold text-[#212121] dark:text-slate-300">
                  SF6 Gas Pressure
                </span>
                <span className="font-mono font-bold text-[#212121] dark:text-white">
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
                className="w-full accent-[#FF6E00] cursor-pointer"
              />
              <div className="flex justify-between text-[10px] text-[#767676] font-mono">
                <span>0.48 MPa (Lockout)</span>
                <span>0.55 MPa</span>
                <span>0.60 MPa</span>
              </div>
            </div>

            {/* Slider 3: BDV Dielectric */}
            <div className="p-4 rounded-xl bg-[#F9F9F9] dark:bg-slate-800/40 border border-[#EAEAEA] dark:border-slate-800 space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="font-bold text-[#212121] dark:text-slate-300">
                  Dielectric BDV Breakdown
                </span>
                <span className="font-mono font-bold text-[#212121] dark:text-white">
                  {simBdv} kV
                </span>
              </div>
              <input
                type="range"
                min="30"
                max="80"
                value={simBdv}
                onChange={(e) => setSimBdv(Number(e.target.value))}
                className="w-full accent-[#FF6E00] cursor-pointer"
              />
              <div className="flex justify-between text-[10px] text-[#767676] font-mono">
                <span>30 kV</span>
                <span>50 kV (IEC Minimum)</span>
                <span>80 kV</span>
              </div>
            </div>

            {/* Slider 4: Load Ratio */}
            <div className="p-4 rounded-xl bg-[#F9F9F9] dark:bg-slate-800/40 border border-[#EAEAEA] dark:border-slate-800 space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="font-bold text-[#212121] dark:text-slate-300">
                  Substation Load Ratio
                </span>
                <span className="font-mono font-bold text-[#212121] dark:text-white">
                  {simLoad} %
                </span>
              </div>
              <input
                type="range"
                min="30"
                max="125"
                value={simLoad}
                onChange={(e) => setSimLoad(Number(e.target.value))}
                className="w-full accent-[#FF6E00] cursor-pointer"
              />
              <div className="flex justify-between text-[10px] text-[#767676] font-mono">
                <span>50%</span>
                <span>85% (Nominal)</span>
                <span>120%</span>
              </div>
            </div>
          </div>

          {/* Result Panel (4 Cols) */}
          <div className="lg:col-span-4 p-5 rounded-xl border border-[#EAEAEA] dark:border-slate-800 bg-[#F9F9F9] dark:bg-slate-950/60 space-y-4">
            <div>
              <span className="text-[11px] font-bold text-[#767676] uppercase tracking-wider block">
                Calculated Health Index
              </span>
              <div className="flex items-baseline gap-2 mt-1">
                <span className="text-4xl font-black font-mono text-[#212121] dark:text-white">
                  {dynamicHealth}
                </span>
                <span className="text-xs text-[#767676] font-mono">/ 100</span>
              </div>

              {/* Minimal Progress Bar */}
              <div className="mt-3 space-y-1">
                <div className="flex justify-between text-[11px] text-[#767676] font-mono">
                  <span>Failure Probability</span>
                  <span className="font-bold text-[#FF6E00]">{dynamicRisk}%</span>
                </div>
                <div className="w-full h-1.5 rounded-full bg-[#EAEAEA] dark:bg-slate-800 overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all duration-200 ${
                      dynamicRisk > 60
                        ? "bg-rose-500"
                        : dynamicRisk > 30
                        ? "bg-[#FF6E00]"
                        : "bg-emerald-500"
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
                  className="w-full py-2.5 px-3 rounded-lg bg-[#FF6E00] hover:bg-[#ef5816] text-white font-bold text-xs transition shadow-sm"
                >
                  Consult Emergency Protocol
                </button>
              </div>
            ) : (
              <div className="text-[11px] text-[#767676] flex items-center gap-1.5 pt-1 font-medium">
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
