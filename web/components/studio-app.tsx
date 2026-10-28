"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { ArrowLeft, BookOpen, Check, ChevronDown, CircleHelp, Menu, Plus, Send, Settings2, ShieldCheck, X } from "lucide-react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { SiteHeader } from "@/components/site-header";
import { SCENES } from "@/components/studio-data";
import { Choice, ModelSettings } from "@/components/studio-controls";
import { StudioSidebar } from "@/components/studio-sidebar";
import { StudioResults } from "@/components/studio-results";
import { exportProposal, splitSections, streamProposal } from "@/lib/api";
import {
  CITIES, DEFAULT_MODEL, DEFAULT_REQUEST, DURATIONS, IDENTITIES, INTERESTS,
  STYLES,
  type AppStatus, type ModelOptions, type Plan, type Scene, type StreamEvent, type TaskRequest,
} from "@/lib/types";



const EXAMPLES = [
  { title:"广州 · 一日非遗漫游", scene:"游客路线" as Scene, city:"广州", duration:"一天", identity:"外地游客", text:"我第一次来广州，有一天时间，想体验岭南非遗文化，适合拍照并且路线轻松。", interests:["粤剧","岭南建筑"] },
  { title:"佛山 · 周末亲子手作", scene:"亲子体验" as Scene, city:"佛山", duration:"周末", identity:"亲子家庭", text:"周末带孩子去佛山，想体验醒狮和石湾陶塑，节奏轻松一点。", interests:["醒狮","陶塑"] },
  { title:"校园 · 研学观察记录", scene:"学生研学" as Scene, city:"自动判断", duration:"一天", identity:"学生研学", text:"我是高中生，要做一份广东非遗研学报告，请围绕粤剧、醒狮和广绣设计任务卡和观察记录表。", interests:["粤剧","醒狮","广绣"] },
  { title:"潮汕 · 英歌舞图文", scene:"内容创作" as Scene, city:"汕头", duration:"不限", identity:"内容创作者", text:"帮我写一篇适合小红书发布的潮汕英歌舞图文，语言生动，附上配图建议和标签。", interests:["拍照"] },
  { title:"广绣 · 针法入门问答", scene:"非遗问答" as Scene, city:"广州", duration:"不限", identity:"自动匹配", text:"广绣有哪些典型针法？各有什么特点？第一次接触广绣的人应该怎样入门？请用通俗语言讲解，并说明可靠的信息来源。", interests:["广绣"] },
];
const MAX_RECENTS = 3;
const isScene = (text: string | null): text is Scene => !!text && SCENES.some((scene) => scene.key === text);
const makeId = () => typeof crypto !== "undefined" && "randomUUID" in crypto ? crypto.randomUUID() : String(Date.now());



