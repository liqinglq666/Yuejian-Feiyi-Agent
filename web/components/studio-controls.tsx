"use client";
import { Check, ChevronDown, ShieldCheck, X } from "lucide-react";
import { memo, useEffect, useRef } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { MODEL_PROVIDERS, type ModelOptions } from "@/lib/types";

export function Choice({ label, value, values, onChange }: {
  label: string; value: string; values: readonly string[]; onChange: (value: string) => void;
}) {
  return <label className="field"><span>{label}</span><span className="select-wrap">
    <select value={value} onChange={(event) => onChange(event.target.value)}>
      {values.map((item) => <option key={item} value={item}>{item}</option>)}
    </select><ChevronDown size={16} aria-hidden="true"/>
  </span></label>;
}

export function ModelSettings({ model, setModel, onClose, platformReady }: {
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
        <Choice label="服务商" value={model.provider} values={Object.keys(MODEL_PROVIDERS)} onChange={(provider) => patch({ provider, api_key:"", ...MODEL_PROVIDERS[provider as keyof typeof MODEL_PROVIDERS] })}/>
        <label className="field"><span>API Key（仅保留在当前页面）</span><input type="password" name="private_api_key" autoComplete="new-password" spellCheck={false} value={model.api_key} placeholder="sk-••••••••••" onChange={(e) => patch({ api_key:e.target.value })}/></label>
        <label className="field"><span>Base URL</span><input name="private_base_url" type="url" autoComplete="off" spellCheck={false} value={model.base_url} placeholder="https://api.example.com/v1" onChange={(e) => patch({ base_url:e.target.value })}/></label>
        <label className="field"><span>模型名称</span><input name="private_model_name" autoComplete="off" spellCheck={false} value={model.model_name} placeholder="模型 ID" onChange={(e) => patch({ model_name:e.target.value })}/></label>
        {model.provider === "自定义 OpenAI-compatible" && <p className="settings-description">为保护服务安全，线上站点只接受已配置的可信 API 域名；其他服务需由站点管理员加入允许列表。</p>}
        <button className="clear-key" type="button" onClick={() => patch({ api_key:"", mode:"auto" })}>清除 API Key 并返回平台服务</button>
      </>}
      <label className="field"><span>生成语言灵活度 <b>{model.temperature.toFixed(2)}</b></span><input type="range" min=".1" max="1" step=".05" value={model.temperature} onChange={(e) => patch({temperature:Number(e.target.value)})}/></label>
      <div className="settings-security"><ShieldCheck size={17} aria-hidden="true"/> 个人 API Key 不会存入浏览器本地存储。</div>
      <button className="button button-dark settings-done" type="button" onClick={onClose}>完成设置 <Check size={17}/></button>
    </section>
  </div>;
}

export const MarkdownDoc = memo(function MarkdownDoc({ content }: { content: string }) {
  return <div className="markdown-document"><ReactMarkdown remarkPlugins={[remarkGfm]} skipHtml>{content}</ReactMarkdown></div>;
});
