import { useEffect, useMemo, useState } from "react";
import {
  Sprout, Leaf, ArrowRight, ArrowLeft, Globe2, ShieldCheck, CloudSun,
  Thermometer, Droplets, Sun, MapPin, CheckCircle2, Info, Wheat,
  Droplet, Mountain, TrendingUp, Flower2, RotateCcw, ExternalLink,
  AlertTriangle, CalendarDays, Database, ClipboardList
} from "lucide-react";
import frontendData from "./data/frontend_data.json";

const translations = {
  English: {
    home: "Home", about: "How it works", getStarted: "Get Started",
    eyebrow: "CLIMATE-SMART AGRICULTURE", hero1: "Smarter Crop Rotations.",
    hero2: "Stronger Farms.", hero3: "A More Resilient India.",
    heroText: "Explore climate observations from NASA POWER alongside locally relevant crop-rotation research data.",
    explore: "Explore CropWise", learn: "Discover how it works", nasa: "NASA POWER climate observations",
    featureTitle: "Climate insights for more informed exploration", featureText: "Explore environmental conditions and candidate crop sequences with clear evidence and limitations.",
    climate: "Climate Insights", climateText: "Review seasonal rainfall, temperature and dry-spell indicators.",
    rotation: "Crop Rotation", rotationText: "Compare example crop sequences without treating them as recommendations.",
    resilience: "Transparent Evidence", resilienceText: "See missing information, evidence status and expert-review flags.",
    location: "Select your pilot district", locationDesc: "Choose a district included in the current data export.",
    farm: "Your farm profile", farmDesc: "Add context to help interpret the information. These inputs do not generate a validated suitability score.",
    dashboard: "Seasonal climate dashboard", dashboardDesc: "Review the supplied seasonal climate indicators for your selected district.",
    compare: "Explore crop rotations", compareDesc: "Review the example crop sequences supplied for your selected district.",
    continue: "Continue", back: "Back", currentCrop: "Current crop", water: "Water availability",
    soil: "Soil type", farmSize: "Farm size (optional)", priority: "Your main priority",
    viewClimate: "View climate dashboard", compareOptions: "Explore rotations", editProfile: "Edit farm profile",
    pending: "Not available", factors: "What should be checked?", waterFactor: "Water-use information",
    soilFactor: "Soil considerations", climateFactor: "Climate observations", cropFactor: "Crop and season suitability",
    priorityFactor: "Farmer priorities", disclaimer: "Important: These sequences are example comparisons, not farming recommendations. Partial scores are illustrative team estimates, not validated agronomic suitability rankings. Consult local agricultural university, ICAR or KVK guidance and an agricultural expert before making farm decisions.",
    footer: "Climate-informed agricultural decision support.", district: "District", state: "State", season: "Season",
    year: "Season year", complete: "Season end date reached (not a guarantee of daily completeness)", incomplete: "Not marked complete",
    climateOnly: "Climate observations describe environmental conditions. They do not establish crop suitability or predict yield.",
    evidence: "Crop evidence", noEvidence: "No crop-specific evidence URLs were supplied in this export.",
    confidence: "Confidence", expert: "Expert review required", missing: "Information still needed", sources: "Data sources",
    score: "Partial illustrative comparison score", noScore: "Not available",
    baseline: "Baseline metadata", scopeNotice: "The four pilot regions in this dataset are Punjab, Bihar, Maharashtra and Tamil Nadu.",
    dataNotice: "Live charts are not shown because this export contains seasonal summary indicators, not a monthly time series.",
    evidenceStatus: "Evidence status", decisionStatus: "Decision status", interpretation: "Interpretation note",
        profileNote: "Farm profile details are user-provided context and are not used to calculate a suitability score in this prototype.",
    stepLocation: "Location", stepProfile: "Farm profile", stepClimate: "Climate", stepCompare: "Compare",
    step1: "STEP 1 - LOCATION", step2: "STEP 2 - FARM DETAILS", step3: "STEP 3 - ENVIRONMENTAL DATA", step4: "STEP 4 - ROTATION EXPLORER",
    approach: "THE CROPWISE APPROACH", startExploring: "START EXPLORING", climateInformed: "Climate-informed farming",
    betterInsights: "Better insights begin with one step.", selectPilot: "Select a pilot district and explore the CropWise experience.",
    farmInformation: "Farm information", requiredMarked: "Required details are marked with an asterisk.",
    exampleCrop: "e.g. Rice, wheat, maize", selectAvailability: "Select availability", selectIfKnown: "Select if known",
    rainfed: "Rainfed", limitedIrrigation: "Limited irrigation", reliableIrrigation: "Reliable irrigation", seasonalAvailability: "Seasonal availability", notSure: "Not sure",
    alluvial: "Alluvial", black: "Black", red: "Red", laterite: "Laterite", loamy: "Loamy", sandy: "Sandy", otherNotSure: "Other / Not sure",
    waterEfficiency: "Water efficiency", climateResilience: "Climate resilience", soilHealth: "Soil health", cropDiversification: "Crop diversification", incomeStability: "Income stability",
    rotationOptions: "Rotation options", exampleComparisons: "Example comparisons from the supplied dataset; not recommendations.", cropSequence: "Crop sequence",
    pleaseNote: "Please note", currentCropLabel: "Current crop", verifyWater: "Verify crop water requirements and local water availability.",
    verifySoil: "Verify soil type, pH and crop-specific soil requirements.", interpretClimate: "Interpret observed seasonal temperature and rainfall indicators.",
    verifyCalendar: "Verify local crop calendars and agronomic suitability.", farmerPriority: "Farmer priority", noFlags: "No climate flags were supplied for this season.",
    historicalNormal: "Historical normal", baselineSupplied: "Baseline metadata supplied", periodUnconfirmed: "Baseline years: 2016 to 2025 inclusive; baseline completeness handling still requires confirmation.",
    detailedExplanation: "Detailed explanation", decisionStatusLabel: "Decision status", sourcesListed: "Sources listed", evidenceSource: "Evidence source", evidenceItem: "Evidence item", notSupplied: "not supplied", farmSizeExample: "e.g. 2 acres", baselineSentence: "Baseline metadata supplied", periodSentence: "Baseline years: 2016 to 2025 inclusive; baseline completeness handling still requires confirmation.", climateInformedTitle: "TRANSPARENT DECISION SUPPORT",
    options: "OPTIONS"
  }
};

const bilingual = (language, english, hindi) => language === "Hindi" ? hindi : english;
const regionEntries = Object.entries(frontendData.regions);
const seasonOrder = ["kharif", "rabi", "summer"];
const pretty = (value = "") => String(value).replaceAll("_", " ").replace(/\b\w/g, (c) => c.toUpperCase());
const displayNumber = (value, unit = "") => value === null || value === undefined ? "Not available" : `${Number.isInteger(value) ? value : Number(value).toFixed(2)}${unit ? ` ${unit}` : ""}`;
const cropName = (crop) => pretty(crop);

function Field({label,children}) { return <div><label className="mb-2 block text-sm font-semibold text-gray-700">{label}</label>{children}</div>; }