export function StudioApp() {
  const params = useSearchParams();
  const [request, setRequest] = useState<TaskRequest>(() => {
    const selectedScene = params.get("scene");
    const selectedCity = params.get("city");
    const selectedPrompt = params.get("prompt");
    return {
      ...DEFAULT_REQUEST,
      ...(isScene(selectedScene) ? { scene:selectedScene, task_type:selectedScene === "内容创作" ? "social" as const : selectedScene === "非遗问答" ? "qa" as const : null } : {}),
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
  const [staleResult, setStaleResult] = useState(false);
  const [runRequest, setRunRequest] = useState<TaskRequest | null>(null);
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
  const pendingHomepageLaunch = useRef(params.get("autostart") === "1" && isScene(params.get("scene")) && !!params.get("prompt")?.trim());
  const closeSettings = useCallback(() => setShowSettings(false), []);
  const pendingStream = useRef("");
  const streamTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const flushStream = useCallback((text: string, replace = false) => {
    pendingStream.current = replace ? text : pendingStream.current + text;
    if (streamTimer.current !== null) return;
    streamTimer.current = setTimeout(() => {
      setStream(pendingStream.current);
      streamTimer.current = null;
    }, 190);
  }, []);
  const resetStream = useCallback(() => {
    if (streamTimer.current !== null) clearTimeout(streamTimer.current);
    streamTimer.current = null;
    pendingStream.current = "";
    setStream("");
  }, []);
  const refreshStatus = useCallback(async () => {
    for (let attempt = 0; attempt < 3; attempt++) {
      try {
        const response = await fetch("/api/v1/status", {cache:"no-store",signal:AbortSignal.timeout(6500)});
        if (!response.ok) throw Error("status unavailable");
        const info = await response.json() as AppStatus;
        setStatus(info); setStatusError(false);
        return;
      } catch {
        if (attempt < 2) await new Promise((resolve) => setTimeout(resolve, 500 * (attempt + 1)));
      }
    }
    setStatusError(true);
  }, []);


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
    queueMicrotask(() => void refreshStatus());
    // Defer hydration to a callback; initial render stays SSR-safe.
    queueMicrotask(() => {
      try {
        const draft = sessionStorage.getItem("yuejian-launch-draft");
        const launchRequested = sessionStorage.getItem("yuejian-start-immediately") === "1";
        sessionStorage.removeItem("yuejian-start-immediately");
        if (draft) {
          sessionStorage.removeItem("yuejian-launch-draft");
          const selected = JSON.parse(draft) as TaskRequest;
          if (isScene(selected.scene) && typeof selected.raw_request === "string" && selected.raw_request.trim() && selected.raw_request.length <= 1200) {
            pendingHomepageLaunch.current = launchRequested;
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
    return () => { controller.current?.abort(); if (streamTimer.current !== null) clearTimeout(streamTimer.current); };
  }, [refreshStatus]);

  useEffect(() => {
    if (!hydrated || !pendingHomepageLaunch.current) return;
    if (statusError) {
      pendingHomepageLaunch.current = false;
      queueMicrotask(() => setNotice("服务状态暂时无法核实，需求已保留。请重新检查连接后手动生成。"));
      return;
    }
    if (!status) return;
    pendingHomepageLaunch.current = false;
    if (!status.platform_ready) {
      queueMicrotask(() => setNotice("平台服务暂不可用，需求已保留。你可以在 AI 设置中连接个人 API。"));
      return;
    }
    queueMicrotask(() => document.getElementById("generate-submit")?.click());
  }, [hydrated, status, statusError]);

  useEffect(() => {
    if (!hydrated) return;
    try { sessionStorage.setItem("yuejian-recent-plans-v2", JSON.stringify(recents)); }
    catch { /* Storage is a convenience, not a prerequisite. */ }
  }, [recents, hydrated]);

  function patch(fields: Partial<TaskRequest>) { setRequest((prev) => ({ ...prev, ...fields })); }
  function selectScene(scene: Scene) {
    setRequest((prev) => {
      if (prev.scene === scene) return prev;
      const oldExample = EXAMPLES.some((item) => item.scene === prev.scene && item.text === prev.raw_request);
      const identity = scene === "学生研学" ? "学生研学" : scene === "亲子体验" ? "亲子家庭"
        : scene === "内容创作" ? "内容创作者" : "自动匹配";
      const output_style = scene === "学生研学" ? "研学报告" : scene === "非遗问答" ? "专业讲解" : "清晰实用";
      return {
        ...prev, scene, identity, output_style,
        task_type: scene === "内容创作" ? "social" : scene === "非遗问答" ? "qa" : null,
        // Switching scenarios should not silently carry an unrelated example.
        raw_request: oldExample ? "" : prev.raw_request,
        interests: oldExample ? [] : prev.interests,
      };
    });
    setDrawerOpen(false);
  }
  function applyExample(index: number) {
    const item = EXAMPLES[index];
    setRequest({
      ...DEFAULT_REQUEST, scene:item.scene, raw_request:item.text, city:item.city,
      duration:item.duration, identity:item.identity, interests:item.interests,
      task_type: item.scene === "内容创作" ? "social" : item.scene === "非遗问答" ? "qa" : null,
    });
    setError("");
  }
  function startNew() {
    if ((request.raw_request.trim() || result) && !window.confirm("开始新方案？当前编辑内容将清空，已生成的方案仍可在最近记录中查看。")) return;
    controller.current?.abort();
    pendingHomepageLaunch.current = false;
    setBusy(false); setRequest(DEFAULT_REQUEST); setResult(null); setStaleResult(false); setRunRequest(null); resetStream(); setError("");
    setRevision(""); setActiveTab("all"); setDrawerOpen(false); setNotice("");
    requestAnimationFrame(() => inputRef.current?.focus());
  }
  function restorePlan(plan: Plan) {
    if (busy) return;
    setResult(plan); setStaleResult(false); setRunRequest(null); setRequest(plan.request); resetStream(); setActiveTab("all");
    setDrawerOpen(false); setError(""); setNotice("");
    requestAnimationFrame(() => document.getElementById("proposal")?.scrollIntoView({behavior:"smooth",block:"start"}));
  }

  function savePlan(plan: Plan) {
    setRecents((prev) => [plan, ...prev.filter((entry) => entry.id !== plan.id)].slice(0, MAX_RECENTS));
    setResult(plan);
    setStaleResult(false);
  }

  async function run(kind: "generate" | "revise", preset?: string) {
    if (busy) return;
    pendingHomepageLaunch.current = false;
    if (kind === "revise" && !result) return;
    if (kind === "generate" && !request.raw_request.trim()) { setError("请先写下你的需求，或者使用示例。"); inputRef.current?.focus(); return; }
    if (model.mode === "user" && (!model.api_key.trim() || !model.base_url.trim() || !model.model_name.trim())) { setError("请先在 AI 服务设置中填写完整的个人 API 信息。"); setShowSettings(true); return; }
    setBusy(true); setError(""); setNotice(""); resetStream(); setActiveTab("all"); setStage("正在准备你的方案…");
    const abortController = new AbortController();
    controller.current = abortController;
    const previous = result;
    setStaleResult(kind === "generate" && previous !== null);
    setRunRequest(kind === "revise" && previous ? previous.request : request);
    try {
      await streamProposal(
        kind,
        kind === "revise" && previous ? previous.request : request,
        model,
        kind === "revise" && previous ? { current_answer:previous.answer, ...(preset ? {preset} : {instruction:revision.trim()}) } : null,
        (event: StreamEvent) => {
          if (abortController.signal.aborted || controller.current !== abortController) return;
          if (event.type === "stage") setStage(event.label);
          if (event.type === "snapshot") flushStream(event.text, true);
          if (event.type === "delta") flushStream(event.text);
          if (event.type === "failure") { setError(event.message); resetStream(); }
          if (event.type === "complete") {
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
            resetStream(); setActiveTab("all"); setRevision("");
            requestAnimationFrame(() => document.getElementById("proposal")?.scrollIntoView({behavior:"smooth",block:"start"}));
          }
        },
        abortController.signal,
      );
    } catch (err) {
      if (!abortController.signal.aborted) setError(err instanceof Error ? err.message : "请求失败，请稍后重试。");
    } finally {
      if (controller.current === abortController) {
        setBusy(false);
        setRunRequest(null);
        controller.current = null;
      }
    }
  }

  function cancelGeneration() {
    const active = controller.current;
    controller.current = null;
    resetStream();
    setRunRequest(null);
    setBusy(false);
    setStage("已取消生成");
    setNotice("已停止接收内容；模型服务端可能已产生部分用量。");
    // Settle UI state first; the pending network operation must not keep the
    // cancel button or mobile controls locked while abort is dispatched.
    window.setTimeout(() => active?.abort(), 0);
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
  const sections = useMemo(() => splitSections(shownAnswer), [shownAnswer]);
  const selectedContent = activeTab === "all" ? shownAnswer
    : activeTab === "sources" ? (busy ? "" : result?.sources ?? "") : sections[Number(activeTab)]?.content ?? shownAnswer;
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
        <StudioSidebar
          drawerOpen={drawerOpen} busy={busy} request={request} recents={recents}
          sidebarRef={sidebarRef} sidebarCloseRef={sidebarCloseRef}
          onClose={() => setDrawerOpen(false)} onSceneChange={selectScene} onRestore={restorePlan}
        />

        <div className="studio-main">
          <div className="studio-heading"><div><h1>生成非遗体验方案</h1><p>选择体验类型、描述需求，即可开始。</p></div><div className="studio-heading__art" aria-hidden="true"/><button type="button" className="studio-new-button" onClick={startNew} disabled={busy}><Plus size={17} aria-hidden="true"/> 新方案</button></div>
          <div className="mobile-scene-bar"><button type="button" onClick={() => setDrawerOpen(true)} aria-expanded={drawerOpen} aria-controls="studio-scenes"><Menu size={17}/> {visibleScene.name} <ChevronDown size={15}/></button><button type="button" onClick={startNew} disabled={busy}><Plus size={17}/> 新方案</button></div>

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
              {busy ? <button className="button button-stop" type="button" onClick={cancelGeneration}><X size={17}/> 取消生成</button>
                : <button id="generate-submit" className="button button-dark generate-button" type="submit" disabled={model.mode === "auto" && status?.platform_ready === false}>生成方案 <Send size={17} aria-hidden="true"/></button>}
            </div>
            {statusError && <div className="service-inline-notice" role="status">连接状态检测暂时失败，草稿会保留。<button type="button" onClick={() => void refreshStatus()}>重新检查连接</button></div>}
            {model.mode === "auto" && status?.platform_ready === false && <div className="service-inline-notice" role="status">平台服务暂不可用，你可以在 <button type="button" onClick={() => setShowSettings(true)}>AI 设置</button> 中使用个人 API，或 <button type="button" onClick={() => void refreshStatus()}>重新检查状态</button>。</div>}
            {error && <div className="studio-error" id="studio-error" role="alert"><CircleHelp size={17} aria-hidden="true"/><span>{error}</span><button type="button" onClick={() => setError("")} aria-label="关闭错误提示"><X size={17}/></button></div>}
          </form>

          <StudioResults
            busy={busy} staleResult={staleResult} result={result} request={busy ? runRequest ?? request : request} stage={stage}
            shownAnswer={shownAnswer} selectedContent={selectedContent} sections={sections}
            activeTab={activeTab} onSelectTab={setActiveTab} downloadBusy={downloadBusy}
            onCopy={copyResult} onDownload={download} revision={revision}
            onRevisionChange={setRevision}
            onQuickRevision={(preset) => run("revise", preset)}
            onSubmitRevision={() => run("revise")}
          />
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
