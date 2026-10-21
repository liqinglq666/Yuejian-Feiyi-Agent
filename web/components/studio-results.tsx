"use client";
import { ArrowUpRight, Check, Clock3, Copy, Download, LoaderCircle, MapPin, RefreshCw, Send } from "lucide-react";
import { MarkdownDoc } from "./studio-controls";
import type { Plan, TaskRequest } from "@/lib/types";

const REVISIONS = ["压缩成半天", "更适合亲子", "生成小红书文案", "生成短视频脚本", "加研学记录表"];

type Props = {
  busy: boolean;
  result: Plan | null;
  request: TaskRequest;
  stage: string;
  shownAnswer: string;
  selectedContent: string;
  sections: { title: string; content: string }[];
  activeTab: string;
  onSelectTab: (value: string) => void;
  downloadBusy: boolean;
  onCopy: () => void | Promise<void>;
  onDownload: (format: "md" | "txt" | "docx") => void | Promise<void>;
  revision: string;
  onRevisionChange: (text: string) => void;
  onQuickRevision: (preset: string) => void | Promise<void>;
  onSubmitRevision: () => void | Promise<void>;
};

export function StudioResults({ busy, result, request, stage, shownAnswer, selectedContent, sections, activeTab, onSelectTab, downloadBusy, onCopy, onDownload, revision, onRevisionChange, onQuickRevision, onSubmitRevision }: Props) {
  return (
    <>
{(busy || result) && <section className="output-panel ux-results" id="proposal" aria-labelledby="result-title">
            <div className="panel-heading output-heading">
              <div><h2 id="result-title">{busy ? "正在生成" : "生成结果"}</h2></div>
              {result && !busy && <div className="result-ready"><Check size={14} aria-hidden="true"/> 已完成{result.metrics && ` · 首字 ${(result.metrics.first_token_ms ?? 0)/1000}s / 总耗时 ${(result.metrics.total_ms/1000).toFixed(1)}s`}</div>}
            </div>
            {busy && <div className="stream-stage" role="status" aria-live="polite"><LoaderCircle className="spin" size={18} aria-hidden="true"/><div><strong>{stage}</strong><span>生成过程中可取消，内容将逐步显示。</span></div></div>}
            {shownAnswer ? <div className="result-view">
              <div className="result-summary"><div className="result-summary-badge">{busy ? request.scene : result?.request.scene || request.scene}</div><div className="result-summary-text"><h3>{busy ? request.raw_request : result?.request.raw_request || request.raw_request}</h3><p><MapPin size={14}/>{result?.request.city || request.city}<span>·</span><Clock3 size={14}/>{result?.request.duration || request.duration}<span>·</span>{result?.request.identity || request.identity}</p></div></div>
              <div className="result-tabs" role="group" aria-label="结果内容导航"><button aria-pressed={activeTab === "all"} className={activeTab === "all" ? "active" : ""} onClick={() => onSelectTab("all")} type="button">完整方案</button>{sections.slice(0,5).map((section,index)=><button key={index} type="button" aria-pressed={activeTab === String(index)} className={activeTab === String(index) ? "active" : ""} onClick={() => onSelectTab(String(index))}>{section.title}</button>)}<button type="button" aria-pressed={activeTab === "sources"} className={activeTab === "sources" ? "active" : ""} onClick={() => onSelectTab("sources")}>资料来源</button></div>
              <MarkdownDoc content={selectedContent || "暂无可展示的检索资料。"} />
              {!busy && result && <div className="result-downloads"><span>保存结果</span><div><button type="button" onClick={() => void onCopy()}><Copy size={15} aria-hidden="true"/>复制正文</button>{(["docx","md","txt"] as const).map((format)=><button disabled={downloadBusy} type="button" onClick={() => void onDownload(format)} key={format}><Download size={15} aria-hidden="true"/>{format === "docx" ? "Word" : format.toUpperCase()}</button>)}</div></div>}
            </div> : busy ? <div className="result-skeleton" aria-hidden="true"><span/><span/><span/><span/></div> : null}
          </section>}

          {result && !busy && <section className="revision-panel ux-revision" aria-labelledby="revision-title"><div className="panel-heading"><div><h2 id="revision-title">调整这份方案</h2></div><RefreshCw size={21} strokeWidth={1.5}/></div><div className="revision-chips">{REVISIONS.map((item)=><button type="button" key={item} onClick={() => void onQuickRevision(item)}>{item}<ArrowUpRight size={14}/></button>)}</div><div className="revision-compose"><textarea rows={2} maxLength={500} value={revision} onChange={(e) => onRevisionChange(e.target.value)} placeholder="例如：减少景点数量、增加适合拍照的体验、加入更多岭南美食…" aria-label="自定义修改要求"/><button className="button button-dark" type="button" disabled={!revision.trim()} onClick={() => void onSubmitRevision()}><Send size={16}/> 提交修改</button></div>{result.revisions.length > 0 && <details className="revision-history"><summary>查看历史调整（{result.revisions.length} 次）</summary>{result.revisions.map((entry,i)=><p key={i}>{entry.createdAt} · {entry.instruction}</p>)}</details>}</section>}
    </>
  );
}
