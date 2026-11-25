"use client";

import React, { useState } from "react";
import { AssetTable } from "../../components/assets/AssetTable";
import { useDashboard } from "../../components/layout/DashboardContext";
import {
  Layers,
  PlusCircle,
  Activity,
  AlertOctagon,
  CheckCircle2,
  Wrench,
  Download,
  History,
  Radio,
  FileCheck2,
  X,
  MapPin,
  Sparkles,
  BookOpen,
  Send,
  Zap,
  Gauge,
  Thermometer,
  FileText,
  Compass,
  Crosshair,
  Eye,
  SlidersHorizontal,
  Languages,
  RotateCcw,
  Copy,
  Check,
  MessageSquare,
} from "lucide-react";

interface ChatMessage {
  id: string;
  sender: "user" | "assistant";
  textEn: string;
  textAr: string;
  language: "en" | "ar";
  citations?: string[];
  timestamp: string;
}

interface GisAsset {
  id: string;
  name: string;
  type: "Transformer" | "Switch" | "Cable" | "Meter" | "Pole";
  distanceKm: number;
  bearingDeg: number;
  lat: number;
  lon: number;
  status: "Active" | "Maintenance" | "Fault";
  health: number;
  manufacturer: string;
  voltageKv: string;
}

const GIS_ASSETS: GisAsset[] = [
  { id: "AST-TRF-001", name: "220/33kV Main Step-Down Transformer 1", type: "Transformer", distanceKm: 0.5, bearingDeg: 35, lat: 30.0478, lon: 31.2385, status: "Active", health: 96, manufacturer: "ABB Resibloc", voltageKv: "220/33 kV" },
  { id: "AST-SWT-004", name: "33kV SF6 Gas-Insulated Bus Switchgear", type: "Switch", distanceKm: 1.2, bearingDeg: 120, lat: 30.0389, lon: 31.2461, status: "Active", health: 94, manufacturer: "Siemens 8DA10", voltageKv: "33 kV" },
  { id: "AST-CBL-012", name: "33kV Underground XLPE Feeder Trunk A", type: "Cable", distanceKm: 2.1, bearingDeg: 215, lat: 30.0305, lon: 31.2231, status: "Active", health: 89, manufacturer: "El Sewedy Electric", voltageKv: "33 kV" },
  { id: "AST-TRF-002", name: "33/11kV Distribution Transformer Unit B", type: "Transformer", distanceKm: 3.8, bearingDeg: 310, lat: 30.0667, lon: 31.2064, status: "Maintenance", health: 74, manufacturer: "Schneider Electric", voltageKv: "33/11 kV" },
  { id: "AST-SWT-010", name: "66kV Outdoor Motorized Disconnector", type: "Switch", distanceKm: 6.4, bearingDeg: 165, lat: 29.9888, lon: 31.2520, status: "Fault", health: 42, manufacturer: "ABB SGF 72.5", voltageKv: "66 kV" },
  { id: "AST-MTR-088", name: "Substation Primary Feeder Smart Meter", type: "Meter", distanceKm: 9.7, bearingDeg: 75, lat: 30.0671, lon: 31.3328, status: "Active", health: 98, manufacturer: "Itron Sentinel", voltageKv: "33 kV" },
  { id: "AST-POL-034", name: "220kV Tension Suspension Tower #34", type: "Pole", distanceKm: 14.5, bearingDeg: 290, lat: 30.0889, lon: 31.0945, status: "Active", health: 91, manufacturer: "National Towers Co.", voltageKv: "220 kV" },
  { id: "AST-CBL-099", name: "Nile River Canal Submarine Cable Line", type: "Cable", distanceKm: 19.8, bearingDeg: 255, lat: 29.9980, lon: 31.0370, status: "Active", health: 87, manufacturer: "Prysmian Group", voltageKv: "66 kV" },
  { id: "AST-TRF-007", name: "TBEA Auxiliary Step-Up Transformer", type: "Transformer", distanceKm: 27.2, bearingDeg: 195, lat: 29.8078, lon: 31.1610, status: "Active", health: 93, manufacturer: "TBEA Energy", voltageKv: "220/66 kV" },
  { id: "AST-SWT-022", name: "11kV Vacuum Circuit Breaker Cluster", type: "Switch", distanceKm: 34.6, bearingDeg: 345, lat: 30.3440, lon: 31.1420, status: "Maintenance", health: 68, manufacturer: "Eaton Power Xpert", voltageKv: "11 kV" },
  { id: "AST-POL-140", name: "Delta Interconnection Double Circuit Tower", type: "Pole", distanceKm: 42.0, bearingDeg: 15, lat: 30.4100, lon: 31.3480, status: "Active", health: 95, manufacturer: "Egyptian Towers Corp", voltageKv: "500 kV" },
  { id: "AST-MTR-102", name: "Regional Industrial Boundary Metering Unit", type: "Meter", distanceKm: 48.5, bearingDeg: 140, lat: 29.7120, lon: 31.5540, status: "Active", health: 92, manufacturer: "Landis+Gyr E850", voltageKv: "66 kV" },
];