function App() {
  const [page, setPage] = useState("home");
  const [language, setLanguage] = useState("English");
  const [regionId, setRegionId] = useState(regionEntries[0]?.[0] || "");
  const [season, setSeason] = useState("kharif");
  const t = translations[language];
  const [profile, setProfile] = useState({ currentCrop: "", water: "", soil: "", farmSize: "", priority: "Water efficiency" });
  const district = frontendData.regions[regionId];
  const regionOptions = useMemo(() => regionEntries.map(([id, item]) => ({ id, ...item })), []);
    // Live backend data
  const [climateSummary, setClimateSummary] = useState(null);
  const [climateLoading, setClimateLoading] = useState(false);
  const [climateError, setClimateError] = useState("");

  const [liveRotations, setLiveRotations] = useState(null);
  const [rotationLoading, setRotationLoading] = useState(false);
  const [rotationError, setRotationError] = useState("");

  // Fetch NASA POWER climate summary for the selected district and season
  useEffect(() => {
    const controller = new AbortController();

    async function loadClimate() {
      setClimateLoading(true);
      setClimateError("");
      setClimateSummary(null);

      try {
        const response = await fetch(
          `http://127.0.0.1:8000/api/climate/summary?region=${encodeURIComponent(regionId)}&season=${encodeURIComponent(season)}`,
          { signal: controller.signal }
        );

        if (!response.ok) {
          const error = await response.json();
          throw new Error(error.detail || "Could not load climate data.");
        }

        const data = await response.json();
        setClimateSummary(data);
      } catch (error) {
        if (error.name !== "AbortError") {
          setClimateError(error.message);
        }
      } finally {
        if (!controller.signal.aborted) {
          setClimateLoading(false);
        }
      }
    }

    loadClimate();
    return () => controller.abort();
  }, [regionId, season]);

  // Fetch the three rotation comparisons from the backend
  useEffect(() => {
    if (page !== "comparison") return;

    let cancelled = false;

    async function loadRotations() {
      setRotationLoading(true);
      setRotationError("");

      try {
        const results = await Promise.all(
          (district.rotations || []).map(async (option) => {
            const response = await fetch(
              "http://127.0.0.1:8000/api/rotation/compare",
              {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                  region_id: regionId,
                  rotation_id: option.id
                })
              }
            );

            if (!response.ok) {
              const error = await response.json();
              throw new Error(error.detail || `Could not load ${option.id}.`);
            }

            const data = await response.json();
            const result = data.result || {};

            return {
              ...option,
              id: data.rotation_id,
              type: data.rotation_type,
              crops: data.crops,
              label: data.label,
              evidence_status: data.decision_status,
              decision_status: data.decision_status,
              overall: result.overall,
              scores: result.scores || {},
              score_coverage: {
                available_count: Object.values(result.scores || {}).filter(value => value != null).length,
                total_count: Object.keys(result.scores || {}).length
              },
              score_note: data.score_note,
              confidence: result.confidence,
              needs_expert_review: result.needs_expert_review,
              missing_info: Array.isArray(result.missing_info) ? result.missing_info.map(item => typeof item === "string" ? item : item?.message || JSON.stringify(item)) : [],
              sources: result.sources || [],
              crop_evidence: (data.crop_evidence || []).map((item) => ({
                crop_id: item.crop_id,
                crop_name: item.name_en,
                source_url: item.source_url,
                ratings: item.evidence || {}
              }))
            };
          })
        );

        if (!cancelled) {
          setLiveRotations(results);
        }
      } catch (error) {
        if (!cancelled) {
          setLiveRotations(null);
          setRotationError(error.message);
        }
      } finally {
        if (!cancelled) {
          setRotationLoading(false);
        }
      }
    }

    loadRotations();

    return () => {
      cancelled = true;
    };
  }, [page, regionId, district]);
  const updateProfile = (field, value) => setProfile((old) => ({ ...old, [field]: value }));
  const goBack = () => setPage(({ region: "home", profile: "region", dashboard: "profile", comparison: "dashboard" })[page] || "home");

  const primaryButton = "inline-flex items-center justify-center gap-2 rounded-xl bg-emerald-700 px-6 py-3.5 text-sm font-semibold text-white shadow-sm transition hover:-translate-y-0.5 hover:bg-emerald-800 hover:shadow-md disabled:cursor-not-allowed disabled:opacity-40";
  const secondaryButton = "inline-flex items-center justify-center gap-2 rounded-xl border border-gray-200 bg-white px-6 py-3.5 text-sm font-semibold text-gray-700 transition hover:border-emerald-300 hover:bg-emerald-50";
  const panel = "rounded-2xl border border-gray-100 bg-white shadow-sm";

  function Header() {
    return <header className="sticky top-0 z-50 border-b border-gray-100 bg-white/95 backdrop-blur"><div className="mx-auto flex max-w-7xl items-center justify-between px-5 py-4 lg:px-8">
      <button onClick={() => setPage("home")} className="flex items-center gap-2.5"><span className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-700 text-white"><Sprout size={24}/></span><span className="text-xl font-extrabold tracking-tight text-gray-900">CropWise <span className="text-emerald-700">AI</span></span></button>
      <nav className="hidden items-center gap-8 md:flex"><button onClick={() => setPage("home")} className="text-sm font-medium text-gray-600 hover:text-emerald-700">{t.home}</button><button onClick={() => document.getElementById("features")?.scrollIntoView({behavior:"smooth"})} className="text-sm font-medium text-gray-600 hover:text-emerald-700">{t.about}</button></nav>
      <div className="flex items-center gap-3"><button onClick={() => setPage("region")} className="hidden rounded-xl bg-emerald-700 px-5 py-2.5 text-sm font-semibold text-white sm:block">{t.getStarted}</button></div>
    </div></header>;
  }
  function Footer() { return <footer className="mt-20 border-t border-gray-100 bg-white"><div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-4 px-5 py-8 text-center md:flex-row md:text-left lg:px-8"><div className="flex items-center gap-2"><Sprout className="text-emerald-700" size={22}/><span className="font-bold text-gray-800">CropWise AI</span></div><p className="text-sm text-gray-400">Copyright 2026 CropWise AI - {t.footer}</p></div></footer>; }
  function PageHeading({step,title,description}) { return <div className="mx-auto mb-10 max-w-3xl text-center"><div className="mb-3 inline-flex items-center gap-2 rounded-full bg-emerald-50 px-4 py-2 text-xs font-bold uppercase tracking-widest text-emerald-800"><Leaf size={14}/>{step}</div><h1 className="text-3xl font-extrabold tracking-tight text-gray-900 md:text-4xl">{title}</h1><p className="mx-auto mt-3 max-w-2xl text-base leading-7 text-gray-500">{description}</p></div>; }
  function ProgressBar() { const steps=[["region",t.stepLocation],["profile",t.stepProfile],["dashboard",t.stepClimate],["comparison",t.stepCompare]]; const active=steps.findIndex(([key])=>key===page); return <div className="mx-auto mb-10 flex max-w-3xl items-center justify-between">{steps.map(([key,label],i)=><div key={key} className="flex flex-1 items-center"><div className="flex flex-col items-center gap-2"><div className={`flex h-9 w-9 items-center justify-center rounded-full text-sm font-bold ${i<=active?"bg-emerald-700 text-white":"bg-gray-100 text-gray-400"}`}>{i<active?<CheckCircle2 size={18}/>:i+1}</div><span className={`hidden text-xs font-semibold sm:block ${i<=active?"text-emerald-800":"text-gray-400"}`}>{label}</span></div>{i!==steps.length-1&&<div className={`mx-2 mb-5 h-0.5 flex-1 ${i<active?"bg-emerald-600":"bg-gray-200"}`}/>}</div>)}</div>; }
  const inputClass="w-full rounded-xl border border-gray-200 bg-white px-4 py-3.5 text-sm text-gray-800 outline-none transition placeholder:text-gray-400 focus:border-emerald-600 focus:ring-4 focus:ring-emerald-50";

  function HomePage() { return <>
    <section className="relative overflow-hidden bg-[#f3f8f2]"><div className="pointer-events-none absolute -left-32 -top-32 h-96 w-96 rounded-full bg-emerald-100/70 blur-3xl"/><div className="pointer-events-none absolute -bottom-40 right-0 h-96 w-96 rounded-full bg-lime-100/70 blur-3xl"/><div className="relative mx-auto grid max-w-7xl items-center gap-12 px-5 py-16 lg:grid-cols-2 lg:px-8 lg:py-24">
      <div className="relative z-10"><div className="mb-6 inline-flex items-center gap-2 rounded-full border border-emerald-100 bg-white px-4 py-2 text-xs font-bold tracking-wide text-emerald-800 shadow-sm"><span className="h-2 w-2 rounded-full bg-emerald-500"/>{t.eyebrow}</div><h1 className="max-w-2xl text-4xl font-extrabold leading-[1.13] tracking-tight text-gray-900 sm:text-5xl lg:text-[58px]">{t.hero1}<span className="block text-emerald-700">{t.hero2}</span><span className="block">{t.hero3}</span></h1><p className="mt-7 max-w-xl text-base leading-8 text-gray-600 md:text-lg">{t.heroText}</p><div className="mt-9 flex flex-wrap gap-3"><button className={primaryButton} onClick={()=>setPage("region")}>{t.explore}<ArrowRight size={18}/></button><button className={secondaryButton} onClick={()=>document.getElementById("features")?.scrollIntoView({behavior:"smooth"})}>{t.learn}</button></div><div className="mt-9 flex items-center gap-3 text-sm text-gray-500"><span className="flex h-9 w-9 items-center justify-center rounded-full bg-white text-emerald-700 shadow-sm"><Globe2 size={18}/></span>{t.nasa}</div></div>
      <div className="relative mx-auto w-full max-w-[570px]"><div className="relative overflow-hidden rounded-[2rem] border-8 border-white bg-[#dcefd8] shadow-2xl shadow-emerald-900/10"><svg viewBox="0 0 640 510" className="block h-auto w-full" role="img" aria-label="Illustrated green agricultural fields, hills and sunshine"><defs><linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#b9e2e9"/><stop offset="100%" stopColor="#e8f3d9"/></linearGradient><linearGradient id="field" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#8bbd66"/><stop offset="100%" stopColor="#386e3d"/></linearGradient></defs><rect width="640" height="510" fill="url(#sky)"/><circle cx="500" cy="105" r="52" fill="#f8d978"/><path d="M0 270 Q120 160 250 250 Q390 130 520 230 Q590 180 640 220 L640 510 L0 510Z" fill="#9dbf86"/><path d="M0 310 Q130 220 250 290 Q400 190 640 290 L640 510 L0 510Z" fill="#6d9d61"/><path d="M0 365 Q160 300 320 365 Q480 305 640 355 L640 510 L0 510Z" fill="url(#field)"/><path d="M0 510 Q130 385 310 380 Q470 385 640 510Z" fill="#315f39"/>{Array.from({length:9},(_,i)=><path key={i} d={`M${i*85-80} 510 Q${i*85+110} 410 ${i*85+210} 375`} fill="none" stroke="#b2ce76" strokeWidth="5" opacity=".7"/>)}<g fill="#fff" opacity=".7"><ellipse cx="120" cy="110" rx="44" ry="14"/><ellipse cx="145" cy="100" rx="28" ry="18"/><ellipse cx="170" cy="112" rx="34" ry="13"/></g></svg><div className="absolute bottom-5 left-5 right-5 rounded-2xl border border-white/70 bg-white/90 p-4 shadow-lg backdrop-blur"><div className="flex items-center justify-between"><div><p className="text-xs font-semibold uppercase tracking-wider text-emerald-700">CropWise AI</p><p className="mt-1 text-sm font-bold text-gray-900">{t.climateInformed}</p></div><span className="flex h-11 w-11 items-center justify-center rounded-xl bg-emerald-100 text-emerald-800"><Sprout size={25}/></span></div></div></div></div>
    </div></section>
    <section id="features" className="mx-auto max-w-7xl px-5 py-20 lg:px-8"><div className="mx-auto mb-12 max-w-2xl text-center"><p className="text-xs font-bold uppercase tracking-[.2em] text-emerald-700">{t.approach}</p><h2 className="mt-3 text-3xl font-extrabold tracking-tight text-gray-900 md:text-4xl">{t.featureTitle}</h2><p className="mt-4 leading-7 text-gray-500">{t.featureText}</p></div><div className="grid gap-5 md:grid-cols-3">{[{icon:CloudSun,title:t.climate,text:t.climateText,color:"bg-blue-50 text-blue-700"},{icon:Wheat,title:t.rotation,text:t.rotationText,color:"bg-emerald-50 text-emerald-700"},{icon:ShieldCheck,title:t.resilience,text:t.resilienceText,color:"bg-amber-50 text-amber-700"}].map((f,i)=><div key={i} className={`${panel} p-7 transition hover:-translate-y-1 hover:shadow-lg`}><span className={`flex h-14 w-14 items-center justify-center rounded-2xl ${f.color}`}><f.icon size={27}/></span><h3 className="mt-6 text-xl font-bold text-gray-900">{f.title}</h3><p className="mt-3 text-sm leading-7 text-gray-500">{f.text}</p></div>)}</div></section>
    <section className="mx-5 mb-10 overflow-hidden rounded-3xl bg-emerald-800 md:mx-auto md:max-w-7xl"><div className="flex flex-col items-center justify-between gap-6 px-7 py-12 text-center md:flex-row md:px-12 md:text-left"><div><p className="text-xs font-bold uppercase tracking-widest text-emerald-200">{t.startExploring}</p><h2 className="mt-3 text-2xl font-bold text-white md:text-3xl">{t.betterInsights}</h2><p className="mt-3 text-sm text-emerald-100">{t.selectPilot}</p></div><button onClick={()=>setPage("region")} className="inline-flex shrink-0 items-center gap-2 rounded-xl bg-white px-6 py-3.5 text-sm font-bold text-emerald-800">{t.getStarted}<ArrowRight size={18}/></button></div></section>
  </>; }

  function RegionPage() { return <div className="mx-auto max-w-7xl px-5 py-12 lg:px-8">{ProgressBar()}<PageHeading step={t.step1} title={t.location} description={t.locationDesc}/><div className="mx-auto grid max-w-5xl gap-5 sm:grid-cols-2">{regionOptions.map((item)=>{const selected=regionId===item.id;return <button key={item.id} onClick={()=>setRegionId(item.id)} className={`relative flex min-h-40 items-center gap-5 rounded-2xl border bg-white p-6 text-left transition hover:-translate-y-1 hover:shadow-lg ${selected?"border-emerald-600 bg-emerald-50 ring-2 ring-emerald-100":"border-gray-200 hover:border-emerald-300"}`}><span className="flex h-16 w-16 shrink-0 items-center justify-center rounded-2xl bg-emerald-50 text-emerald-700"><Sprout size={28}/></span><span className="flex-1"><span className="block text-xs font-bold uppercase tracking-widest text-emerald-700">{item.state}</span><span className="mt-1 block text-xl font-bold text-gray-900">{item.district}</span><span className="mt-1 block text-sm text-gray-500">{item.state}, India - Pilot data</span></span>{selected&&<CheckCircle2 className="absolute right-5 top-5 text-emerald-700" size={22}/>}</button>;})}</div><div className="mx-auto mt-8 max-w-5xl rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm leading-6 text-amber-900"><AlertTriangle className="mr-2 inline" size={17}/>{t.scopeNotice}</div><div className="mx-auto mt-9 flex max-w-5xl justify-between"><button onClick={goBack} className={secondaryButton}><ArrowLeft size={17}/>{t.back}</button><button onClick={()=>setPage("profile")} className={primaryButton}>{t.continue}<ArrowRight size={17}/></button></div></div>; }

  function ProfilePage() { return <div className="mx-auto max-w-7xl px-5 py-12 lg:px-8">{ProgressBar()}<PageHeading step={t.step2} title={t.farm} description={t.farmDesc}/><div className="mx-auto grid max-w-5xl gap-7 lg:grid-cols-[.85fr_1.15fr]"><div className="relative overflow-hidden rounded-3xl bg-emerald-800 p-8 text-white"><div className="relative"><span className="flex h-14 w-14 items-center justify-center rounded-2xl bg-white/15"><Sprout size={30}/></span><p className="mt-7 text-xs font-bold uppercase tracking-widest text-emerald-200">{t.district}</p><h2 className="mt-2 text-3xl font-extrabold">{district.district}</h2><p className="mt-1 text-emerald-100">{district.state}, India</p><div className="mt-8 space-y-4 border-t border-white/15 pt-6 text-sm text-emerald-50"><div className="flex items-center gap-3"><MapPin size={18}/>{district.district}, {district.state}</div><div className="flex items-center gap-3"><Database size={18}/>NASA POWER data export</div></div></div></div><div className={`${panel} p-6 md:p-8`}><h3 className="text-xl font-bold text-gray-900">{t.farmInformation}</h3><p className="mt-1 text-sm text-gray-500">{t.requiredMarked}</p><div className="mt-6 grid gap-5 sm:grid-cols-2"><div className="sm:col-span-2"><Field label={`${t.currentCrop} *`}><input className={inputClass} value={profile.currentCrop} onChange={e=>updateProfile("currentCrop",e.target.value)} placeholder={t.exampleCrop}/></Field></div><Field label={`${t.water} *`}><select className={inputClass} value={profile.water} onChange={e=>updateProfile("water",e.target.value)}><option value="">{t.selectAvailability}</option><option value="Rainfed">{t.rainfed}</option><option value="Limited irrigation">{t.limitedIrrigation}</option><option value="Reliable irrigation">{t.reliableIrrigation}</option><option value="Seasonal availability">{t.seasonalAvailability}</option><option value="Not sure">{t.notSure}</option></select></Field>{Field({label: t.soil, children: <> <select className={inputClass} value={profile.soil} onChange={e=>updateProfile("soil",e.target.value)}><option value="">{t.selectIfKnown}</option><option value="Alluvial">{t.alluvial}</option><option value="Black">{t.black}</option><option value="Red">{t.red}</option><option value="Laterite">{t.laterite}</option><option value="Loamy">{t.loamy}</option><option value="Sandy">{t.sandy}</option><option value="Other / Not sure">{t.otherNotSure}</option></select> </>})}{Field({label: t.farmSize, children: <> <input className={inputClass} value={profile.farmSize} onChange={e=>updateProfile("farmSize",e.target.value)} placeholder={t.farmSizeExample}/> </>})}{Field({label: t.priority, children: <> <select className={inputClass} value={profile.priority} onChange={e=>updateProfile("priority",e.target.value)}><option value="Water efficiency">{t.waterEfficiency}</option><option value="Climate resilience">{t.climateResilience}</option><option value="Soil health">{t.soilHealth}</option><option value="Crop diversification">{t.cropDiversification}</option><option value="Income stability">{t.incomeStability}</option></select> </>})}</div><p className="mt-5 rounded-xl bg-blue-50 p-3 text-xs leading-5 text-blue-800">{t.profileNote}</p><div className="mt-7 flex flex-wrap justify-between gap-3 border-t border-gray-100 pt-6"><button onClick={goBack} className={secondaryButton}><ArrowLeft size={17}/>{t.back}</button><button disabled={!profile.currentCrop.trim()||!profile.water} onClick={()=>setPage("dashboard")} className={primaryButton}>{t.viewClimate}<ArrowRight size={17}/></button></div></div></div></div>; }

  function DashboardPage() {
        const seasonData = district.season_risk_indicators?.[season];

    const flags = climateSummary
      ? [
          {
            indicator: "rainfall_below_baseline",
            observed_value: climateSummary.rain_pct,
            unit: "%",
            message: `Compared with baseline (${climateSummary.baseline_years || "2016-2025"})`
          },
          {
            indicator: "temperature_above_baseline",
            observed_value: climateSummary.temp_delta,
            unit: "°C",
            message: "Mean temperature difference from historical baseline"
          },
          {
            indicator: "dry_spell_observed",
            observed_value: climateSummary.dry_spell_days,
            unit: "days",
            message: `Longest consecutive period below ${climateSummary.thresholds?.dry_day_rain_below ?? 1} mm/day`
          },
          {
            indicator: "heat_days_above_normal",
            observed_value: climateSummary.heat_days,
            historical_normal: climateSummary.heat_days_normal,
            unit: "days",
            message: `Days above the ${climateSummary.thresholds?.heat_t_max ?? 40}°C team threshold`
          }
        ]
      : seasonData?.climate_flags || [];

    const quality = climateSummary
      ? {
          period_start: climateSummary.data_range?.period_start || climateSummary.period?.split("/")[0],
          period_end: climateSummary.data_range?.period_end || climateSummary.period?.split("/")[1],
          missing_pct: {
            rain: climateSummary.details?.missing_pct_by_parameter?.rain_mm ?? climateSummary.missing_pct,
            t_mean: climateSummary.details?.missing_pct_by_parameter?.t_mean,
            t_max: climateSummary.details?.missing_pct_by_parameter?.t_max
          }
        }
      : district.season_data_quality?.[season];
    const biharRabi = district.id === "bihar_samastipur" && season === "rabi" && seasonData?.season_year === 2025;
    const indicatorMeta = {
      rainfall_below_baseline: { title: bilingual(language, "Seasonal rainfall deviation", "ÃƒÂ Ã‚Â¤Ã‚Â®ÃƒÂ Ã‚Â¥Ã…â€™ÃƒÂ Ã‚Â¤Ã‚Â¸ÃƒÂ Ã‚Â¤Ã‚Â®ÃƒÂ Ã‚Â¥Ã¢â€šÂ¬ ÃƒÂ Ã‚Â¤Ã‚ÂµÃƒÂ Ã‚Â¤Ã‚Â°ÃƒÂ Ã‚Â¥Ã‚ÂÃƒÂ Ã‚Â¤Ã‚Â·ÃƒÂ Ã‚Â¤Ã‚Â¾ ÃƒÂ Ã‚Â¤Ã‚Â®ÃƒÂ Ã‚Â¥Ã¢â‚¬Â¡ÃƒÂ Ã‚Â¤Ã¢â‚¬Å¡ ÃƒÂ Ã‚Â¤Ã¢â‚¬Â¦ÃƒÂ Ã‚Â¤Ã¢â‚¬Å¡ÃƒÂ Ã‚Â¤Ã‚Â¤ÃƒÂ Ã‚Â¤Ã‚Â°"), icon: Droplets, color: "text-blue-700", bg: "bg-blue-50" },
      temperature_above_baseline: { title: bilingual(language, "Temperature anomaly", "ÃƒÂ Ã‚Â¤Ã‚Â¤ÃƒÂ Ã‚Â¤Ã‚Â¾ÃƒÂ Ã‚Â¤Ã‚ÂªÃƒÂ Ã‚Â¤Ã‚Â®ÃƒÂ Ã‚Â¤Ã‚Â¾ÃƒÂ Ã‚Â¤Ã‚Â¨ ÃƒÂ Ã‚Â¤Ã‚Â®ÃƒÂ Ã‚Â¥Ã¢â‚¬Â¡ÃƒÂ Ã‚Â¤Ã¢â‚¬Å¡ ÃƒÂ Ã‚Â¤Ã¢â‚¬Â¦ÃƒÂ Ã‚Â¤Ã‚Â¸ÃƒÂ Ã‚Â¤Ã‚Â¾ÃƒÂ Ã‚Â¤Ã‚Â®ÃƒÂ Ã‚Â¤Ã‚Â¾ÃƒÂ Ã‚Â¤Ã‚Â¨ÃƒÂ Ã‚Â¥Ã‚ÂÃƒÂ Ã‚Â¤Ã‚Â¯ÃƒÂ Ã‚Â¤Ã‚Â¤ÃƒÂ Ã‚Â¤Ã‚Â¾"), icon: Thermometer, color: "text-orange-700", bg: "bg-orange-50" },
      dry_spell_observed: { title: bilingual(language, "Longest consecutive dry spell (<1 mm/day)", "ÃƒÂ Ã‚Â¤Ã‚Â¸ÃƒÂ Ã‚Â¤Ã‚Â¬ÃƒÂ Ã‚Â¤Ã‚Â¸ÃƒÂ Ã‚Â¥Ã¢â‚¬Â¡ ÃƒÂ Ã‚Â¤Ã‚Â²ÃƒÂ Ã‚Â¤Ã¢â‚¬Å¡ÃƒÂ Ã‚Â¤Ã‚Â¬ÃƒÂ Ã‚Â¥Ã¢â€šÂ¬ ÃƒÂ Ã‚Â¤Ã‚Â²ÃƒÂ Ã‚Â¤Ã¢â‚¬â€ÃƒÂ Ã‚Â¤Ã‚Â¾ÃƒÂ Ã‚Â¤Ã‚Â¤ÃƒÂ Ã‚Â¤Ã‚Â¾ÃƒÂ Ã‚Â¤Ã‚Â° ÃƒÂ Ã‚Â¤Ã‚Â¶ÃƒÂ Ã‚Â¥Ã‚ÂÃƒÂ Ã‚Â¤Ã‚Â·ÃƒÂ Ã‚Â¥Ã‚ÂÃƒÂ Ã‚Â¤Ã¢â‚¬Â¢ ÃƒÂ Ã‚Â¤Ã¢â‚¬Â¦ÃƒÂ Ã‚Â¤Ã‚ÂµÃƒÂ Ã‚Â¤Ã‚Â§ÃƒÂ Ã‚Â¤Ã‚Â¿ (<1 ÃƒÂ Ã‚Â¤Ã‚Â®ÃƒÂ Ã‚Â¤Ã‚Â¿ÃƒÂ Ã‚Â¤Ã‚Â®ÃƒÂ Ã‚Â¥Ã¢â€šÂ¬/ÃƒÂ Ã‚Â¤Ã‚Â¦ÃƒÂ Ã‚Â¤Ã‚Â¿ÃƒÂ Ã‚Â¤Ã‚Â¨)"), icon: CloudSun, color: "text-amber-700", bg: "bg-amber-50" },
      heat_days_above_normal: { title: bilingual(language, "Heat days", "ÃƒÂ Ã‚Â¤Ã¢â‚¬Â¦ÃƒÂ Ã‚Â¤Ã‚Â§ÃƒÂ Ã‚Â¤Ã‚Â¿ÃƒÂ Ã‚Â¤Ã¢â‚¬Â¢ ÃƒÂ Ã‚Â¤Ã¢â‚¬â€ÃƒÂ Ã‚Â¤Ã‚Â°ÃƒÂ Ã‚Â¥Ã‚ÂÃƒÂ Ã‚Â¤Ã‚Â®ÃƒÂ Ã‚Â¥Ã¢â€šÂ¬ ÃƒÂ Ã‚Â¤Ã‚ÂµÃƒÂ Ã‚Â¤Ã‚Â¾ÃƒÂ Ã‚Â¤Ã‚Â²ÃƒÂ Ã‚Â¥Ã¢â‚¬Â¡ ÃƒÂ Ã‚Â¤Ã‚Â¦ÃƒÂ Ã‚Â¤Ã‚Â¿ÃƒÂ Ã‚Â¤Ã‚Â¨"), icon: Sun, color: "text-rose-700", bg: "bg-rose-50" }
    };
    return <div className="mx-auto max-w-7xl px-5 py-12 lg:px-8">{ProgressBar()}<PageHeading step={t.step3} title={t.dashboard} description={`${t.dashboardDesc} - ${district.district}, ${district.state}`}/>
      <div className="mb-7 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">{[{label:t.district,value:district.district,icon:MapPin},{label:t.state,value:district.state,icon:Globe2},{label:t.currentCrop,value:profile.currentCrop,icon:Wheat}].map((item)=><div key={item.label} className={`${panel} p-5`}><div className="flex items-center justify-between"><p className="text-xs font-semibold uppercase tracking-wide text-gray-400">{item.label}</p><item.icon size={19} className="text-emerald-700"/></div><p className="mt-3 text-lg font-bold text-gray-900">{item.value}</p></div>)}</div>
      <div className="mb-6 flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-emerald-100 bg-emerald-50 p-5"><div><p className="text-xs font-bold uppercase tracking-wide text-emerald-800">{t.season}</p><p className="mt-1 text-lg font-bold text-gray-900">{pretty(season)} {seasonData?.season_year ? `- ${seasonData.season_year}` : ""}</p></div><select aria-label="Select season" className={`${inputClass} max-w-xs`} value={season} onChange={e=>setSeason(e.target.value)}>{seasonOrder.map(s=><option key={s} value={s}>{pretty(s)}</option>)}</select></div>
      <div className="mb-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">{flags.map((flag,i)=>{const meta=indicatorMeta[flag.indicator]||{title:pretty(flag.indicator),icon:Info,color:"text-gray-700",bg:"bg-gray-50"};const Icon=meta.icon;return <div key={`${flag.indicator}-${i}`} className={`${panel} p-5`}><div className="flex items-center justify-between"><span className={`flex h-10 w-10 items-center justify-center rounded-xl ${meta.bg} ${meta.color}`}><Icon size={21}/></span><span className="text-xs text-gray-400">{flag.unit||""}</span></div><p className="mt-4 text-xs font-semibold uppercase tracking-wide text-gray-500">{meta.title}</p><p className="mt-1 text-2xl font-extrabold text-gray-900">{displayNumber(flag.observed_value,flag.unit)}</p><p className="mt-2 text-xs leading-5 text-gray-500">{flag.message}</p>{flag.historical_normal!==undefined&&<p className="mt-2 text-xs font-semibold text-gray-600">{t.historicalNormal}: {displayNumber(flag.historical_normal,flag.unit)}</p>}</div>;})}</div>
      {biharRabi&&<div className={`${panel} mb-5 p-5`}><h3 className="font-bold text-gray-900">{bilingual(language,"Bihar Rabi 2025 rainfall details","ÃƒÂ Ã‚Â¤Ã‚Â¬ÃƒÂ Ã‚Â¤Ã‚Â¿ÃƒÂ Ã‚Â¤Ã‚Â¹ÃƒÂ Ã‚Â¤Ã‚Â¾ÃƒÂ Ã‚Â¤Ã‚Â° ÃƒÂ Ã‚Â¤Ã‚Â°ÃƒÂ Ã‚Â¤Ã‚Â¬ÃƒÂ Ã‚Â¥Ã¢â€šÂ¬ 2025 ÃƒÂ Ã‚Â¤Ã‚ÂµÃƒÂ Ã‚Â¤Ã‚Â°ÃƒÂ Ã‚Â¥Ã‚ÂÃƒÂ Ã‚Â¤Ã‚Â·ÃƒÂ Ã‚Â¤Ã‚Â¾ ÃƒÂ Ã‚Â¤Ã‚ÂµÃƒÂ Ã‚Â¤Ã‚Â¿ÃƒÂ Ã‚Â¤Ã‚ÂµÃƒÂ Ã‚Â¤Ã‚Â°ÃƒÂ Ã‚Â¤Ã‚Â£")}</h3><div className="mt-3 grid gap-3 sm:grid-cols-2"><div className="rounded-xl bg-blue-50 p-4"><p className="text-xs text-blue-800">{bilingual(language,"Total dry days (<1 mm/day)","ÃƒÂ Ã‚Â¤Ã¢â‚¬Â¢ÃƒÂ Ã‚Â¥Ã‚ÂÃƒÂ Ã‚Â¤Ã‚Â² ÃƒÂ Ã‚Â¤Ã‚Â¶ÃƒÂ Ã‚Â¥Ã‚ÂÃƒÂ Ã‚Â¤Ã‚Â·ÃƒÂ Ã‚Â¥Ã‚ÂÃƒÂ Ã‚Â¤Ã¢â‚¬Â¢ ÃƒÂ Ã‚Â¤Ã‚Â¦ÃƒÂ Ã‚Â¤Ã‚Â¿ÃƒÂ Ã‚Â¤Ã‚Â¨ (<1 ÃƒÂ Ã‚Â¤Ã‚Â®ÃƒÂ Ã‚Â¤Ã‚Â¿ÃƒÂ Ã‚Â¤Ã‚Â®ÃƒÂ Ã‚Â¥Ã¢â€šÂ¬/ÃƒÂ Ã‚Â¤Ã‚Â¦ÃƒÂ Ã‚Â¤Ã‚Â¿ÃƒÂ Ã‚Â¤Ã‚Â¨)")}</p><p className="text-2xl font-bold">172 days</p></div><div className="rounded-xl bg-amber-50 p-4"><p className="text-xs text-amber-800">{bilingual(language,"Longest consecutive dry spell","ÃƒÂ Ã‚Â¤Ã‚Â¸ÃƒÂ Ã‚Â¤Ã‚Â¬ÃƒÂ Ã‚Â¤Ã‚Â¸ÃƒÂ Ã‚Â¥Ã¢â‚¬Â¡ ÃƒÂ Ã‚Â¤Ã‚Â²ÃƒÂ Ã‚Â¤Ã¢â‚¬Å¡ÃƒÂ Ã‚Â¤Ã‚Â¬ÃƒÂ Ã‚Â¥Ã¢â€šÂ¬ ÃƒÂ Ã‚Â¤Ã‚Â²ÃƒÂ Ã‚Â¤Ã¢â‚¬â€ÃƒÂ Ã‚Â¤Ã‚Â¾ÃƒÂ Ã‚Â¤Ã‚Â¤ÃƒÂ Ã‚Â¤Ã‚Â¾ÃƒÂ Ã‚Â¤Ã‚Â° ÃƒÂ Ã‚Â¤Ã‚Â¶ÃƒÂ Ã‚Â¥Ã‚ÂÃƒÂ Ã‚Â¤Ã‚Â·ÃƒÂ Ã‚Â¥Ã‚ÂÃƒÂ Ã‚Â¤Ã¢â‚¬Â¢ ÃƒÂ Ã‚Â¤Ã¢â‚¬Â¦ÃƒÂ Ã‚Â¤Ã‚ÂµÃƒÂ Ã‚Â¤Ã‚Â§ÃƒÂ Ã‚Â¤Ã‚Â¿")}</p><p className="text-2xl font-bold">138 days</p><p className="mt-1 text-xs">2 Nov 2025 ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Å“ 19 Mar 2026</p></div></div><p className="mt-3 text-xs text-gray-600">{bilingual(language,"Verified by the data team against saved NASA POWER daily records (181 records; 0 missing rainfall observations).","ÃƒÂ Ã‚Â¤Ã‚Â¡ÃƒÂ Ã‚Â¥Ã¢â‚¬Â¡ÃƒÂ Ã‚Â¤Ã…Â¸ÃƒÂ Ã‚Â¤Ã‚Â¾ ÃƒÂ Ã‚Â¤Ã…Â¸ÃƒÂ Ã‚Â¥Ã¢â€šÂ¬ÃƒÂ Ã‚Â¤Ã‚Â® ÃƒÂ Ã‚Â¤Ã‚Â¨ÃƒÂ Ã‚Â¥Ã¢â‚¬Â¡ ÃƒÂ Ã‚Â¤Ã‚Â¸ÃƒÂ Ã‚Â¤Ã¢â‚¬Å¡ÃƒÂ Ã‚Â¤Ã¢â‚¬â€ÃƒÂ Ã‚Â¥Ã‚ÂÃƒÂ Ã‚Â¤Ã‚Â°ÃƒÂ Ã‚Â¤Ã‚Â¹ÃƒÂ Ã‚Â¥Ã¢â€šÂ¬ÃƒÂ Ã‚Â¤Ã‚Â¤ NASA POWER ÃƒÂ Ã‚Â¤Ã‚Â¦ÃƒÂ Ã‚Â¥Ã‹â€ ÃƒÂ Ã‚Â¤Ã‚Â¨ÃƒÂ Ã‚Â¤Ã‚Â¿ÃƒÂ Ã‚Â¤Ã¢â‚¬Â¢ ÃƒÂ Ã‚Â¤Ã‚Â°ÃƒÂ Ã‚Â¤Ã‚Â¿ÃƒÂ Ã‚Â¤Ã¢â‚¬Â¢ÃƒÂ Ã‚Â¥Ã¢â‚¬Â°ÃƒÂ Ã‚Â¤Ã‚Â°ÃƒÂ Ã‚Â¥Ã‚ÂÃƒÂ Ã‚Â¤Ã‚Â¡ ÃƒÂ Ã‚Â¤Ã‚Â¸ÃƒÂ Ã‚Â¥Ã¢â‚¬Â¡ ÃƒÂ Ã‚Â¤Ã…â€œÃƒÂ Ã‚Â¤Ã‚Â¾ÃƒÂ Ã‚Â¤Ã‚ÂÃƒÂ Ã‚Â¤Ã…Â¡ ÃƒÂ Ã‚Â¤Ã¢â‚¬Â¢ÃƒÂ Ã‚Â¥Ã¢â€šÂ¬ (181 ÃƒÂ Ã‚Â¤Ã‚Â°ÃƒÂ Ã‚Â¤Ã‚Â¿ÃƒÂ Ã‚Â¤Ã¢â‚¬Â¢ÃƒÂ Ã‚Â¥Ã¢â‚¬Â°ÃƒÂ Ã‚Â¤Ã‚Â°ÃƒÂ Ã‚Â¥Ã‚ÂÃƒÂ Ã‚Â¤Ã‚Â¡; ÃƒÂ Ã‚Â¤Ã‚ÂµÃƒÂ Ã‚Â¤Ã‚Â°ÃƒÂ Ã‚Â¥Ã‚ÂÃƒÂ Ã‚Â¤Ã‚Â·ÃƒÂ Ã‚Â¤Ã‚Â¾ ÃƒÂ Ã‚Â¤Ã¢â‚¬Â¢ÃƒÂ Ã‚Â¥Ã¢â‚¬Â¡ 0 ÃƒÂ Ã‚Â¤Ã‚Â°ÃƒÂ Ã‚Â¤Ã‚Â¿ÃƒÂ Ã‚Â¤Ã¢â‚¬Â¢ÃƒÂ Ã‚Â¥Ã¢â‚¬Â°ÃƒÂ Ã‚Â¤Ã‚Â°ÃƒÂ Ã‚Â¥Ã‚ÂÃƒÂ Ã‚Â¤Ã‚Â¡ ÃƒÂ Ã‚Â¤Ã¢â‚¬Â¦ÃƒÂ Ã‚Â¤Ã‚Â¨ÃƒÂ Ã‚Â¥Ã‚ÂÃƒÂ Ã‚Â¤Ã‚ÂªÃƒÂ Ã‚Â¤Ã‚Â²ÃƒÂ Ã‚Â¤Ã‚Â¬ÃƒÂ Ã‚Â¥Ã‚ÂÃƒÂ Ã‚Â¤Ã‚Â§)ÃƒÂ Ã‚Â¥Ã‚Â¤")}</p></div>}
      {quality&&<div className={`${panel} mb-5 p-5`}><h3 className="font-bold text-gray-900">{bilingual(language,"Seasonal data quality","Seasonal data quality")}</h3><p className="mt-2 text-sm text-gray-600">{quality.period_start} - {quality.period_end}</p><div className="mt-3 flex flex-wrap gap-3 text-sm">{[["Rainfall",quality.missing_pct?.rain],["Mean temperature",quality.missing_pct?.t_mean],["Maximum temperature",quality.missing_pct?.t_max]].map(([label,value])=><span key={label} className="rounded-lg bg-gray-50 px-3 py-2">{label}: {value==null?"Not available":`${value}% missing`}</span>)}</div><p className="mt-3 text-xs text-gray-500">{bilingual(language,"The 'complete' flag checks season end-date coverage, not whether every daily observation is present.","The 'complete' flag checks season end-date coverage, not whether every daily observation is present.")}</p></div>}
      {!flags.length&&<div className={`${panel} p-6 text-sm text-gray-600`}>{t.noFlags}</div>}
      <div className="mt-6 rounded-2xl border border-amber-200 bg-amber-50 p-5"><div className="flex gap-3"><Info className="mt-0.5 shrink-0 text-amber-700" size={21}/><div><h3 className="font-bold text-amber-900">{t.climateOnly}</h3><p className="mt-2 text-sm leading-6 text-amber-900">{seasonData?.interpretation_note || t.climateOnly}</p><p className="mt-2 text-xs text-amber-800">{seasonData?.complete ? t.complete : t.incomplete}</p></div></div></div>
      <div className="mt-6 rounded-2xl border border-gray-200 bg-white p-5"><div className="flex items-center gap-2 font-bold text-gray-900"><Database size={18} className="text-emerald-700"/>{t.sources}</div><p className="mt-2 text-sm text-gray-600">{frontendData.source || "NASA POWER Daily API"}</p><p className="mt-2 text-xs leading-5 text-gray-500">{t.dataNotice}</p><p className="mt-2 text-xs leading-5 text-gray-500">{t.baselineSentence}: {JSON.stringify(district.baseline_years)}. {t.periodSentence}</p></div>
      <div className="mt-8 flex flex-wrap justify-between gap-3"><button onClick={goBack} className={secondaryButton}><ArrowLeft size={17}/>{t.back}</button><button onClick={()=>setPage("comparison")} className={primaryButton}>{t.compareOptions}<ArrowRight size={17}/></button></div>
    </div>;
  }

  function ComparisonPage() {
    const rotations = liveRotations || district.rotations || [];
    const factors=[{icon:Droplet,title:t.waterFactor,description:t.verifyWater},{icon:Mountain,title:t.soilFactor,description:t.verifySoil},{icon:CloudSun,title:t.climateFactor,description:t.interpretClimate},{icon:Flower2,title:t.cropFactor,description:t.verifyCalendar},{icon:TrendingUp,title:t.priorityFactor,description:`Farmer priority: ${profile.priority}.`}];
    return <div className="mx-auto max-w-7xl px-5 py-12 lg:px-8">{ProgressBar()}<PageHeading step={t.step4} title={t.compare} description={`${t.compareDesc} - ${district.district}, ${district.state}`}/>
      <div className="mb-8 flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-emerald-100 bg-emerald-50 p-5"><div className="flex items-center gap-3"><span className="flex h-12 w-12 items-center justify-center rounded-xl bg-white text-emerald-700"><MapPin size={22}/></span><div><p className="text-xs font-semibold uppercase tracking-wide text-emerald-700">{t.district}</p><p className="text-lg font-bold text-gray-900">{district.district}, {district.state}</p></div></div><div className="text-sm text-gray-600">{t.currentCropLabel}: <strong className="text-gray-900">{profile.currentCrop}</strong></div></div>
      <div className="mb-5 flex flex-wrap items-end justify-between gap-3"><div><h2 className="text-2xl font-bold text-gray-900">{t.rotationOptions}</h2><p className="mt-1 text-sm text-gray-500">{t.exampleComparisons}</p></div><span className="rounded-full bg-gray-100 px-3 py-1.5 text-xs font-bold text-gray-600">{rotations.length} OPTIONS</span></div>
      <div className="grid gap-5 lg:grid-cols-3">{rotations.map((option,index)=>{const score=option.overall;const explanation=option.explanations?.[language==="Hindi"?"hi":"en"] || "This provisional comparison uses illustrative team estimates. Soil health, crop suitability and economics are not scored because verified local evidence is unavailable. It is not a farming recommendation.";const evidence=option.crop_evidence||[];return <article key={option.id} className={`${panel} flex flex-col overflow-hidden`}><div className={`h-1.5 ${index===0?"bg-gray-300":index===1?"bg-emerald-500":"bg-lime-500"}`}/><div className="flex flex-1 flex-col p-6"><div className="flex flex-wrap items-center justify-between gap-2"><span className="rounded-full bg-gray-100 px-3 py-1 text-xs font-bold text-gray-700">{pretty(option.id)} - {pretty(option.type)}</span><span className="text-xs font-semibold text-amber-700">{pretty(option.evidence_status)}</span></div><h3 className="mt-5 text-xl font-bold text-gray-900">{(option.crops||[]).map(cropName).join(" -> ")}</h3><p className="mt-2 text-sm leading-6 text-gray-500">{option.display_note||option.label||"Example crop sequence for comparison."}</p><div className="my-5 rounded-2xl bg-[#f4f8f1] p-4"><p className="text-xs font-bold uppercase tracking-wide text-emerald-800">{t.cropSequence}</p><div className="mt-3 flex flex-wrap items-center gap-2">{(option.crops||[]).map((crop,i)=><span key={`${crop}-${i}`} className="rounded-xl border border-emerald-100 bg-white px-3 py-2 text-sm font-bold text-gray-800">{cropName(crop)}</span>)}</div></div><div className="border-t border-gray-100 pt-4"><p className="text-xs font-bold uppercase tracking-wider text-gray-400">{t.score}</p><p className="mt-2 text-sm font-semibold text-gray-600">{score===null||score===undefined?"Not available":`${Number(score).toFixed(2)} / 100`}</p><p className="mt-2 text-xs text-amber-800">{option.score_note||"Illustrative team estimates; not a validated suitability ranking."} - {option.score_coverage?.available_count??0}/{option.score_coverage?.total_count??5} components available</p><div className="mt-2 grid grid-cols-2 gap-2 text-xs">{Object.entries(option.scores||{}).map(([key,value])=><div key={key} className="rounded-lg bg-gray-50 p-2"><span className="block text-gray-500">{pretty(key)}</span><strong>{value==null?"Not available":Number(value).toFixed(2)}</strong></div>)}</div><div className="mt-3 flex flex-wrap gap-2"><span className="rounded-full bg-rose-50 px-3 py-1 text-xs font-semibold text-rose-700">{t.confidence}: {pretty(option.confidence||"unknown")}</span>{option.needs_expert_review&&<span className="rounded-full bg-amber-50 px-3 py-1 text-xs font-semibold text-amber-800">{t.expert}</span>}</div></div>
        <div className="mt-5"><p className="text-xs font-bold uppercase tracking-wide text-gray-500">{t.evidence}</p>{evidence.length?evidence.map((ev,i)=><div key={i} className="mt-2 text-sm">{ev.source_url?<a href={ev.source_url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-emerald-700 underline">{ev.title||ev.crop_name||t.evidenceSource}<ExternalLink size={13}/></a>:<span>{ev.title||ev.crop_name||t.evidenceItem}</span>}</div>):<p className="mt-2 text-xs leading-5 text-gray-500">{t.noEvidence}</p>}{evidence.length>0&&<p className="mt-2 text-xs text-gray-500">{bilingual(language,"Supporting links do not independently validate the ratings.","ÃƒÂ Ã‚Â¤Ã‚Â¸ÃƒÂ Ã‚Â¤Ã¢â‚¬Å¡ÃƒÂ Ã‚Â¤Ã‚Â¦ÃƒÂ Ã‚Â¤Ã‚Â°ÃƒÂ Ã‚Â¥Ã‚ÂÃƒÂ Ã‚Â¤Ã‚Â­ ÃƒÂ Ã‚Â¤Ã‚Â²ÃƒÂ Ã‚Â¤Ã‚Â¿ÃƒÂ Ã‚Â¤Ã¢â‚¬Å¡ÃƒÂ Ã‚Â¤Ã¢â‚¬Â¢ ÃƒÂ Ã‚Â¤Ã‚Â°ÃƒÂ Ã‚Â¥Ã¢â‚¬Â¡ÃƒÂ Ã‚Â¤Ã…Â¸ÃƒÂ Ã‚Â¤Ã‚Â¿ÃƒÂ Ã‚Â¤Ã¢â‚¬Å¡ÃƒÂ Ã‚Â¤Ã¢â‚¬â€ ÃƒÂ Ã‚Â¤Ã¢â‚¬Â¢ÃƒÂ Ã‚Â¤Ã‚Â¾ ÃƒÂ Ã‚Â¤Ã‚Â¸ÃƒÂ Ã‚Â¥Ã‚ÂÃƒÂ Ã‚Â¤Ã‚ÂµÃƒÂ Ã‚Â¤Ã‚Â¤ÃƒÂ Ã‚Â¤Ã¢â‚¬Å¡ÃƒÂ Ã‚Â¤Ã‚Â¤ÃƒÂ Ã‚Â¥Ã‚ÂÃƒÂ Ã‚Â¤Ã‚Â° ÃƒÂ Ã‚Â¤Ã‚Â¸ÃƒÂ Ã‚Â¤Ã‚Â¤ÃƒÂ Ã‚Â¥Ã‚ÂÃƒÂ Ã‚Â¤Ã‚Â¯ÃƒÂ Ã‚Â¤Ã‚Â¾ÃƒÂ Ã‚Â¤Ã‚ÂªÃƒÂ Ã‚Â¤Ã‚Â¨ ÃƒÂ Ã‚Â¤Ã‚Â¨ÃƒÂ Ã‚Â¤Ã‚Â¹ÃƒÂ Ã‚Â¥Ã¢â€šÂ¬ÃƒÂ Ã‚Â¤Ã¢â‚¬Å¡ ÃƒÂ Ã‚Â¤Ã‚Â¹ÃƒÂ Ã‚Â¥Ã‹â€ ÃƒÂ Ã‚Â¤Ã¢â‚¬Å¡ÃƒÂ Ã‚Â¥Ã‚Â¤")}</p>}{evidence.map((ev,i)=><div key={`ratings-${i}`} className="mt-2 rounded-lg border border-gray-100 p-3"><p className="text-xs font-semibold text-gray-700">{cropName(ev.crop_id||ev.crop_name)}</p>{Object.entries(ev.ratings||{}).map(([name,detail])=><p key={name} className="mt-1 text-xs text-gray-600">{pretty(name)}: <strong>{detail.classification==="team_estimate"?"Team estimate":detail.classification==="pending_source_verification"?"Pending source verification":pretty(detail.classification)}</strong></p>)}</div>)}</div>
        {option.missing_info?.length>0&&<details className="mt-5 rounded-xl bg-amber-50 p-3"><summary className="cursor-pointer text-sm font-bold text-amber-900">{t.missing} ({option.missing_info.length})</summary><ul className="mt-2 list-disc space-y-1 pl-5 text-xs leading-5 text-amber-900">{option.missing_info.filter(Boolean).map((m,i)=><li key={i}>{String(m)}</li>)}</ul></details>}
        {explanation&&<details className="mt-3 rounded-xl bg-gray-50 p-3"><summary className="cursor-pointer text-sm font-semibold text-gray-700">{language==="Hindi"?"ÃƒÂ Ã‚Â¤Ã‚ÂµÃƒÂ Ã‚Â¤Ã‚Â¿ÃƒÂ Ã‚Â¤Ã‚Â¸ÃƒÂ Ã‚Â¥Ã‚ÂÃƒÂ Ã‚Â¤Ã‚Â¤ÃƒÂ Ã‚Â¥Ã†â€™ÃƒÂ Ã‚Â¤Ã‚Â¤ ÃƒÂ Ã‚Â¤Ã‚ÂµÃƒÂ Ã‚Â¥Ã‚ÂÃƒÂ Ã‚Â¤Ã‚Â¯ÃƒÂ Ã‚Â¤Ã‚Â¾ÃƒÂ Ã‚Â¤Ã¢â‚¬â€œÃƒÂ Ã‚Â¥Ã‚ÂÃƒÂ Ã‚Â¤Ã‚Â¯ÃƒÂ Ã‚Â¤Ã‚Â¾":t.detailedExplanation}</summary><p className="mt-2 whitespace-pre-line text-xs leading-5 text-gray-600">{explanation}</p></details>}
        <div className="mt-auto pt-5"><p className="text-xs text-gray-500">{t.decisionStatusLabel}: {pretty(option.decision_status||t.notSupplied)}</p>{option.sources?.length>0&&<p className="mt-1 text-xs text-gray-500">{t.sourcesListed}: {option.sources.join(", ")}</p>}</div></div></article>;})}</div>
      <div className="mt-10"><div className="mb-5 text-center"><p className="text-xs font-bold uppercase tracking-widest text-emerald-700">{t.climateInformedTitle}</p><h2 className="mt-2 text-2xl font-bold text-gray-900">{t.factors}</h2></div><div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">{factors.map((f,i)=><div key={i} className={`${panel} flex gap-4 p-5`}><span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-emerald-50 text-emerald-700"><f.icon size={22}/></span><div><h3 className="font-bold text-gray-900">{f.title}</h3><p className="mt-1 text-sm leading-6 text-gray-500">{f.description}</p></div></div>)}</div></div>
      <div className="mt-8 rounded-2xl border border-amber-200 bg-amber-50 p-5"><div className="flex gap-3"><AlertTriangle className="mt-0.5 shrink-0 text-amber-700" size={21}/><div><h3 className="font-bold text-amber-900">{t.pleaseNote}</h3><p className="mt-1 text-sm leading-7 text-amber-900">{t.disclaimer}</p></div></div></div>
      <div className="mt-8 flex flex-wrap justify-between gap-3"><button onClick={goBack} className={secondaryButton}><ArrowLeft size={17}/>{t.back}</button><button onClick={()=>setPage("profile")} className={primaryButton}><RotateCcw size={17}/>{t.editProfile}</button></div>
    </div>;
  }

  return <div className="min-h-screen bg-[#fbfcfa] text-gray-800">{Header()}<main>{page==="home"&&HomePage()}{page==="region"&&RegionPage()}{page==="profile"&&ProfilePage()}{page==="dashboard"&&DashboardPage()}{page==="comparison"&&ComparisonPage()}</main>{Footer()}</div>;
}

export default App;


