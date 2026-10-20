"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import {
  ArrowLeft, ArrowRight, ArrowUpRight, BookOpen, Check, ChevronDown, CircleHelp, Copy,
  Clock3, Compass, Download, FileText, GraduationCap, HeartHandshake, LoaderCircle,
  MapPin, Menu, MessageCircle, PencilLine, Plus, RefreshCw, Send, Settings2,
  ShieldCheck, X,
} from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { SiteHeader } from "@/components/site-header";
import { exportProposal, splitSections, streamProposal } from "@/lib/api";
import {
  CITIES, DEFAULT_MODEL, DEFAULT_REQUEST, DURATIONS, IDENTITIES, INTERESTS,
  MODEL_PROVIDERS, STYLES,
  type AppStatus, type ModelOptions, type Plan, type Scene, type StreamEvent, type TaskRequest,
} from "@/lib/types";

const SCENES = [
  { key:"游客路线", name:"城市漫游", desc:"从街巷走进传统", icon:Compass, en:"CITY WALK" },
  { key:"学生研学", name:"文化研学", desc:"带着问题去观察", icon:GraduationCap, en:"STUDY" },
  { key:"亲子体验", name:"亲子体验", desc:"让孩子亲手感知", icon:HeartHandshake, en:"FAMILY" },
  { key:"内容创作", name:"内容创作", desc:"传播鲜活的文化", icon:PencilLine, en:"CREATION" },
  { key:"非遗问答", name:"非遗问答", desc:"听见技艺背后故事", icon:MessageCircle, en:"DISCOVER" },
] as const;

const EXAMPLES = [
  { title:"广州 · 一日非遗漫游", scene:"游客路线" as Scene, city:"广州", duration:"一天", identity:"外地游客", text:"我第一次来广州，有一天时间，想体验岭南非遗文化，适合拍照并且路线轻松。", interests:["粤剧","岭南建筑"] },
  { title:"佛山 · 周末亲子手作", scene:"亲子体验" as Scene, city:"佛山", duration:"周末", identity:"亲子家庭", text:"周末带孩子去佛山，想体验醒狮和石湾陶塑，节奏轻松一点。", interests:["醒狮","陶塑"] },
  { title:"校园 · 研学观察记录", scene:"学生研学" as Scene, city:"自动判断", duration:"一天", identity:"学生研学", text:"我是高中生，要做一份广东非遗研学报告，请围绕粤剧、醒狮和广绣设计任务卡和观察记录表。", interests:["粤剧","醒狮","广绣"] },
  { title:"潮汕 · 英歌舞图文", scene:"内容创作" as Scene, city:"汕头", duration:"不限", identity:"内容创作者", text:"帮我写一篇适合小红书发布的潮汕英歌舞图文，语言生动，附上配图建议和标签。", interests:["拍照"] },
];
const MAX_RECENTS = 3;
const REVISIONS = ["压缩成半天", "更适合亲子", "生成小红书文案", "生成短视频脚本", "加研学记录表"];
const isScene = (text: string | null): text is Scene => !!text && SCENES.some((scene) => scene.key === text);
const makeId = () => typeof crypto !== "undefined" && "randomUUID" in crypto ? crypto.randomUUID() : String(Date.now());

function Choice({ label, value, values, onChange }: {
  label: string; value: string; values: readonly string[]; onChange: (value: string) => void;
}) {
  return <label className="field"><span>{label}</span><span className="select-wrap">
    <select value={value} onChange={(event) => onChange(event.target.value)}>
      {values.map((item) => <option key={item} value={item}>{item}</option>)}
    </select><ChevronDown size={16} aria-hidden="true"/>
  </span></label>;
}

