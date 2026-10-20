"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowRight, ArrowUpRight, BookOpen, Compass, GraduationCap, HeartHandshake, PenLine, Sparkles, MapPin, ShieldCheck } from "lucide-react";
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
    if (!prompt.trim()) { setError("先简单描述你的需求，或者使用下面的示例。"); return; }
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
      <main className="fast-main">
        <section className="fast-hero">
          <div className="fast-hero-inner container">
            <div className="fast-intro">
              <span className="fast-eyebrow"><span className="fast-mark"/> 广东非遗 · AI 文化体验</span>
              <h1>想了解岭南文化，<br/><em>从这里开始。</em></h1>
              <p>路线规划、研学、亲子体验或内容创作。<br/>告诉我们你的想法，生成一份可使用的方案。</p>
              <div className="fast-confidence"><ShieldCheck size={16}/> 五种体验方式 · 结果可修改、可导出</div>
            </div>
            <div className="fast-hero-art" role="img" aria-label="广东传统文化与非遗主题插画"><span>YUEJIAN · 发现广东非遗</span></div>
          </div>
        </section>

        <section className="fast-workspace container" id="start">
          <div className="fast-workspace-heading">
            <div><span className="fast-step">开始体验</span><h2>你今天想做什么？</h2></div>
            <Link href="/studio" className="fast-text-link">直接打开工作台 <ArrowUpRight size={16}/></Link>
          </div>
          <div className="fast-task-grid" role="group" aria-label="选择体验方式">
            {tasks.map((task) => {
              const Icon = task.icon;
              return <button type="button" key={task.key}
                aria-pressed={scene === task.key}
                className={`fast-task ${scene === task.key ? "is-active" : ""}`}
                onClick={() => {setScene(task.key);setError("");}}>
                <Icon size={21} strokeWidth={1.7}/>
                <strong>{task.label}</strong>
                <span>{task.desc}</span>
              </button>;
            })}
          </div>

          <form className="fast-prompt-box" onSubmit={(event) => {event.preventDefault();start();}}>
            <label htmlFor="fast-request">描述你的想法</label>
            <textarea id="fast-request" maxLength={1200} rows={3} value={prompt} onChange={(event)=>{setPrompt(event.target.value);setError("");}}
              placeholder={selected.example}/>
            <div className="fast-form-bottom">
              <div className="fast-city"><MapPin size={16}/><label htmlFor="fast-city">城市</label>
                <select id="fast-city" value={city} onChange={(event)=>setCity(event.target.value)}>
                  {CITIES.map((item)=><option key={item} value={item}>{item}</option>)}
                </select>
              </div>
              <button type="submit" className="fast-submit">开始生成 <ArrowRight size={18}/></button>
            </div>
            {error && <p className="fast-form-error" role="alert">{error}</p>}
          </form>
          <div className="fast-examples">
            <span><Sparkles size={15}/> 没有思路？试试</span>
            {tasks.slice(0,3).map((task)=><button key={task.key} type="button" onClick={()=>{setScene(task.key);setPrompt(task.example);setCity("自动判断");setError("");}}>{task.label}示例 <ArrowUpRight size={13}/></button>)}
          </div>
        </section>

        <section className="fast-about container" aria-label="关于结果">
          <div><strong>一份方案，持续完善</strong><span>生成后可按需要调整行程、修改文字，或保存为 Word。</span></div>
          <Link href="/studio">查看工作台 <ArrowRight size={17}/></Link>
        </section>
        <footer className="fast-footer"><div className="container"><span>粤见非遗 · YUEJIAN</span><span>文化内容辅助生成；开放时间与票价请以官方信息为准。</span></div></footer>
      </main>
    </>
  );
}
