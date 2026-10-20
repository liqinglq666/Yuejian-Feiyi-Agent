"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowRight, BookOpen, Compass, GraduationCap, HeartHandshake, PenLine, Sparkles, MapPin } from "lucide-react";
import { SiteHeader } from "@/components/site-header";
import { CITIES, type Scene, type TaskRequest, DEFAULT_REQUEST } from "@/lib/types";

const tasks = [
  { key:"游客路线", label:"规划路线", desc:"一日游 · 城市漫游", icon: Compass, example:"帮我规划广州一天的粤剧和广绣体验路线，步行友好。" },
  { key:"学生研学", label:"设计研学", desc:"课程 · 观察任务", icon: GraduationCap, example:"为初中生设计潮汕英歌舞主题的研学活动。" },
  { key:"亲子体验", label:"亲子体验", desc:"亲子 · 手作活动", icon: HeartHandshake, example:"带孩子去佛山看醒狮和陶塑，安排轻松的半天体验。" },
  { key:"内容创作", label:"内容创作", desc:"图文 · 视频脚本", icon: PenLine, example:"写一篇介绍香云纱制作工艺的小红书图文。" },
  { key:"非遗问答", label:"了解非遗", desc:"知识 · 文化故事", icon: BookOpen, example:"广绣有哪些典型针法？适合怎样的初学者？" },
] as const;

export default function HomePage() {
  const router = useRouter();
  const [scene, setScene] = useState<Scene>("游客路线");
  const [prompt, setPrompt] = useState("");
  const [city, setCity] = useState("自动判断");
  const [error, setError] = useState("");
  const selected = tasks.find((item) => item.key === scene) ?? tasks[0];

  function start() {
    if (!prompt.trim()) { setError("先写一句你的需求，也可以点击下方示例。"); document.getElementById("fast-request")?.focus(); return; }
    const draft: TaskRequest = {
      ...DEFAULT_REQUEST, scene, raw_request:prompt.trim(), city,
      task_type:scene === "内容创作" ? "social" : null,
    };
    try {
      sessionStorage.setItem("yuejian-launch-draft", JSON.stringify(draft));
    } catch {
      // Session storage is optional; the studio remains usable without it.
      const query = new URLSearchParams({ scene, prompt:prompt.trim(), city });
      router.push(`/studio?${query.toString()}`);
      return;
    }
    router.push("/studio");
  }

  return (
    <>
      <SiteHeader />
      <main className="fast-main" id="main-content">
        <div className="container fast-workspace" id="start">
          <header className="fast-heading">
            <div>
              <p className="fast-overline">粤见非遗 / 广东文化体验</p>
              <h1>找到适合你的非遗体验</h1>
              <p className="fast-subhead">选一个方向，说说你的想法。路线、研学、亲子活动和内容创作，都能从这里开始。</p>
            </div>
            <div className="fast-aside"><span>从想法到方案</span><strong>几分钟，认识一座城里的手艺。</strong></div>
          </header>
          <section aria-labelledby="fast-scene-heading" className="fast-scene-section">
            <h2 id="fast-scene-heading" className="fast-section-label">1. 选择体验方式</h2>
            <div className="fast-task-grid" role="group" aria-label="选择体验方式">
              {tasks.map((task) => {
                const Icon = task.icon;
                return <button type="button" key={task.key} aria-pressed={scene === task.key}
                  className={"fast-task " + (scene === task.key ? "is-active" : "")}
                  onClick={() => {setScene(task.key);setError("");}}>
                  <Icon size={22} strokeWidth={1.8} aria-hidden="true"/>
                  <strong>{task.label}</strong><span>{task.desc}</span>
                </button>;
              })}
            </div>
          </section>
          <section aria-labelledby="fast-prompt-heading" className="fast-request-section">
            <h2 id="fast-prompt-heading" className="fast-section-label">2. 描述你的需求</h2>
            <form className="fast-prompt-box" onSubmit={(event) => {event.preventDefault();start();}}>
              <label htmlFor="fast-request" className="fast-label">你希望体验什么？</label>
              <textarea id="fast-request" name="request" autoComplete="off" maxLength={1200} rows={4} value={prompt}
                aria-invalid={!!error} aria-describedby={error ? "fast-form-error" : "fast-prompt-help"}
                onChange={(event)=>{setPrompt(event.target.value);setError("");}}
                placeholder={selected.example + "…"}/>
              {error && <p id="fast-form-error" className="fast-form-error" role="alert">{error}</p>}
              <div className="fast-form-bottom">
                <div className="fast-city"><MapPin size={17} aria-hidden="true"/><label htmlFor="fast-city">城市（可选）</label>
                  <select id="fast-city" name="city" value={city} onChange={(event)=>setCity(event.target.value)}>
                    {CITIES.map((item)=><option key={item} value={item}>{item}</option>)}
                  </select>
                </div>
                <p id="fast-prompt-help" className="fast-help">{prompt.length}/1200 字</p>
                <button type="submit" className="fast-submit">下一步：生成方案 <ArrowRight size={18} aria-hidden="true"/></button>
              </div>
            </form>
            <div className="fast-examples" aria-label="示例需求">
              <span><Sparkles size={15} aria-hidden="true"/> 没有思路？</span>
              {tasks.slice(0,3).map((task)=><button key={task.key} type="button" onClick={()=>{setScene(task.key);setPrompt(task.example);setCity("自动判断");setError("");document.getElementById("fast-request")?.focus();}}>{task.label}示例</button>)}
            </div>
          </section>
          <p className="fast-hint">生成结果支持继续修改及导出 Word；开放时间、票价等实时信息请以官方公告为准。</p>
        </div>
        <footer className="fast-footer"><div className="container"><strong>粤见非遗</strong><span>让文化更易走近。</span></div></footer>
      </main>
    </>
  );
}