function ModelSettings({ model, setModel, onClose, platformReady }: {
  model: ModelOptions; setModel: (model: ModelOptions) => void; onClose: () => void; platformReady?: boolean;
}) {
  const patch = (values: Partial<ModelOptions>) => setModel({ ...model, ...values });
  const closeButtonRef = useRef<HTMLButtonElement>(null);
  const dialogRef = useRef<HTMLElement>(null);
  useEffect(() => {
    const previous = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    closeButtonRef.current?.focus();
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") { event.preventDefault(); onClose(); return; }
      if (event.key !== "Tab" || !dialogRef.current) return;
      const items = Array.from(dialogRef.current.querySelectorAll<HTMLElement>(
        'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])',
      ));
      if (!items.length) return;
      const first = items[0], last = items[items.length - 1];
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
    };
    document.addEventListener("keydown", onKey);
    return () => { document.removeEventListener("keydown", onKey); previous?.focus(); };
  }, [onClose]);
  return <div className="modal-backdrop" onMouseDown={(event) => {if (event.target === event.currentTarget) onClose();}}>
    <section ref={dialogRef} className="settings-dialog" role="dialog" aria-modal="true" aria-labelledby="settings-title" onMouseDown={(event) => event.stopPropagation()}>
      <div className="dialog-heading"><h2 id="settings-title">AI 服务设置</h2><button ref={closeButtonRef} type="button" className="icon-btn" onClick={onClose} aria-label="关闭设置"><X size={20}/></button></div>
      <p className="settings-description">优先使用平台服务，也可以自行连接 API。</p>
      <div className="settings-segments" role="group" aria-label="AI 模型来源">
        <button type="button" className={model.mode === "auto" ? "selected" : ""} onClick={() => patch({ mode:"auto" })}>平台服务</button>
        <button type="button" className={model.mode === "user" ? "selected" : ""} onClick={() => patch({ mode:"user" })}>使用我的 API</button>
      </div>
      {model.mode === "auto" ? <div className={`service-notice ${platformReady ? "service-ok" : "service-warn"}`}><ShieldCheck size={19}/><div><strong>{platformReady ? "平台服务已就绪" : "平台免费额度暂未开放"}</strong><p>{platformReady ? "可直接返回工作台生成方案。" : "平台额度保护尚未启用，暂不能使用共享模型。你可以使用自己的 API。"}</p></div></div> : <>
        <Choice label="服务商" value={model.provider} values={Object.keys(MODEL_PROVIDERS)} onChange={(provider) => patch({ provider, ...MODEL_PROVIDERS[provider as keyof typeof MODEL_PROVIDERS] })}/>
        <label className="field"><span>API Key（仅保留在当前页面）</span><input type="password" name="private_api_key" autoComplete="new-password" spellCheck={false} value={model.api_key} placeholder="sk-••••••••••" onChange={(e) => patch({ api_key:e.target.value })}/></label>
        <label className="field"><span>Base URL</span><input name="private_base_url" type="url" autoComplete="off" spellCheck={false} value={model.base_url} placeholder="https://api.example.com/v1" onChange={(e) => patch({ base_url:e.target.value })}/></label>
        <label className="field"><span>模型名称</span><input name="private_model_name" autoComplete="off" spellCheck={false} value={model.model_name} placeholder="模型 ID" onChange={(e) => patch({ model_name:e.target.value })}/></label>
        <button className="clear-key" type="button" onClick={() => patch({ api_key:"", mode:"auto" })}>清除 API Key 并返回平台服务</button>
      </>}
      <label className="field"><span>生成语言灵活度 <b>{model.temperature.toFixed(2)}</b></span><input type="range" min=".1" max="1" step=".05" value={model.temperature} onChange={(e) => patch({temperature:Number(e.target.value)})}/></label>
      <div className="settings-security"><ShieldCheck size={17} aria-hidden="true"/> 个人 API Key 不会存入浏览器本地存储。</div>
      <button className="button button-dark settings-done" type="button" onClick={onClose}>完成设置 <Check size={17}/></button>
    </section>
  </div>;
}

function MarkdownDoc({ content }: { content: string }) {
  return <div className="markdown-document"><ReactMarkdown remarkPlugins={[remarkGfm]} skipHtml>{content}</ReactMarkdown></div>;
}