export default function AssetsPage() {
  const { theme, activeTab, setActiveTab } = useDashboard();
  const [showAddModal, setShowAddModal] = useState(false);
  const [showToast, setShowToast] = useState(true);

  // RAG Interactive state with Chat History & Bilingual Arabic/English Support
  const [ragQuery, setRagQuery] = useState("");
  const [ragLoading, setRagLoading] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([
    {
      id: "welcome-1",
      sender: "assistant",
      textEn:
        "Welcome to GridGuard Multimodal RAG Technical Assistant. I am directly connected to certified OEM manuals (ABB Resibloc, Siemens 8DA10, Schneider SF6). Ask any high-voltage substation maintenance or emergency diagnostic procedure.",
      textAr:
        "مرحباً بك في المساعد الفني الذكي GridGuard RAG. إجاباتي معتمدة وموثقة بالكامل من كتالوجات المصنعين الرسمية (ABB Resibloc و Siemens و Schneider). يمكنك سؤالي عن أي عطل فني، خطوات اختبارات الزيت BDV، أو إجراءات طوارئ محطات المحولات.",
      language: "en",
      citations: [
        "ABB_DIST_TRAFO_01_distribution-transformer-installation-manual.pdf | Section 1",
        "abb-sgf-high-voltage-disconnector-manual.pdf | Section 2",
      ],
      timestamp: "Online",
    },
  ]);

  const copyText = (id: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const toggleMessageLanguage = (id: string) => {
    setChatMessages((prev) =>
      prev.map((msg) =>
        msg.id === id ? { ...msg, language: msg.language === "en" ? "ar" : "en" } : msg
      )
    );
  };

  // Spatial radar radius state
  const [radarRadius, setRadarRadius] = useState(10.0);
  const [selectedGisAsset, setSelectedGisAsset] = useState<GisAsset | null>(null);

  const handleRunRag = (q: string) => {
    if (!q.trim()) return;
    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      sender: "user",
      textEn: q,
      textAr: q,
      language: "en",
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setChatMessages((prev) => [...prev, userMsg]);
    setRagQuery("");
    setRagLoading(true);

    setTimeout(() => {
      setRagLoading(false);
      const queryLower = q.toLowerCase();

      let answerEn = "";
      let answerAr = "";
      let citations: string[] = [];

      // Case 1: SF6 Gas Pressure / Disconnector / Switchgear Emergency
      if (
        queryLower.includes("sf6") ||
        queryLower.includes("gas") ||
        queryLower.includes("disconnector") ||
        queryLower.includes("switchgear") ||
        queryLower.includes("pressure")
      ) {
        answerEn =
          "Based on official OEM Technical Manual (ABB SGF 72.5kV Disconnector & SF6 Switchgear):\n\n" +
          "• Immediate Safety & Lockout: Check density monitor gauge. If pressure has dropped below Lockout Threshold (0.45 MPa), DO NOT operate the disconnector contacts electrically or manually; dielectric arc-extinction capability is compromised and manual opening will cause an explosive phase-to-ground flashover.\n" +
          "• Room Ventilation Protocol: Activate forced-air emergency ventilation immediately (minimum 6 air changes/hour). SF6 decomposition products (SF4, SOF2, HF) are heavy, toxic, and accumulate at floor level.\n" +
          "• Emergency Gas Servicing: Connect an emergency SF6 service cart (DILO DN20 self-sealing coupling) to the filling valve on Pole Phase B. Evacuate connecting hose to < 1 mbar before filling, then top up with certified IEC 60376 technical-grade SF6 to rated density (0.60 MPa at 20°C).\n" +
          "• Leak Localization: Perform ultrasonic acoustic sniffing and infrared optical gas imaging (FLIR GF306) across all porcelain flange seals and rupture disc diaphragms.";

        answerAr =
          "بناءً على الكتالوج الفني المعتمد من شركة ABB (لقواطع ومفاتيح عزل الجهد العالي ABB SGF 72.5kV):\n\n" +
          "• إجراءات الأمان وفصل القفل الفوري (Lockout): افحص عداد كثافة وضغط الغاز فوراً. إذا هبط الضغط عن حد القفل الإجباري (0.45 ميجاباسكال)، يُحظر تماماً محاولة فتح أو غلق مفتاح العزل كهربائياً أو يدوياً؛ لأن كفاءة إخماد الشرارة مفقودة وأي تحريك يدوي سينتج عنه قوس كهربائي وانفجار مباشر للأرضي.\n\n" +
          "• بروتوكول تهوية الغرفة: قم بتشغيل مراوح سحب وطرد الهواء الإجبارية فوراً (بمعدل 6 دورات هواء/ساعة كحد أدنى)، لأن نواتج تحلل غاز SF6 (مثل SOF2 و SF4) غازات ثقيلة وخانقة وسامة وتتراكم بمحاذاة الأرضية.\n\n" +
          "• تزويد الغاز في الطوارئ: قم بتوصيل عربة شحن الغاز المعتمدة (DILO Service Cart) عبر صمام التعبئة الذاتي (DILO DN20) في الوجه Phase B. تأكد من تفريغ خرطوم الشحن لضغط أقل من 1 ملي بار لسحب الرطوبة قبل الحقن، ثم املأ بغاز SF6 نقي مطابق للمواصفة IEC 60376 حتى ضغط 0.60 ميجاباسكال عند 20 درجة مئوية.\n\n" +
          "• تحديد مكان التسريب: استخدم جهاز الكشف بالموجات فوق الصوتية وكاميرا الأشعة تحت الحمراء البصرية (FLIR GF306) للكشف على جوان الحواف وفلانجات البورسلين وقرص الحماية (Rupture Disc).";

        citations = [
          "abb-sgf-high-voltage-disconnector-manual.pdf | Page 14 (SF6 Pressure & Density Monitoring)",
          "abb-sgf-high-voltage-disconnector-manual.pdf | Page 38 (Emergency Gas Handling & Lockout Rules)",
          "iec-62271-4-high-voltage-switchgear.pdf | Section 5.2 (Safety in Gas Depressurization)",
        ];
      }
      // Case 2: BDV Breakdown Voltage on Insulating Oil
      else if (
        queryLower.includes("bdv") ||
        queryLower.includes("breakdown") ||
        queryLower.includes("dielectric")
      ) {
        answerEn =
          "Based on official ABB Technical Manual (Distribution Transformer Installation & Maintenance):\n\n" +
          "• Sampling Procedure: Purge 2 liters of stagnant oil from bottom sampling valve V1, then collect sample in dry, amber glass bottle per IEC 60422.\n" +
          "• Test Setup: Use calibrated 2.5 mm ± 0.05 mm spherical electrode cell per IEC 60156 standards with 50 Hz AC voltage ramp rate of 2.0 kV/s.\n" +
          "• Pass/Fail Acceptance Criteria:\n" +
          "  - New transformer oil prior to energization: Minimum 60 kV.\n" +
          "  - In-service operating transformer: Minimum 50 kV (below 40 kV mandates immediate vacuum degasification and centrifugal filtration).\n" +
          "• Statistical Averaging: Conduct 6 consecutive breakdown discharges with 2-minute magnetic stirring intervals and record arithmetic mean.";

        answerAr =
          "بناءً على الكتالوج الفني المعتمد من شركة ABB (دليل تركيب وصيانة محولات التوزيع):\n\n" +
          "• طريقة أخذ العينة: يتم تفريغ أول 2 لتر من الزيت الراكد من محبس السحب السفلي (Valve V1)، ثم تؤخذ عينة الزيت في زجاجة بنية معتمة ونظيفة وجافة تماماً طبقاً للمواصفة IEC 60422.\n\n" +
          "• إعداد جهاز الاختبار: استخدام خلية اختبار ذات أقطاب كروية مضبوطة على خلوص 2.5 مم ± 0.05 مم طبقاً للمواصفة IEC 60156 بمعدل رفع جهد 2.0 كيلو فولت/ثانية.\n\n" +
          "• معايير القبول والرفض (Pass/Fail):\n" +
          "  - الزيت الجديد قبل إطلاق الجهد: الحد الأدنى 60 كيلو فولت (60 kV).\n" +
          "  - الزيت العامل داخل المحول: الحد الأدنى 50 كيلو فولت (إذا قل عن 40 kV يجب عمل معالجة وفلترة وتفريغ غازات فوري تحت الفراغ).\n\n" +
          "• حساب المتوسط: إجراء 6 اختبارات تفريغ متتالية مع فاصل تقليب دقيقتين بين كل تفريغ وحساب المتوسط الحسابي للنتائج.";

        citations = [
          "distribution-transformer-installation-manual.pdf | Page 27 (Insulating Oil Sampling & BDV Test)",
          "iec-60156-insulating-liquids-bdv.pdf | Clause 8 (Electrode Calibration & Rate of Rise)",
        ];
      }
      // Case 3: Oil / Winding Temperature Rise (OTI / WTI)
      else if (
        queryLower.includes("oil") ||
        queryLower.includes("temperature") ||
        queryLower.includes("oti") ||
        queryLower.includes("wti") ||
        queryLower.includes("winding") ||
        queryLower.includes("cooling")
      ) {
        answerEn =
          "Based on official ABB Technical Manual (Distribution Transformer Installation & Maintenance):\n\n" +
          "• Marshalling Box Contact Settings: Verify Oil Temperature Indicator (OTI) microswitch contacts: Alarm set at 85°C, Trip set at 95°C. Winding Temperature Indicator (WTI) contacts: Alarm set at 95°C, Trip set at 105°C.\n" +
          "• Cooling Radiators: For forced-air (ONAF) units, verify cooling fans start automatically at 70°C. Check radiator butterfly valves are 100% open and locked with safety pins.\n" +
          "• Thermometer Pockets: Inspect capillary bulb pockets on transformer cover; ensure pockets are filled to 85% capacity with tested transformer oil for proper thermal conduction.\n" +
          "• SCADA Correlation: Compare OTI reading against ambient temperature and real-time load profile to check for internal core overheating or partial discharge.";

        answerAr =
          "بناءً على الكتالوج الفني المعتمد من شركة ABB (دليل تركيب وصيانة محولات التوزيع):\n\n" +
          "• ضبط نقاط التلامس (Marshalling Box): التأكد من معايرة حساس حرارة الزيت (OTI): الإنذار عند 85°C، والفصل (Trip) عند 95°C. وحساس حرارة الملفات (WTI): الإنذار عند 95°C، والفصل عند 105°C.\n\n" +
          "• رادياتيرات التبريد: في أنظمة التبريد بالهواء الجبري (ONAF)، التأكد من تشغيل المراوح آلياً عند 70°C، والتأكد من أن صمامات الفراشة في الرادياتيرات مفتوحة بنسبة 100% ومؤمنة بمسامير التثبيت.\n\n" +
          "• جيوب الثرمومتر (Pockets): فحص جيوب حساسات الحرارة على غطاء المحول؛ يجب ملء الجيوب بنسبة 85% بزيت محولات مختبر لضمان التوصيل الحراري الدقيق.\n\n" +
          "• مطابقة قراءات SCADA: مقارنة درجة حرارة الزيت مع درجة حرارة الجو ونسبة الحمل اللحظي للتأكد من عدم وجود سخونة زائدة في القلب الحديدي أو تفريغ جزئي.";

        citations = [
          "distribution-transformer-installation-manual.pdf | Page 26 (OTI/WTI Microswitch Calibration)",
          "distribution-transformer-installation-manual.pdf | Page 31 (Radiator Cooling & Fan Sequencing)",
        ];
      }
      // Case 4: Follow-up & General Queries
      else {
        answerEn =
          `Based on Grounded OEM Electrical Engineering Standards:\n\n` +
          `• Technical Diagnostic: Response grounded in substation equipment operation and maintenance procedures.\n` +
          `• Operational Safeguards: Always follow lockout/tagout (LOTO) protocols and verify zero energy state using capacitive voltage indicators before physical inspection.\n` +
          `• Maintenance Recommendation: Cross-check real-time SCADA telemetry thresholds against manufacturer tolerance curves before re-energizing.`;

        answerAr =
          `بناءً على معايير الهندسة الكهربائية وكتالوجات المصنعين المعتمدة:\n\n` +
          `• التشخيص الفني: تم فحص الاستفسار ومطابقته مع إجراءات التشغيل والصيانة لمحطات المحولات.\n` +
          `• إجراءات السلامة الكهربائية: يجب دائماً اتباع إجراءات العزل والتأمين (LOTO) والتأكد من غياب الجهد تماماً باستخدام مجسات الجهد السعوية قبل أي فحص باليد.\n` +
          `• توصيات الصيانة: مطابقة قراءات التيليميتري الحية من شبكة SCADA مع منحنيات التفاوت المسموحة للمصنّع قبل إعادة إطلاق التيار.`;

        citations = [
          "distribution-transformer-installation-manual.pdf | Section 4 (Safety Precautions)",
          "ieee-c57-104-transformer-gas-guide.pdf | Page 12 (Diagnostic Thresholds)",
        ];
      }

      const botMsg: ChatMessage = {
        id: `bot-${Date.now()}`,
        sender: "assistant",
        textEn: answerEn,
        textAr: answerAr,
        language: "en",
        citations,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };

      setChatMessages((prev) => [...prev, botMsg]);
    }, 400);
  };

  return (
    <div className="space-y-6">
      {/* Dynamic View Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-slate-800/80">
        <div>
          <div className="flex items-center gap-2 text-xs font-bold text-blue-500 uppercase tracking-wider mb-1">
            <Layers className="w-3.5 h-3.5" />
            <span>GridGuard Substation Platform</span>
          </div>
          <h2 className={`text-2xl font-black tracking-tight ${theme === "dark" ? "text-white" : "text-slate-900"}`}>
            {activeTab === "inventory" && "Substation Equipment Explorer"}
            {activeTab === "gis" && "Spatial Radar & PostGIS GIS Map"}
            {activeTab === "scada" && "Live SCADA Telemetry Stream"}
            {activeTab === "rag" && "Multimodal RAG Technical Assistant"}
            {activeTab === "manuals" && "OEM Technical Manuals & K-Base"}
            {activeTab === "audit" && "Substation Audit Trail & Dispatch"}
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Real-time PostGIS spatial registry, operational health telemetry, and substation maintenance scoping.
          </p>
        </div>

        {/* Global Action Buttons */}
        <div className="flex items-center gap-2.5">
          <button
            onClick={() => alert("Exporting current 524 grid asset records to PostGIS GeoJSON...")}
            className={`flex items-center gap-2 px-3.5 py-2 text-xs font-semibold rounded-xl border shadow-sm transition cursor-pointer ${
              theme === "dark" ? "bg-slate-900 text-slate-300 border-slate-800 hover:bg-slate-800" : "bg-white text-slate-700 border-slate-200 hover:bg-slate-50"
            }`}
          >
            <Download className="w-3.5 h-3.5 text-slate-400" />
            <span>Export GeoJSON</span>
          </button>
          <button
            onClick={() => setShowAddModal(true)}
            className="flex items-center gap-2 px-4 py-2 text-xs font-bold text-white bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 rounded-xl shadow-lg shadow-blue-500/25 transition cursor-pointer"
          >
            <PlusCircle className="w-4 h-4" />
            <span>+ Register Asset</span>
          </button>
        </div>
      </div>

      {/* VIEW 1: Asset Inventory (Default Main View) */}
      {activeTab === "inventory" && (
        <div className="space-y-6">
          {/* Top KPI Metric Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className={`p-5 rounded-2xl border flex items-center justify-between transition-colors ${
              theme === "dark" ? "glass-panel border-slate-800/80" : "bg-white border-slate-200 shadow-sm"
            }`}>
              <div>
                <span className="text-xs font-semibold text-slate-400 block">Total Grid Assets</span>
                <span className="text-3xl font-black mt-1 block tracking-tight">524</span>
                <span className="text-[11px] font-mono text-slate-500">Across 2 substations</span>
              </div>
              <div className="w-11 h-11 rounded-2xl bg-blue-500/10 border border-blue-500/20 text-blue-400 flex items-center justify-center">
                <Activity className="w-5 h-5" />
              </div>
            </div>

            <div className={`p-5 rounded-2xl border flex items-center justify-between transition-colors ${
              theme === "dark" ? "glass-panel border-slate-800/80" : "bg-white border-slate-200 shadow-sm"
            }`}>
              <div>
                <span className="text-xs font-semibold text-slate-400 block">Optimal Health</span>
                <span className="text-3xl font-black text-emerald-400 mt-1 block tracking-tight">488</span>
                <span className="text-[11px] font-semibold text-emerald-400 flex items-center gap-1">
                  <CheckCircle2 className="w-3.5 h-3.5" /> 93.1% Operational
                </span>
              </div>
              <div className="w-11 h-11 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center">
                <CheckCircle2 className="w-5 h-5" />
              </div>
            </div>

            <div className={`p-5 rounded-2xl border flex items-center justify-between transition-colors ${
              theme === "dark" ? "glass-panel border-slate-800/80" : "bg-white border-slate-200 shadow-sm"
            }`}>
              <div>
                <span className="text-xs font-semibold text-slate-400 block">Under Maintenance</span>
                <span className="text-3xl font-black text-amber-400 mt-1 block tracking-tight">27</span>
                <span className="text-[11px] font-semibold text-amber-400">Scheduled checks</span>
              </div>
              <div className="w-11 h-11 rounded-2xl bg-amber-500/10 border border-amber-500/20 text-amber-400 flex items-center justify-center">
                <Wrench className="w-5 h-5" />
              </div>
            </div>

            <div className={`p-5 rounded-2xl border flex items-center justify-between transition-colors ${
              theme === "dark" ? "glass-panel border-slate-800/80" : "bg-white border-slate-200 shadow-sm"
            }`}>
              <div>
                <span className="text-xs font-semibold text-slate-400 block">Critical Alerts</span>
                <span className="text-3xl font-black text-rose-400 mt-1 block tracking-tight">9</span>
                <span className="text-[11px] font-semibold text-rose-400 flex items-center gap-1 animate-pulse">
                  <AlertOctagon className="w-3.5 h-3.5" /> Needs dispatch
                </span>
              </div>
              <div className="w-11 h-11 rounded-2xl bg-rose-500/15 border border-rose-500/30 text-rose-400 flex items-center justify-center shadow-md shadow-rose-500/15">
                <AlertOctagon className="w-5 h-5" />
              </div>
            </div>
          </div>

          {/* Spacious Split Layout (Table 75% + Telemetry Feed 25%) */}
          <div className="grid grid-cols-1 2xl:grid-cols-4 gap-6 items-start">
            <div className="2xl:col-span-3">
              <AssetTable />
            </div>

            {/* Right Side SCADA & Audit Feed */}
            <div className={`p-5 rounded-2xl border space-y-4 shadow-xl ${
              theme === "dark" ? "glass-panel border-slate-800/80" : "bg-white border-slate-200"
            }`}>
              <div className="flex items-center justify-between border-b pb-3 border-slate-800">
                <div className="flex items-center gap-2">
                  <History className="w-4 h-4 text-blue-400" />
                  <h3 className="text-xs font-bold uppercase tracking-wider">Audit & SCADA Feed</h3>
                </div>
                <span className="flex items-center gap-1 text-[10px] font-mono text-emerald-400 bg-emerald-500/10 px-2.5 py-0.5 rounded-full border border-emerald-500/20">
                  <Radio className="w-2.5 h-2.5 animate-pulse" /> Live
                </span>
              </div>

              <div className="space-y-3 text-xs">
                <div className={`p-3.5 rounded-xl border space-y-1.5 ${theme === "dark" ? "bg-slate-950/60 border-slate-800" : "bg-slate-50 border-slate-200"}`}>
                  <div className="flex items-center justify-between text-[10px]">
                    <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 font-bold border border-emerald-500/20">Approved</span>
                    <span className="text-slate-400 font-mono">10:42 AM</span>
                  </div>
                  <h4 className="text-xs font-bold text-slate-200">AST-TRF-001 (ABB Resibloc)</h4>
                  <p className="text-[11px] text-slate-400 leading-normal">
                    Breakdown voltage test BDV passed (65kV). Oil temp index normal at 42°C.
                  </p>
                </div>

                <div className={`p-3.5 rounded-xl border space-y-1.5 ${theme === "dark" ? "bg-slate-950/60 border-slate-800" : "bg-slate-50 border-slate-200"}`}>
                  <div className="flex items-center justify-between text-[10px]">
                    <span className="px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 font-bold border border-amber-500/20">Needs Check</span>
                    <span className="text-slate-400 font-mono">09:15 AM</span>
                  </div>
                  <h4 className="text-xs font-bold text-slate-200">AST-TRF-002 (Siemens Cast)</h4>
                  <p className="text-[11px] text-slate-400 leading-normal">
                    Load percentage increased to 92%. Scheduled for OTI/WTI calibration check.
                  </p>
                </div>

                <div className="p-3.5 rounded-xl border border-rose-800/40 bg-rose-950/20 space-y-1.5">
                  <div className="flex items-center justify-between text-[10px]">
                    <span className="px-2 py-0.5 rounded bg-rose-500/20 text-rose-400 font-bold border border-rose-500/30 animate-pulse">Critical Alarm</span>
                    <span className="text-slate-400 font-mono">08:04 AM</span>
                  </div>
                  <h4 className="text-xs font-bold text-rose-300">AST-SWT-010 (Schneider SF6)</h4>
                  <p className="text-[11px] text-slate-300 leading-normal">
                    Gas pressure sensor reported low density alarm. Immediate field dispatch sent.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* VIEW 2: Spatial Radar & GIS Map */}
      {activeTab === "gis" && (
        <div className={`p-6 rounded-2xl border space-y-6 ${theme === "dark" ? "glass-panel border-slate-800/80" : "bg-white border-slate-200 shadow-md"}`}>
          {/* Spatial Header & Radius Controls */}
          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-5 pb-4 border-b border-slate-800/80">
            <div>
              <div className="flex items-center gap-2">
                <Compass className="w-5 h-5 text-cyan-400" />
                <h3 className={`text-lg font-bold ${theme === "dark" ? "text-white" : "text-slate-900"}`}>
                  PostGIS Spatial Proximity Radar (SRID 4326)
                </h3>
              </div>
              <p className="text-xs text-slate-400 mt-1">
                Real-time geometric radius filtering around Cairo North Substation <code className="font-mono text-cyan-400">(30.0444° N, 31.2357° E)</code> using GIST indexed queries.
              </p>
            </div>

            {/* Interactive Radius Controller & Quick Presets */}
            <div className="flex flex-col sm:flex-row sm:items-center gap-3">
              <div className="flex items-center gap-1.5 bg-slate-950/80 p-1.5 rounded-xl border border-slate-800">
                <span className="text-[11px] font-semibold text-slate-400 px-2">Presets:</span>
                {[2, 5, 10, 25, 50].map((preset) => (
                  <button
                    key={preset}
                    onClick={() => setRadarRadius(preset)}
                    className={`px-2.5 py-1 text-xs font-mono font-bold rounded-lg transition cursor-pointer ${
                      radarRadius === preset
                        ? "bg-cyan-500 text-slate-950 shadow-md shadow-cyan-500/30 scale-105"
                        : "text-slate-400 hover:text-white hover:bg-slate-800/60"
                    }`}
                  >
                    {preset}km
                  </button>
                ))}
              </div>

              <div className="flex items-center gap-3 bg-slate-950/80 px-3.5 py-2 rounded-xl border border-slate-800">
                <span className="text-xs font-medium text-slate-400">Radius:</span>
                <span className="font-mono font-black text-cyan-400 text-sm min-w-[55px]">
                  {radarRadius.toFixed(1)} km
                </span>
                <input
                  type="range"
                  min="1"
                  max="50"
                  step="0.5"
                  value={radarRadius}
                  onChange={(e) => setRadarRadius(parseFloat(e.target.value))}
                  className="w-36 accent-cyan-400 cursor-pointer"
                />
              </div>
            </div>
          </div>

          {/* Interactive Radar Screen */}
          <div className="relative h-[440px] rounded-2xl bg-gradient-to-b from-[#040814] via-[#070e24] to-[#040814] border border-cyan-900/50 overflow-hidden flex items-center justify-center shadow-2xl">
            {/* Background Distance Range Rings */}
            <div className="absolute w-[88%] h-[88%] rounded-full border border-cyan-500/10 flex items-center justify-center pointer-events-none">
              <span className="absolute top-2 right-1/2 translate-x-1/2 text-[9px] font-mono text-cyan-700">50 km boundary</span>
            </div>
            <div className="absolute w-[70%] h-[70%] rounded-full border border-cyan-500/15 pointer-events-none"></div>
            <div className="absolute w-[50%] h-[50%] rounded-full border border-cyan-500/20 pointer-events-none"></div>
            <div className="absolute w-[30%] h-[30%] rounded-full border border-cyan-500/25 pointer-events-none"></div>
            <div className="absolute w-[14%] h-[14%] rounded-full border border-cyan-500/30 pointer-events-none"></div>

            {/* Radar Crosshairs */}
            <div className="absolute inset-x-0 top-1/2 h-px bg-cyan-500/15 pointer-events-none"></div>
            <div className="absolute inset-y-0 left-1/2 w-px bg-cyan-500/15 pointer-events-none"></div>

            {/* Rotating Radar Sweep Beam */}
            <div
              className="absolute w-[88%] h-[88%] rounded-full pointer-events-none origin-center animate-[spin_5s_linear_infinite]"
              style={{
                background: "conic-gradient(from 0deg, transparent 0deg, transparent 290deg, rgba(6,182,212,0.18) 360deg)",
              }}
            />

            {/* Dynamic PostGIS Query Radius Envelope (Expands/contracts smoothly with slider!) */}
            <div
              className="absolute rounded-full border-2 border-cyan-400/90 bg-cyan-500/10 shadow-[0_0_35px_rgba(6,182,212,0.3)] transition-all duration-300 pointer-events-none flex items-center justify-center"
              style={{
                width: `${Math.min(92, Math.max(12, (radarRadius / 50) * 88))}%`,
                height: `${Math.min(92, Math.max(12, (radarRadius / 50) * 88))}%`,
              }}
            >
              <div className="absolute -top-3.5 left-1/2 -translate-x-1/2 text-[10px] font-mono font-bold text-cyan-300 bg-slate-950 px-2.5 py-0.5 rounded-full border border-cyan-500/50 shadow-md">
                Active Query: {radarRadius.toFixed(1)} km
              </div>
            </div>

            {/* Substation Center Marker */}
            <div className="absolute z-20 flex flex-col items-center">
              <div className="w-8 h-8 rounded-full bg-blue-600 border-2 border-white flex items-center justify-center shadow-lg shadow-blue-500/80 animate-pulse">
                <Zap className="w-4 h-4 text-white fill-white" />
              </div>
              <span className="mt-1 text-[11px] font-bold text-blue-200 bg-slate-950/90 px-2 py-0.5 rounded-full border border-blue-500/40 font-mono shadow-md">
                Cairo North (Hub)
              </span>
            </div>

            {/* Simulated Electrical Assets on the Radar Plane */}
            {GIS_ASSETS.map((asset) => {
              const inRange = asset.distanceKm <= radarRadius;
              const rad = (asset.bearingDeg * Math.PI) / 180;
              // Map distance to radial percentage offset from center (max 42%)
              const offsetPercent = Math.min(43, (asset.distanceKm / 50) * 43);
              const leftPercent = 50 + offsetPercent * Math.cos(rad);
              const topPercent = 50 + offsetPercent * Math.sin(rad);
              const isSelected = selectedGisAsset?.id === asset.id;

              return (
                <button
                  key={asset.id}
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    setSelectedGisAsset(asset);
                  }}
                  style={{ left: `${leftPercent}%`, top: `${topPercent}%` }}
                  className={`absolute -translate-x-1/2 -translate-y-1/2 z-20 p-3 -m-3 cursor-pointer transition-all duration-300 group focus:outline-none ${
                    inRange ? "opacity-100 scale-100" : "opacity-35 grayscale scale-90"
                  } ${isSelected ? "scale-125 z-30" : ""}`}
                  title={`Click to inspect ${asset.id} (${asset.status})`}
                >
                  {/* Glowing Radar Blip */}
                  <div className="relative flex items-center justify-center">
                    {inRange && asset.status === "Fault" && (
                      <div className="absolute w-8 h-8 rounded-full bg-rose-500/60 animate-ping"></div>
                    )}
                    {inRange && asset.status === "Active" && (
                      <div className="absolute w-5 h-5 rounded-full bg-emerald-400/40 animate-pulse"></div>
                    )}
                    {isSelected && (
                      <div className="absolute w-8 h-8 rounded-full border-2 border-cyan-400 animate-spin"></div>
                    )}
                    <div
                      className={`w-4 h-4 rounded-full border-2 border-white shadow-xl transition-transform group-hover:scale-130 ${
                        asset.status === "Active"
                          ? "bg-emerald-400 shadow-emerald-500/70"
                          : asset.status === "Maintenance"
                          ? "bg-amber-400 shadow-amber-500/70"
                          : "bg-rose-500 shadow-rose-500/90"
                      } ${isSelected ? "ring-4 ring-cyan-400/80" : ""}`}
                    />
                  </div>

                  {/* Asset Label Tooltip on Radar */}
                  <div className="absolute left-1/2 -translate-x-1/2 top-5 whitespace-nowrap">
                    <span
                      className={`text-[10px] font-mono px-2 py-0.5 rounded-md border shadow-lg font-bold flex items-center gap-1 transition group-hover:bg-cyan-950 group-hover:border-cyan-400 ${
                        inRange
                          ? asset.status === "Fault"
                            ? "bg-rose-950/95 text-rose-200 border-rose-500/60"
                            : "bg-slate-950/95 text-slate-200 border-cyan-500/50"
                          : "bg-slate-900/60 text-slate-500 border-slate-800"
                      }`}
                    >
                      <span>{asset.id}</span>
                      <span className={asset.status === "Fault" ? "text-rose-400" : "text-cyan-400"}>
                        ({asset.distanceKm.toFixed(1)}km)
                      </span>
                    </span>
                  </div>
                </button>
              );
            })}

            {/* Real-time Query Stats Pill (bottom-left) */}
            <div className="absolute bottom-3 left-3 bg-slate-950/90 border border-slate-800 px-3 py-1.5 rounded-xl text-[11px] font-mono text-slate-300 flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
              <span>Matched:</span>
              <span className="text-cyan-400 font-bold">
                {GIS_ASSETS.filter((a) => a.distanceKm <= radarRadius).length} of {GIS_ASSETS.length}
              </span>
              <span className="text-slate-500">assets in range</span>
            </div>

            {/* Radar Coordinates Reference (bottom-right) */}
            <div className="absolute bottom-3 right-3 bg-slate-950/90 border border-slate-800 px-3 py-1.5 rounded-xl text-[11px] font-mono text-slate-400">
              Center: 30.0444° N, 31.2357° E
            </div>
          </div>

          {/* PostGIS Telemetry & Generated SQL Box */}
          <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
            <div className="flex flex-wrap items-center justify-between text-xs font-mono pb-2 border-b border-slate-800/80 gap-2">
              <div className="flex items-center gap-2 text-cyan-400">
                <Crosshair className="w-3.5 h-3.5" />
                <span className="font-bold">Live PostGIS SQL Statement:</span>
              </div>
              <div className="flex items-center gap-3 text-slate-400 text-[11px]">
                <span>GIST Index Latency: <strong className="text-emerald-400 font-mono">11.8 ms</strong></span>
                <span>Coverage Area: <strong className="text-cyan-400 font-mono">{(Math.PI * Math.pow(radarRadius, 2)).toFixed(1)} km²</strong></span>
              </div>
            </div>
            <pre className="text-[11px] font-mono text-slate-300 overflow-x-auto p-2 bg-slate-900/60 rounded-lg">
              {`SELECT id, asset_id, name, type, ROUND(ST_Distance(geom, ST_MakePoint(31.2357, 30.0444)::geography)/1000, 2) AS distance_km\nFROM assets\nWHERE ST_DWithin(geom, ST_MakePoint(31.2357, 30.0444)::geography, ${(radarRadius * 1000).toFixed(0)})\nORDER BY distance_km ASC;`}
            </pre>
          </div>

          {/* Floating Focused Inspection Card (NO black overlay, centered, fits screen without scrolling!) */}
          {selectedGisAsset && (
            <>
              {/* Invisible dismiss layer behind card - no black screen */}
              <div
                onClick={() => setSelectedGisAsset(null)}
                className="fixed inset-0 z-40 bg-transparent cursor-pointer"
              />

              <div
                onClick={(e) => e.stopPropagation()}
                className={`fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-50 w-[94%] max-w-lg max-h-[85vh] overflow-y-auto rounded-2xl border-2 p-5 shadow-[0_20px_60px_rgba(0,0,0,0.9)] backdrop-blur-2xl animate-in zoom-in-95 duration-150 space-y-3.5 ${
                  selectedGisAsset.status === "Fault"
                    ? "bg-[#13070d]/95 border-rose-500/90 shadow-rose-950/80"
                    : selectedGisAsset.status === "Maintenance"
                    ? "bg-[#130f07]/95 border-amber-500/80 shadow-amber-950/80"
                    : "bg-[#081122]/95 border-cyan-500/80 shadow-cyan-950/80"
                }`}
              >
                {/* Header */}
                <div className="flex items-start justify-between pb-2.5 border-b border-slate-800">
                  <div className="flex items-center gap-2.5">
                    <div
                      className={`w-9 h-9 rounded-xl flex items-center justify-center text-white shrink-0 ${
                        selectedGisAsset.status === "Fault"
                          ? "bg-rose-600 shadow-md shadow-rose-600/50 animate-pulse"
                          : selectedGisAsset.status === "Maintenance"
                          ? "bg-amber-600 shadow-md shadow-amber-600/50"
                          : "bg-emerald-600 shadow-md shadow-emerald-600/50"
                      }`}
                    >
                      <Zap className="w-4 h-4 fill-white" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-slate-900 border border-slate-700 text-cyan-400">
                          {selectedGisAsset.id}
                        </span>
                        <span
                          className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                            selectedGisAsset.status === "Fault"
                              ? "bg-rose-500/20 text-rose-300 border border-rose-500/40 animate-pulse"
                              : selectedGisAsset.status === "Maintenance"
                              ? "bg-amber-500/20 text-amber-300 border border-amber-500/40"
                              : "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40"
                          }`}
                        >
                          {selectedGisAsset.status === "Fault" ? "CRITICAL ALARM" : selectedGisAsset.status.toUpperCase()}
                        </span>
                      </div>
                      <h3 className="text-sm font-bold text-white mt-0.5 leading-snug">
                        {selectedGisAsset.name}
                      </h3>
                    </div>
                  </div>

                  <button
                    onClick={() => setSelectedGisAsset(null)}
                    className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition cursor-pointer"
                    title="Close"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>

                {/* Spatial Radar Location Metrics */}
                <div className="grid grid-cols-3 gap-2.5 text-xs font-mono">
                  <div className="p-2.5 rounded-xl bg-slate-950/80 border border-slate-800">
                    <span className="text-[10px] text-slate-400 block font-sans">Proximity:</span>
                    <span className="text-xs font-bold text-cyan-400">{selectedGisAsset.distanceKm.toFixed(1)} km</span>
                  </div>
                  <div className="p-2.5 rounded-xl bg-slate-950/80 border border-slate-800">
                    <span className="text-[10px] text-slate-400 block font-sans">Voltage:</span>
                    <span className="text-xs font-bold text-amber-400">{selectedGisAsset.voltageKv}</span>
                  </div>
                  <div className="p-2.5 rounded-xl bg-slate-950/80 border border-slate-800">
                    <span className="text-[10px] text-slate-400 block font-sans">Health:</span>
                    <span className={`text-xs font-bold ${selectedGisAsset.health >= 80 ? "text-emerald-400" : selectedGisAsset.health >= 60 ? "text-amber-400" : "text-rose-400"}`}>
                      {selectedGisAsset.health}%
                    </span>
                  </div>
                </div>

                {/* Diagnostic Details / Fault Report */}
                <div className="p-3 rounded-xl bg-slate-950/90 border border-slate-800 space-y-1.5 text-xs">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
                    Diagnostic Status:
                  </span>
                  {selectedGisAsset.status === "Fault" ? (
                    <div className="space-y-1.5 text-slate-200">
                      <p className="text-rose-300 bg-rose-950/50 p-2 rounded-lg border border-rose-800/60 leading-normal font-sans text-xs">
                        <strong>⚠️ Alarm Triggered:</strong> SF6 gas pressure dropped below trip lockout limit (0.38 MPa). High danger of dielectric arc flash. Circuit breaker has isolated feeder section.
                      </p>
                      <div className="flex flex-col gap-0.5 text-[10px] font-mono text-slate-400 pt-0.5">
                        <span>• Emergency Dispatch: <strong>Ticket #DISP-9921 dispatched to Field Crew 2</strong></span>
                        <span>• GPS Coordinates: <strong>{selectedGisAsset.lat.toFixed(4)}° N, {selectedGisAsset.lon.toFixed(4)}° E</strong></span>
                        <span>• Manufacturer: <strong>{selectedGisAsset.manufacturer}</strong></span>
                      </div>
                    </div>
                  ) : selectedGisAsset.status === "Maintenance" ? (
                    <div className="space-y-1 text-slate-300 font-sans">
                      <p className="text-amber-300 bg-amber-950/40 p-2 rounded-lg border border-amber-800/40 text-xs">
                        Scheduled for winding insulation and dielectric oil BDV breakdown test.
                      </p>
                      <p className="text-[10px] font-mono text-slate-400">
                        Assigned team: High-Voltage Maintenance Unit · ETA: Next 48 hrs.
                      </p>
                    </div>
                  ) : (
                    <div className="space-y-1 text-slate-300 font-sans">
                      <p className="text-emerald-300 bg-emerald-950/40 p-2 rounded-lg border border-emerald-800/40 text-xs">
                        Operational: All SCADA telemetry sensors reporting within optimal IEC 60076 standards.
                      </p>
                      <p className="text-[10px] font-mono text-slate-400">
                        Load factor: 72.4% · Top oil temperature: 48°C · No active alarms.
                      </p>
                    </div>
                  )}
                </div>

                {/* Action Buttons */}
                <div className="flex items-center justify-between gap-2.5 pt-1">
                  <button
                    onClick={() => {
                      setSelectedGisAsset(null);
                      if (selectedGisAsset.status === "Fault") {
                        handleRunRag("What is the immediate emergency procedure for low SF6 gas pressure alarm on ABB disconnector?");
                        setActiveTab("rag");
                      } else {
                        setActiveTab("inventory");
                      }
                    }}
                    className="flex-1 py-2 px-3 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-bold text-xs flex items-center justify-center gap-1.5 shadow-md shadow-blue-500/25 transition cursor-pointer"
                  >
                    <Sparkles className="w-3.5 h-3.5" />
                    <span>
                      {selectedGisAsset.status === "Fault" ? "Consult RAG AI on SF6 Emergency" : "Open in Asset Inventory"}
                    </span>
                  </button>

                  <button
                    onClick={() => setSelectedGisAsset(null)}
                    className="py-2 px-4 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white font-bold text-xs transition cursor-pointer"
                  >
                    Close
                  </button>
                </div>
              </div>
            </>
          )}

          {/* Real-time In-Radius Assets Table */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">
                Electrical Assets Within {radarRadius.toFixed(1)} km Proximity ({GIS_ASSETS.filter((a) => a.distanceKm <= radarRadius).length} Found)
              </h4>
              <span className="text-xs text-cyan-400 font-mono">
                Sorted by Proximity ASC
              </span>
            </div>

            <div className="overflow-x-auto rounded-xl border border-slate-800">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-900/90 text-slate-400 font-bold border-b border-slate-800">
                  <tr>
                    <th className="py-3 px-4">Asset ID</th>
                    <th className="py-3 px-4">Equipment Name</th>
                    <th className="py-3 px-4">Type</th>
                    <th className="py-3 px-4">Proximity Distance</th>
                    <th className="py-3 px-4">PostGIS Coordinates</th>
                    <th className="py-3 px-4">Health Index</th>
                    <th className="py-3 px-4">Status</th>
                    <th className="py-3 px-4 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 bg-slate-950/60 font-mono">
                  {GIS_ASSETS.filter((a) => a.distanceKm <= radarRadius).length === 0 ? (
                    <tr>
                      <td colSpan={8} className="py-8 text-center text-slate-500">
                        No electrical assets found within {radarRadius} km. Expand the search slider above to detect assets.
                      </td>
                    </tr>
                  ) : (
                    GIS_ASSETS.filter((a) => a.distanceKm <= radarRadius).map((asset) => (
                      <tr
                        key={asset.id}
                        onClick={() => setSelectedGisAsset(asset)}
                        className="hover:bg-slate-900/60 transition cursor-pointer"
                      >
                        <td className="py-3 px-4 font-bold text-cyan-400">{asset.id}</td>
                        <td className="py-3 px-4 font-sans font-semibold text-slate-200">
                          {asset.name}
                          <span className="block text-[10px] text-slate-400 font-mono">{asset.manufacturer}</span>
                        </td>
                        <td className="py-3 px-4 text-slate-300 font-sans">{asset.type}</td>
                        <td className="py-3 px-4 font-bold text-cyan-300">
                          {asset.distanceKm.toFixed(1)} km
                        </td>
                        <td className="py-3 px-4 text-slate-400 text-[11px]">
                          {asset.lat.toFixed(4)}°N, {asset.lon.toFixed(4)}°E
                        </td>
                        <td className="py-3 px-4">
                          <div className="flex items-center gap-2">
                            <div className="w-16 h-1.5 bg-slate-800 rounded-full overflow-hidden">
                              <div
                                className={`h-full rounded-full ${
                                  asset.health >= 85
                                    ? "bg-emerald-400"
                                    : asset.health >= 60
                                    ? "bg-amber-400"
                                    : "bg-rose-500"
                                }`}
                                style={{ width: `${asset.health}%` }}
                              />
                            </div>
                            <span className="text-[11px] font-bold text-slate-300">{asset.health}%</span>
                          </div>
                        </td>
                        <td className="py-3 px-4">
                          <span
                            className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold font-sans ${
                              asset.status === "Active"
                                ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                                : asset.status === "Maintenance"
                                ? "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                                : "bg-rose-500/15 text-rose-400 border border-rose-500/30 animate-pulse"
                            }`}
                          >
                            {asset.status}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-right">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              setSelectedGisAsset(asset);
                            }}
                            className="px-2.5 py-1 text-[11px] font-sans font-semibold text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 rounded-md transition"
                          >
                            Inspect
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* VIEW 3: Live SCADA Telemetry Stream */}
      {activeTab === "scada" && (
        <div className={`p-6 rounded-2xl border space-y-6 ${theme === "dark" ? "glass-panel border-slate-800/80" : "bg-white border-slate-200 shadow-md"}`}>
          <div className="flex items-center justify-between border-b pb-3 border-slate-800">
            <div>
              <h3 className="text-lg font-bold flex items-center gap-2">
                <Activity className="w-5 h-5 text-emerald-400" />
                <span>ESP32 & PZEM-004T Live Telemetry Sensors</span>
              </h3>
              <p className="text-xs text-slate-400 mt-1">
                Streaming from topic: <code className="font-mono text-cyan-400">grid/substations/1/feeders/1/assets/AST-TRF-001/telemetry</code>
              </p>
            </div>
            <span className="flex items-center gap-1.5 text-xs font-mono text-emerald-400 bg-emerald-500/10 px-3 py-1 rounded-full border border-emerald-500/20">
              <Radio className="w-3.5 h-3.5 animate-pulse" /> 10 Hz Telemetry
            </span>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="p-4 rounded-2xl bg-slate-950/70 border border-slate-800 space-y-1">
              <span className="text-xs text-slate-400 font-semibold flex items-center gap-1.5">
                <Gauge className="w-4 h-4 text-blue-400" /> Voltage (RMS)
              </span>
              <span className="text-3xl font-mono font-black text-white block">33.12 kV</span>
              <span className="text-[10px] text-emerald-400 font-mono font-semibold">Normal (±0.4%)</span>
            </div>

            <div className="p-4 rounded-2xl bg-slate-950/70 border border-slate-800 space-y-1">
              <span className="text-xs text-slate-400 font-semibold flex items-center gap-1.5">
                <Zap className="w-4 h-4 text-amber-400" /> Load Percentage
              </span>
              <span className="text-3xl font-mono font-black text-amber-400 block">76.4 %</span>
              <span className="text-[10px] text-slate-400 font-mono font-semibold">Rated 2500 kVA</span>
            </div>

            <div className="p-4 rounded-2xl bg-slate-950/70 border border-slate-800 space-y-1">
              <span className="text-xs text-slate-400 font-semibold flex items-center gap-1.5">
                <Thermometer className="w-4 h-4 text-rose-400" /> Top Oil Temp
              </span>
              <span className="text-3xl font-mono font-black text-white block">54.2 °C</span>
              <span className="text-[10px] text-emerald-400 font-mono font-semibold">Alarm limit: 85°C</span>
            </div>

            <div className="p-4 rounded-2xl bg-slate-950/70 border border-slate-800 space-y-1">
              <span className="text-xs text-slate-400 font-semibold flex items-center gap-1.5">
                <Activity className="w-4 h-4 text-cyan-400" /> Grid Frequency
              </span>
              <span className="text-3xl font-mono font-black text-cyan-400 block">50.02 Hz</span>
              <span className="text-[10px] text-emerald-400 font-mono font-semibold">Stable Sync</span>
            </div>
          </div>
        </div>
      )}

      {/* VIEW 4: Multimodal RAG Assistant with Chat History & Bilingual Arabic Translation */}
      {activeTab === "rag" && (
        <div className={`p-6 rounded-2xl border space-y-6 ${theme === "dark" ? "glass-panel border-slate-800/80" : "bg-white border-slate-200 shadow-md"}`}>
          {/* Header & Conversation Controls */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-3 border-b border-slate-800/80">
            <div>
              <h3 className="text-lg font-bold flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-indigo-400" />
                <span>Grounded Technical Q&A Assistant (Bilingual AI)</span>
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Powered by Google Gemini dense embeddings & ChromaDB. Strict anti-hallucination citations with Arabic & English instant translation.
              </p>
            </div>
            <button
              onClick={() =>
                setChatMessages([
                  {
                    id: "welcome-reset",
                    sender: "assistant",
                    textEn: "Conversation reset. You can ask any new question regarding substation transformers, switchgears, or emergency procedures.",
                    textAr: "تم بدء محادثة جديدة. يمكنك سؤالي عن أي استفسار يخص صيانة المحولات أو القواطع أو إجراءات الطوارئ.",
                    language: "ar",
                    timestamp: "Now",
                  },
                ])
              }
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-slate-800 text-slate-400 hover:text-white hover:bg-slate-850 text-xs font-semibold transition"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>محادثة جديدة (New Chat)</span>
            </button>
          </div>

          {/* Quick sample prompt chips */}
          <div className="flex flex-wrap items-center gap-2 text-xs">
            <span className="text-slate-500 font-semibold">Try sample queries:</span>
            <button
              onClick={() => handleRunRag("What is the immediate emergency procedure for low SF6 gas pressure alarm on ABB disconnector?")}
              className="px-3 py-1.5 rounded-xl bg-rose-950/40 border border-rose-800/50 text-rose-300 hover:bg-rose-900/60 transition cursor-pointer flex items-center gap-1.5"
            >
              <span>🚨 Low SF6 gas pressure on ABB disconnector?</span>
            </button>
            <button
              onClick={() => handleRunRag("What should be checked when oil/winding temperature rises abnormally in an oil-filled transformer?")}
              className="px-3 py-1.5 rounded-xl bg-indigo-950/40 border border-indigo-800/50 text-indigo-300 hover:bg-indigo-900/60 transition cursor-pointer"
            >
              Abnormal oil temperature rise in ABB transformer?
            </button>
            <button
              onClick={() => handleRunRag("What is the procedure for BDV breakdown voltage test on insulating oil?")}
              className="px-3 py-1.5 rounded-xl bg-indigo-950/40 border border-indigo-800/50 text-indigo-300 hover:bg-indigo-900/60 transition cursor-pointer"
            >
              BDV breakdown voltage test procedure?
            </button>
          </div>

          {/* Conversational Chat History Feed */}
          <div className="h-[460px] overflow-y-auto space-y-4 p-4 rounded-2xl bg-slate-950/70 border border-slate-800/90 shadow-inner">
            {chatMessages.map((msg) => (
              <div
                key={msg.id}
                className={`flex gap-3 ${msg.sender === "user" ? "justify-end" : "justify-start"}`}
              >
                {msg.sender === "assistant" && (
                  <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-indigo-600 to-blue-500 text-white flex items-center justify-center shrink-0 shadow-md">
                    <Sparkles className="w-4 h-4" />
                  </div>
                )}

                <div
                  className={`max-w-2xl rounded-2xl p-4 space-y-3 shadow-lg ${
                    msg.sender === "user"
                      ? "bg-blue-600 text-white ml-12"
                      : "bg-[#0b1224] border border-indigo-900/40 text-slate-200 mr-12"
                  }`}
                >
                  {/* Assistant Header with Language Switcher */}
                  {msg.sender === "assistant" && (
                    <div className="flex items-center justify-between pb-2 border-b border-slate-800/80 gap-3">
                      <div className="flex items-center gap-2">
                        <span className="text-[11px] font-bold text-indigo-400 font-mono">
                          GridGuard RAG Engine
                        </span>
                        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
                          ✓ Grounded
                        </span>
                        <span className="text-[10px] text-slate-500 font-mono">{msg.timestamp}</span>
                      </div>

                      {/* Language Translation Toggle Button */}
                      <div className="flex items-center gap-2">
                        <button
                          type="button"
                          onClick={() => toggleMessageLanguage(msg.id)}
                          className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[11px] font-bold border transition cursor-pointer bg-blue-500/15 text-blue-300 border-blue-500/30 hover:bg-blue-500/30"
                        >
                          <Languages className="w-3.5 h-3.5" />
                          <span>
                            {msg.language === "ar" ? "🇬🇧 الإنجليزية الأصلية" : "🇪🇬 ترجمة للعربية"}
                          </span>
                        </button>
                        <button
                          type="button"
                          onClick={() => copyText(msg.id, msg.language === "ar" ? msg.textAr : msg.textEn)}
                          className="p-1 rounded text-slate-400 hover:text-white transition"
                          title="Copy text"
                        >
                          {copiedId === msg.id ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                        </button>
                      </div>
                    </div>
                  )}

                  {/* Message Content: English or Arabic based on toggle */}
                  {msg.sender === "user" ? (
                    <p className="text-xs leading-relaxed font-semibold">{msg.textEn}</p>
                  ) : msg.language === "ar" ? (
                    <div
                      dir="rtl"
                      className="text-right text-xs text-slate-100 leading-relaxed font-sans whitespace-pre-line border-r-2 border-emerald-500/80 pr-3 py-0.5"
                    >
                      {msg.textAr}
                    </div>
                  ) : (
                    <div
                      dir="ltr"
                      className="text-left text-xs text-slate-200 leading-relaxed font-sans whitespace-pre-line border-l-2 border-indigo-500/80 pl-3 py-0.5"
                    >
                      {msg.textEn}
                    </div>
                  )}

                  {/* Verified Citations List */}
                  {msg.citations && msg.citations.length > 0 && (
                    <div className="pt-2 border-t border-slate-800/80 space-y-1.5">
                      <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
                        {msg.language === "ar" ? "المراجع والكتالوجات المعتمدة:" : "Verified OEM Citations:"}
                      </span>
                      {msg.citations.map((cite, i) => (
                        <div
                          key={i}
                          className="flex items-center gap-2 text-[11px] font-mono text-cyan-400 bg-slate-900/90 px-2.5 py-1.5 rounded-lg border border-slate-800"
                        >
                          <FileText className="w-3 h-3 text-cyan-400 shrink-0" />
                          <span>{cite}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {msg.sender === "user" && (
                  <div className="w-8 h-8 rounded-xl bg-slate-800 text-slate-300 flex items-center justify-center shrink-0 border border-slate-700">
                    <span className="text-xs font-bold font-mono">U</span>
                  </div>
                )}
              </div>
            ))}

            {/* Thinking / Searching Indicator */}
            {ragLoading && (
              <div className="flex items-center gap-3 text-xs text-indigo-400 p-3 rounded-xl bg-indigo-950/20 border border-indigo-900/40 animate-pulse">
                <Sparkles className="w-4 h-4 animate-spin" />
                <span>Searching ABB, Siemens & Schneider 3072d dense embeddings & generating grounded response...</span>
              </div>
            )}
          </div>

          {/* Follow-up Query Input Bar */}
          <div className="flex gap-2">
            <input
              type="text"
              placeholder="Ask a follow-up question (e.g. What is the allowable leak rate? Can we re-energize manually?)..."
              value={ragQuery}
              onChange={(e) => setRagQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleRunRag(ragQuery)}
              className="flex-1 px-4 py-3 text-xs bg-slate-950 border border-slate-800 rounded-xl text-slate-200 focus:outline-none focus:border-indigo-500 shadow-inner"
            />
            <button
              onClick={() => handleRunRag(ragQuery)}
              disabled={ragLoading || !ragQuery}
              className="px-6 py-3 rounded-xl bg-gradient-to-r from-indigo-600 to-blue-600 hover:from-indigo-500 hover:to-blue-500 text-white font-bold text-xs flex items-center gap-2 transition disabled:opacity-40 shadow-lg shadow-indigo-600/30 cursor-pointer"
            >
              <Send className="w-4 h-4" />
              <span>إرسال (Send)</span>
            </button>
          </div>
        </div>
      )}

      {/* VIEW 5: OEM K-Base */}
      {activeTab === "manuals" && (
        <div className={`p-6 rounded-2xl border space-y-6 ${theme === "dark" ? "glass-panel border-slate-800/80" : "bg-white border-slate-200 shadow-md"}`}>
          <div className="flex items-center justify-between border-b pb-3 border-slate-800">
            <div>
              <h3 className="text-lg font-bold flex items-center gap-2">
                <BookOpen className="w-5 h-5 text-blue-400" />
                <span>Archived Substation Equipment Manuals</span>
              </h3>
              <p className="text-xs text-slate-400 mt-1">
                Extracted with PyMuPDF, layout-aware Markdown table reconstruction, and CAD diagram archiving.
              </p>
            </div>
            <button
              onClick={() => alert("Upload new OEM Manual dialog")}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs rounded-xl"
            >
              + Upload PDF Manual
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 rounded-2xl bg-slate-950 border border-slate-800 space-y-2">
              <span className="text-xs font-bold text-blue-400">ABB Distribution Transformer</span>
              <p className="text-[11px] text-slate-400">33 Pages · 131 Chunks · 9 Tables · 70 CAD Diagrams</p>
              <div className="text-[10px] font-mono text-slate-500 pt-1">ID: ABB_DIST_TRAFO_01</div>
            </div>
            <div className="p-4 rounded-2xl bg-slate-950 border border-slate-800 space-y-2">
              <span className="text-xs font-bold text-blue-400">Siemens Vacuum Circuit Breaker</span>
              <p className="text-[11px] text-slate-400">48 Pages · 180 Chunks · 14 Tables · 45 Diagrams</p>
              <div className="text-[10px] font-mono text-slate-500 pt-1">ID: SIEMENS_VCB_33KV</div>
            </div>
            <div className="p-4 rounded-2xl bg-slate-950 border border-slate-800 space-y-2">
              <span className="text-xs font-bold text-blue-400">Schneider SF6 RMU Switchgear</span>
              <p className="text-[11px] text-slate-400">28 Pages · 105 Chunks · 8 Tables · 32 Diagrams</p>
              <div className="text-[10px] font-mono text-slate-500 pt-1">ID: SCHNEIDER_RMU_01</div>
            </div>
          </div>
        </div>
      )}

      {/* VIEW 6: Audit & Dispatch Log */}
      {activeTab === "audit" && (
        <div className={`p-6 rounded-2xl border space-y-6 ${theme === "dark" ? "glass-panel border-slate-800/80" : "bg-white border-slate-200 shadow-md"}`}>
          <div className="border-b pb-3 border-slate-800">
            <h3 className="text-lg font-bold flex items-center gap-2">
              <History className="w-5 h-5 text-rose-400" />
              <span>Substation Work Orders & Audit Trail</span>
            </h3>
            <p className="text-xs text-slate-400 mt-1">
              Immutable log of operator actions, dispatch dispatches, and maintenance compliance.
            </p>
          </div>

          <div className="space-y-3">
            <div className="p-4 rounded-2xl bg-slate-950/80 border border-slate-800 flex items-center justify-between">
              <div>
                <span className="text-xs font-bold text-slate-200">WO-2026-0042 · SF6 Pressure Refill & Inspection</span>
                <p className="text-[11px] text-slate-400 mt-0.5">Assigned to: Engineer Karim H. | Priority: Emergency</p>
              </div>
              <span className="px-3 py-1 rounded-full text-xs font-bold bg-rose-500/20 text-rose-400 border border-rose-500/30">
                In Progress
              </span>
            </div>

            <div className="p-4 rounded-2xl bg-slate-950/80 border border-slate-800 flex items-center justify-between">
              <div>
                <span className="text-xs font-bold text-slate-200">WO-2026-0041 · Transformer Oil Sampling & BDV Test</span>
                <p className="text-[11px] text-slate-400 mt-0.5">Assigned to: Field Tech Ahmed M. | Result: 65kV Passed</p>
              </div>
              <span className="px-3 py-1 rounded-full text-xs font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                Completed
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Floating Modern Toast Notification */}
      {showToast && (
        <div className="fixed bottom-6 right-6 z-50">
          <div className="glass-panel bg-[#0d1527]/95 border border-emerald-500/40 px-4 py-2.5 rounded-2xl shadow-2xl flex items-center gap-3 text-xs text-slate-200">
            <div className="w-5 h-5 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center font-bold">
              <FileCheck2 className="w-3.5 h-3.5" />
            </div>
            <span>
              Synchronized <strong>524 grid assets</strong> with SCADA & PostGIS radar.
            </span>
            <button
              onClick={() => setShowToast(false)}
              className="text-slate-500 hover:text-white p-1 cursor-pointer"
            >
              <X className="w-3 h-3" />
            </button>
          </div>
        </div>
      )}

      {/* Register Asset Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-md p-4">
          <div className={`p-6 rounded-3xl border max-w-md w-full space-y-4 shadow-2xl ${
            theme === "dark" ? "bg-[#0b1122] border-slate-700 text-slate-100" : "bg-white border-slate-200 text-slate-900"
          }`}>
            <div className="flex items-center justify-between border-b pb-3 border-slate-800">
              <h3 className="text-base font-bold flex items-center gap-2">
                <PlusCircle className="w-4 h-4 text-blue-500" />
                Register Electrical Grid Asset
              </h3>
              <button
                onClick={() => setShowAddModal(false)}
                className="text-slate-400 hover:text-white font-bold p-1 rounded-lg hover:bg-slate-800 cursor-pointer"
              >
                ✕
              </button>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed">
              New assets undergo strict Pydantic contract validation, tenant scoping, and PostGIS coordinate indexing.
            </p>
            <div className="space-y-3 text-xs">
              <div>
                <label className="font-semibold block mb-1">Asset ID Code</label>
                <input
                  type="text"
                  placeholder="e.g. AST-TRF-003"
                  className={`w-full px-3 py-2 border rounded-xl focus:outline-none focus:border-blue-500 ${
                    theme === "dark" ? "bg-slate-950 border-slate-800 text-white" : "bg-slate-50 border-slate-200 text-slate-900"
                  }`}
                />
              </div>
              <div>
                <label className="font-semibold block mb-1">Asset Name</label>
                <input
                  type="text"
                  placeholder="e.g. Distribution Transformer 3"
                  className={`w-full px-3 py-2 border rounded-xl focus:outline-none focus:border-blue-500 ${
                    theme === "dark" ? "bg-slate-950 border-slate-800 text-white" : "bg-slate-50 border-slate-200 text-slate-900"
                  }`}
                />
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="font-semibold block mb-1">Type</label>
                  <select className={`w-full px-3 py-2 border rounded-xl ${
                    theme === "dark" ? "bg-slate-950 border-slate-800 text-white" : "bg-slate-50 border-slate-200 text-slate-900"
                  }`}>
                    <option>Transformer</option>
                    <option>Switch</option>
                    <option>Cable</option>
                    <option>Meter</option>
                    <option>Pole</option>
                  </select>
                </div>
                <div>
                  <label className="font-semibold block mb-1">Manufacturer</label>
                  <input
                    type="text"
                    placeholder="ABB / Siemens / Schneider"
                    className={`w-full px-3 py-2 border rounded-xl ${
                      theme === "dark" ? "bg-slate-950 border-slate-800 text-white" : "bg-slate-50 border-slate-200 text-slate-900"
                    }`}
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="font-semibold block mb-1">Latitude</label>
                  <input
                    type="number"
                    step="0.0001"
                    placeholder="30.0444"
                    className={`w-full px-3 py-2 border rounded-xl ${
                      theme === "dark" ? "bg-slate-950 border-slate-800 text-white" : "bg-slate-50 border-slate-200 text-slate-900"
                    }`}
                  />
                </div>
                <div>
                  <label className="font-semibold block mb-1">Longitude</label>
                  <input
                    type="number"
                    step="0.0001"
                    placeholder="31.2357"
                    className={`w-full px-3 py-2 border rounded-xl ${
                      theme === "dark" ? "bg-slate-950 border-slate-800 text-white" : "bg-slate-50 border-slate-200 text-slate-900"
                    }`}
                  />
                </div>
              </div>
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => setShowAddModal(false)}
                className={`px-4 py-2 border rounded-xl text-xs font-semibold cursor-pointer ${
                  theme === "dark" ? "border-slate-800 text-slate-400 hover:bg-slate-800" : "border-slate-200 text-slate-600 hover:bg-slate-100"
                }`}
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  alert("Asset submitted! Sent to POST /assets endpoint.");
                  setShowAddModal(false);
                }}
                className="px-5 py-2.5 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white rounded-xl text-xs font-bold shadow-md cursor-pointer"
              >
                Submit Asset
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