export function StudioApp() {
  const params = useSearchParams();
  const [request, setRequest] = useState<TaskRequest>(() => {
    const selectedScene = params.get("scene");
    const selectedCity = params.get("city");
    const selectedPrompt = params.get("prompt");
    return {
      ...DEFAULT_REQUEST,
      ...(isScene(selectedScene) ? { scene:selectedScene, task_type:selectedScene === "内容创作" ? "social" as const : null } : {}),
      ...(selectedCity && CITIES.includes(selectedCity) ? { city:selectedCity } : {}),
      ...(selectedPrompt ? { raw_request:selectedPrompt.slice(0,1200) } : {}),
    };
  });
  const [model, setModel] = useState<ModelOptions>(DEFAULT_MODEL);
  const [status, setStatus] = useState<AppStatus | null>(null);
  const [statusError, setStatusError] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [interestsOpen, setInterestsOpen] = useState(false);
  const [result, setResult] = useState<Plan | null>(null);
  const [recents, setRecents] = useState<Plan[]>([]);
  const [hydrated, setHydrated] = useState(false);
  const [stream, setStream] = useState("");
  const [busy, setBusy] = useState(false);
  const [stage, setStage] = useState("正在理解你的需求…");
  const [error, setError] = useState("");
  const [activeTab, setActiveTab] = useState("all");
  const [revision, setRevision] = useState("");
  const [downloadBusy, setDownloadBusy] = useState(false);
  const [notice, setNotice] = useState("");
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const sidebarRef = useRef<HTMLElement>(null);
  const sidebarCloseRef = useRef<HTMLButtonElement>(null);
  const controller = useRef<AbortController | null>(null);
  const pendingHomepageLaunch = useRef(false);
  const closeSettings = useCallback(() => setShowSettings(false), []);

  useEffect(() => {
    if (!drawerOpen) return;
    const previous = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    sidebarCloseRef.current?.focus();
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") { event.preventDefault(); setDrawerOpen(false); return; }
      if (event.key !== "Tab" || !sidebarRef.current) return;
      const elements = Array.from(sidebarRef.current.querySelectorAll<HTMLElement>("button:not([disabled]),a[href]"));
      const first = elements[0], last = elements[elements.length - 1];
      if (!first || !last) return;
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
    };
    document.addEventListener("keydown", onKey);
    return () => { document.removeEventListener("keydown", onKey); previous?.focus(); };
  }, [drawerOpen]);

  useEffect(() => {
    const checkStatus = async () => {
      for (let attempt = 0; attempt < 3; attempt++) {
        try {
          const response = await fetch("/api/v1/status", {cache:"no-store",signal:AbortSignal.timeout(6500)});
          if (!response.ok) throw Error("status unavailable");
          const info = await response.json() as AppStatus;
          setStatus(info); setStatusError(false);
          return;
        } catch {
          // Brief retries are safe: status never spends an AI quota.
          if (attempt < 2) await new Promise((resolve) => setTimeout(resolve, 500 * (attempt + 1)));
        }
      }
      setStatusError(true);
    };
    void checkStatus();
    // Defer hydration to a callback; initial render stays SSR-safe.
    queueMicrotask(() => {
      try {
        const draft = sessionStorage.getItem("yuejian-launch-draft");
        pendingHomepageLaunch.current = sessionStorage.getItem("yuejian-start-immediately") === "1";
        sessionStorage.removeItem("yuejian-start-immediately");
        if (draft) {
          sessionStorage.removeItem("yuejian-launch-draft");
          const selected = JSON.parse(draft) as TaskRequest;
          if (isScene(selected.scene) && typeof selected.raw_request === "string" && selected.raw_request.length <= 1200) {
            setRequest({ ...DEFAULT_REQUEST, ...selected, city:CITIES.includes(selected.city) ? selected.city : "自动判断" });
          }
        }
      } catch { /* Cross-page draft is optional. */ }
      try {
        const saved = sessionStorage.getItem("yuejian-recent-plans-v2");
        if (saved) {
          const parsed = JSON.parse(saved) as Plan[];
          if (Array.isArray(parsed)) setRecents(parsed.filter((plan) => plan && plan.id && plan.request && typeof plan.answer === "string").slice(0, MAX_RECENTS));
        }
      } catch { /* Browsers may block session storage. */ }
      setHydrated(true);
    });
    return () => controller.current?.abort();
  }, []);

  useEffect(() => {
    if (!hydrated || !status || !pendingHomepageLaunch.current) return;
    pendingHomepageLaunch.current = false;
    queueMicrotask(() => document.getElementById("generate-submit")?.click());
  }, [hydrated, status]);

  useEffect(() => {
    if (!hydrated) return;
    try { sessionStorage.setItem("yuejian-recent-plans-v2", JSON.stringify(recents)); }
    catch { /* Storage is a convenience, not a prerequisite. */ }
  }, [recents, hydrated]);

  function patch(fields: Partial<TaskRequest>) { setRequest((prev) => ({ ...prev, ...fields })); }
  function selectScene(scene: Scene) {
    patch({ scene, task_type: scene === "内容创作" ? "social" : null });
    setDrawerOpen(false);
  }
  function applyExample(index: number) {
    const item = EXAMPLES[index];
    setRequest({
      ...DEFAULT_REQUEST, scene:item.scene, raw_request:item.text, city:item.city,
      duration:item.duration, identity:item.identity, interests:item.interests,
      task_type: item.scene === "内容创作" ? "social" : null,
    });
    setError("");
  }
  function startNew() {
    if ((request.raw_request.trim() || result) && !window.confirm("开始新方案？当前编辑内容将清空，已生成的方案仍可在最近记录中查看。")) return;
    controller.current?.abort();
    setBusy(false); setRequest(DEFAULT_REQUEST); setResult(null); setStream(""); setError("");
    setRevision(""); setActiveTab("all"); setDrawerOpen(false); setNotice("");
    requestAnimationFrame(() => inputRef.current?.focus());
  }
  function savePlan(plan: Plan) {
    setRecents((prev) => [plan, ...prev.filter((entry) => entry.id !== plan.id)].slice(0, MAX_RECENTS));
    setResult(plan);
  }

  async function run(kind: "generate" | "revise", preset?: string) {
    if (busy) return;
    if (kind === "revise" && !result) return;
    if (kind === "generate" && !request.raw_request.trim()) { setError("请先写下你的需求，或者使用示例。"); inputRef.current?.focus(); return; }
    if (model.mode === "user" && (!model.api_key.trim() || !model.base_url.trim() || !model.model_name.trim())) { setError("请先在 AI 服务设置中填写完整的个人 API 信息。"); setShowSettings(true); return; }
    setBusy(true); setError(""); setNotice(""); setStream(""); setActiveTab("all"); setStage("正在准备你的方案…");
    const abortController = new AbortController();
    controller.current = abortController;
    const previous = result;
    let generated = false;
    try {
      await streamProposal(
        kind,
        kind === "revise" && previous ? previous.request : request,
        model,
        kind === "revise" && previous ? { current_answer:previous.answer, ...(preset ? {preset} : {instruction:revision.trim()}) } : null,
        (event: StreamEvent) => {
          if (event.type === "stage") setStage(event.label);
          if (event.type === "snapshot") setStream(event.text);
          if (event.type === "delta") setStream((value) => value + event.text);
          if (event.type === "failure") { setError(event.message); setStream(""); }
          if (event.type === "complete") {
            generated = true;
            const plan: Plan = {
              id: kind === "revise" && previous ? previous.id : makeId(),
              request:event.request, answer:event.answer, sources:event.sources,
              createdAt:new Date().toLocaleString("zh-CN"),
              metrics:event.metrics,
              quality:event.quality,
              revisions:kind === "revise" && previous
                ? [...previous.revisions, {instruction:preset || revision, createdAt:new Date().toLocaleTimeString("zh-CN")}].slice(-10)
                : [],
            };
            savePlan(plan);
            setRequest(event.request);
            setStream(""); setActiveTab("all"); setRevision("");
            requestAnimationFrame(() => document.getElementById("proposal")?.scrollIntoView({behavior:"smooth",block:"start"}));
          }
        },
        abortController.signal,
      );
      if (!generated) {
        // An error event has already populated the human-readable status.
      }
    } catch (err) {
      if (!abortController.signal.aborted) setError(err instanceof Error ? err.message : "请求失败，请稍后重试。");
    } finally {
      setBusy(false); controller.current = null;
    }
  }

  async function download(format: "md" | "txt" | "docx") {
    if (!result || downloadBusy) return;
    setDownloadBusy(true); setError(""); setNotice("");
    try { await exportProposal(result.request, result.answer, result.sources, format); setNotice(`已开始下载 ${format === "docx" ? "Word" : format.toUpperCase()} 文件。`); }
    catch (err) { setError(err instanceof Error ? err.message : "导出失败。"); }
    finally { setDownloadBusy(false); }
  }

  async function copyResult() {
    if (!result) return;
    try { await navigator.clipboard.writeText(result.answer); setNotice("方案已复制到剪贴板。"); }
    catch { setNotice("复制失败，请使用下方导出功能保存。"); }
  }

  const shownAnswer = busy ? stream : result?.answer ?? "";
  const sections = splitSections(shownAnswer);
  const selectedContent = activeTab === "all" ? shownAnswer
    : activeTab === "sources" ? result?.sources ?? "" : sections[Number(activeTab)]?.content ?? shownAnswer;
  const visibleScene = SCENES.find((item) => item.key === request.scene) ?? SCENES[0];

  return <>
    <SiteHeader />
    <main className="studio-background" id="main-content">
      <div className="studio-top container">
        <div className="studio-breadcrumb"><Link href="/"><ArrowLeft size={15} aria-hidden="true"/> 首页</Link><span className="crumb-separator">/</span><span>AI 工作台</span></div>
        <div className="studio-top-actions">
          <span className={`studio-service-dot ${status?.platform_ready ? "is-live" : ""}`}/>
          <span className="studio-service-label">{model.mode === "user" ? "个人 API" : status === null ? "正在检查服务…" : status.platform_ready ? "平台服务可用" : "平台服务暂不可用"}</span>
          <button className="toolbar-button" type="button" onClick={() => setShowSettings(true)}><Settings2 size={16}/> AI 设置</button>
        </div>
      </div>
      <div className="studio-shell container">
        <aside ref={sidebarRef} id="studio-scenes" className={`studio-sidebar ${drawerOpen ? "sidebar-open" : ""}`}>
          <div className="sidebar-topline"><div className="sidebar-brand">粤见非遗</div><button ref={sidebarCloseRef} aria-label="关闭菜单" type="button" onClick={() => setDrawerOpen(false)} className="sidebar-close"><X size={19}/></button></div>
          <h2 className="sidebar-heading">选择体验</h2>
          <div className="sidebar-section-label">体验类型</div>
          <div className="sidebar-scene-list">
            {SCENES.map((scene) => {
              const Icon = scene.icon;
              return <button className={`sidebar-scene ${request.scene === scene.key ? "selected" : ""}`} key={scene.key} type="button" onClick={() => selectScene(scene.key)} disabled={busy} aria-pressed={request.scene === scene.key}>
                <span className="sidebar-scene-icon"><Icon size={19} strokeWidth={1.6}/></span>
                <span className="sidebar-scene-text"><strong>{scene.name}</strong><small>{scene.desc}</small></span>
                {request.scene === scene.key ? <span className="sidebar-selected-mark"><Check size={14} aria-hidden="true"/></span> : <ArrowRight className="sidebar-arrow" size={15}/>}
              </button>;
            })}
          </div>
          <div className="sidebar-library">
            <div className="sidebar-section-label">最近生成</div>
            {recents.length ? recents.map((plan) => <button type="button" key={plan.id} className="recent-plan" onClick={() => {
              if (busy) return;
              setResult(plan); setRequest(plan.request); setStream(""); setActiveTab("all"); setDrawerOpen(false); setError(""); setNotice("");
              requestAnimationFrame(() => document.getElementById("proposal")?.scrollIntoView({behavior:"smooth",block:"start"}));
            }}><FileText size={17}/><span><strong>{plan.request.city !== "自动判断" ? plan.request.city : "非遗"} · {plan.request.scene}</strong><small>{plan.createdAt}</small></span></button>) : <p className="no-recents">生成的方案会暂存在这个浏览器会话中。</p>}
          </div>
          
        </aside>

        <div className="studio-main">
          <div className="studio-heading"><div><h1>生成非遗体验方案</h1><p>选择体验类型、描述需求，即可开始。</p></div><div className="studio-heading__art" aria-hidden="true"/><button type="button" className="studio-new-button" onClick={startNew} disabled={busy}><Plus size={17} aria-hidden="true"/> 新方案</button></div>
          <div className="mobile-scene-bar"><button type="button" onClick={() => setDrawerOpen(true)} aria-expanded={drawerOpen} aria-controls="studio-scenes"><Menu size={17}/> {visibleScene.name} <ChevronDown size={15}/></button><button type="button" onClick={startNew}><Plus size={17}/> 新方案</button></div>

          <form className="composer-panel" aria-labelledby="composer-title" onSubmit={(event) => {event.preventDefault();void run("generate");}}>
            <div className="panel-heading">
              <div><h2 id="composer-title">描述你的需求</h2><p>可以很简单，例如“广州一天的广绣与粤剧路线”。</p></div>
            </div>
            <div className="composer-grid">
              <div className="composer-primary">
                <label className="field-head" htmlFor="request-input">你的想法 <small>{request.raw_request.length}/1200</small></label>
                <textarea ref={inputRef} id="request-input" name="request" autoComplete="off" aria-invalid={!!error} aria-describedby={error ? "studio-error" : undefined} rows={4} maxLength={1200} value={request.raw_request} disabled={busy}
                  placeholder="例如：周末带孩子去佛山体验醒狮和陶塑，安排轻松的半天行程……"
                  onChange={(event) => patch({raw_request:event.target.value})}
                  onKeyDown={(event) => {if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {event.preventDefault();void run("generate");}}}/>
                <div className="inspiration-caption">试试这些示例</div>
                <div className="inspiration-list">{EXAMPLES.map((example,index)=><button type="button" key={example.title} disabled={busy} onClick={() => {applyExample(index);inputRef.current?.focus();}}>{example.title}</button>)}</div>
                <div className="interest-wrapper">
                  <button className="interest-toggle" type="button" onClick={() => setInterestsOpen(!interestsOpen)} aria-expanded={interestsOpen}>特别想体验的文化主题 <span>{request.interests.length ? `已选择 ${request.interests.length} 项` : "按需添加"} <ChevronDown size={16}/></span></button>
                  {interestsOpen && <div className="interest-chips">{INTERESTS.map((interest)=><button type="button" disabled={busy} key={interest} aria-pressed={request.interests.includes(interest)} className={request.interests.includes(interest) ? "active" : ""} onClick={() => patch({interests:request.interests.includes(interest) ? request.interests.filter((x) => x !== interest) : [...request.interests,interest]})}>{request.interests.includes(interest) && <Check size={12}/>} {interest}</button>)}</div>}
                </div>
              </div>
              <details className="composer-preferences">
                <summary className="ux-preferences-toggle"><span><Settings2 size={17} aria-hidden="true"/> 更多选项 <small>城市、时长、风格</small></span><ChevronDown size={16} aria-hidden="true"/></summary>
                <div className="ux-preferences-fields">
                <Choice label="探索城市" value={request.city} values={CITIES} onChange={(city) => patch({city})}/>
                <Choice label="体验时长" value={request.duration} values={DURATIONS} onChange={(duration) => patch({duration})}/>
                <Choice label="同行身份" value={request.identity} values={IDENTITIES} onChange={(identity) => patch({identity})}/>
                <Choice label="方案风格" value={request.output_style} values={STYLES} onChange={(output_style) => patch({output_style})}/>
                {request.scene === "内容创作" && <Choice label="内容形式" value={request.task_type === "video" ? "短视频" : "图文"} values={["图文","短视频"]} onChange={(form) => patch({task_type:form === "短视频" ? "video" : "social"})}/>}
                <div className="composer-model-note"><ShieldCheck size={16}/> 实际开放时间、票价及预约信息以官方发布为准。</div>
                </div>
              </details>
            </div>
            <div className="composer-actions">
              <span className="keyboard-hint">Ctrl / ⌘ + Enter 生成</span>
              {busy ? <button className="button button-stop" type="button" onClick={() => { controller.current?.abort(); setBusy(false); setStage("已取消生成"); }}><X size={17}/> 取消生成</button>
                : <button id="generate-submit" className="button button-dark generate-button" type="submit" disabled={model.mode === "auto" && status?.platform_ready === false}>生成方案 <Send size={17} aria-hidden="true"/></button>}
            </div>
            {statusError && <div className="service-inline-notice" role="status">连接状态检测暂时失败，请刷新重试；个人 API 仍可在设置中配置。</div>}
            {model.mode === "auto" && status?.platform_ready === false && <div className="service-inline-notice" role="status">平台服务暂不可用，你可以在 <button type="button" onClick={() => setShowSettings(true)}>AI 设置</button> 中使用个人 API。</div>}
            {error && <div className="studio-error" id="studio-error" role="alert"><CircleHelp size={17} aria-hidden="true"/><span>{error}</span><button type="button" onClick={() => setError("")} aria-label="关闭错误提示"><X size={17}/></button></div>}
          </form>

          {(busy || result) && <section className="output-panel ux-results" id="proposal" aria-labelledby="result-title">
            <div className="panel-heading output-heading">
              <div><h2 id="result-title">{busy ? "正在生成" : "生成结果"}</h2></div>
              {result && !busy && <div className="result-ready"><Check size={14} aria-hidden="true"/> 已完成{result.metrics && ` · 首字 ${(result.metrics.first_token_ms ?? 0)/1000}s / 总耗时 ${(result.metrics.total_ms/1000).toFixed(1)}s`}</div>}
            </div>
            {busy && <div className="stream-stage" role="status" aria-live="polite"><LoaderCircle className="spin" size={18} aria-hidden="true"/><div><strong>{stage}</strong><span>生成过程中可取消，内容将逐步显示。</span></div></div>}
            {shownAnswer ? <div className="result-view">
              <div className="result-summary"><div className="result-summary-badge">{busy ? request.scene : result?.request.scene || request.scene}</div><div className="result-summary-text"><h3>{busy ? request.raw_request : result?.request.raw_request || request.raw_request}</h3><p><MapPin size={14}/>{result?.request.city || request.city}<span>·</span><Clock3 size={14}/>{result?.request.duration || request.duration}<span>·</span>{result?.request.identity || request.identity}</p></div></div>
              <div className="result-tabs" role="group" aria-label="结果内容导航"><button aria-pressed={activeTab === "all"} className={activeTab === "all" ? "active" : ""} onClick={() => setActiveTab("all")} type="button">完整方案</button>{sections.slice(0,5).map((section,index)=><button key={index} type="button" aria-pressed={activeTab === String(index)} className={activeTab === String(index) ? "active" : ""} onClick={() => setActiveTab(String(index))}>{section.title}</button>)}<button type="button" aria-pressed={activeTab === "sources"} className={activeTab === "sources" ? "active" : ""} onClick={() => setActiveTab("sources")}>资料来源</button></div>
              <MarkdownDoc content={selectedContent || "暂无可展示的检索资料。"} />
              {!busy && result && <div className="result-downloads"><span>保存结果</span><div><button type="button" onClick={() => void copyResult()}><Copy size={15} aria-hidden="true"/>复制正文</button>{(["docx","md","txt"] as const).map((format)=><button disabled={downloadBusy} type="button" onClick={() => void download(format)} key={format}><Download size={15} aria-hidden="true"/>{format === "docx" ? "Word" : format.toUpperCase()}</button>)}</div></div>}
            </div> : busy ? <div className="result-skeleton" aria-hidden="true"><span/><span/><span/><span/></div> : null}
          </section>}

          {result && !busy && <section className="revision-panel ux-revision" aria-labelledby="revision-title"><div className="panel-heading"><div><h2 id="revision-title">调整这份方案</h2></div><RefreshCw size={21} strokeWidth={1.5}/></div><div className="revision-chips">{REVISIONS.map((item)=><button type="button" key={item} onClick={() => void run("revise",item)}>{item}<ArrowUpRight size={14}/></button>)}</div><div className="revision-compose"><textarea rows={2} maxLength={500} value={revision} onChange={(e) => setRevision(e.target.value)} placeholder="例如：减少景点数量、增加适合拍照的体验、加入更多岭南美食…" aria-label="自定义修改要求"/><button className="button button-dark" type="button" disabled={!revision.trim()} onClick={() => void run("revise")}><Send size={16}/> 提交修改</button></div>{result.revisions.length > 0 && <details className="revision-history"><summary>查看历史调整（{result.revisions.length} 次）</summary>{result.revisions.map((entry,i)=><p key={i}>{entry.createdAt} · {entry.instruction}</p>)}</details>}</section>}
          <div className="studio-bottom-disclaimer"><BookOpen size={16} aria-hidden="true"/><p>内容由 AI 辅助生成。开放时间、预约与票价请以官方信息为准。</p></div>
          <p className="studio-notice" role="status" aria-live="polite">{notice}</p>
        </div>
      </div>
    </main>
    <footer className="studio-footer"><div className="container"><span>粤见非遗</span><Link href="/">返回首页 <ArrowLeft size={15} aria-hidden="true"/></Link></div></footer>
    {showSettings && <ModelSettings model={model} setModel={setModel} platformReady={status?.platform_ready} onClose={closeSettings}/>}
    {drawerOpen && <button aria-label="关闭侧边栏" className="mobile-side-overlay" onClick={() => setDrawerOpen(false)} type="button"/>}
  </>;
}
