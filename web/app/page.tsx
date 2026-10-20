"use client";

import Image from "next/image";
import { useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowRight, ArrowUpRight, BookOpen, Compass, GraduationCap, HeartHandshake, MapPin, PenLine, Sparkles } from "lucide-react";
import { SiteHeader } from "@/components/site-header";
import { CITIES, DEFAULT_REQUEST, type Scene, type TaskRequest } from "@/lib/types";

const tasks = [
  { key: "游客路线", label: "文化漫游", icon: Compass, example: "想在潮州待一天，逛老城、体验工夫茶，路线希望轻松一些。" },
  { key: "学生研学", label: "研学活动", icon: GraduationCap, example: "设计一场适合初中生的粤剧研学活动，包含观察任务和讨论。" },
  { key: "亲子体验", label: "亲子探索", icon: HeartHandshake, example: "周末带孩子到佛山了解醒狮和陶塑，安排适合亲子的半天体验。" },
  { key: "内容创作", label: "文化创作", icon: PenLine, example: "写一篇适合社交媒体发布的香云纱介绍，语言生动自然。" },
  { key: "非遗问答", label: "非遗问答", icon: BookOpen, example: "广绣和潮绣有什么区别？分别适合从哪里入门？" },
] as const;

const inspirations: { title: string; kicker: string; description: string; city: string; scene: Scene; prompt: string; image: string; alt: string }[] = [
  { kicker: "城市漫游", title: "在潮州，把一天交给老街", description: "工夫茶、牌坊街与街巷里的故事", city: "潮州", scene: "游客路线", prompt: "第一次去潮州，想安排一天的古城非遗漫游，体验工夫茶和传统街巷，路线不要太赶。", image: "/heritage/inspiration-festival.webp", alt: "传统建筑与民俗巡游的水彩插画" },
  { kicker: "亲子探索", title: "听见龙舟鼓点", description: "从节日热闹走向传统文化", city: "广州", scene: "亲子体验", prompt: "想带孩子了解广东龙舟文化，设计一个有故事、有动手互动的半天亲子体验。", image: "/heritage/inspiration-dragon-boat.webp", alt: "龙舟竞渡与水乡节庆的彩色插画" },
  { kicker: "文化研学", title: "坐下来，看一场好戏", description: "从舞台角色认识表演艺术", city: "广州", scene: "学生研学", prompt: "为初中生设计一场以广东传统戏曲为主题的研学体验，包含观察表和演出礼仪。", image: "/heritage/inspiration-theatre.webp", alt: "传统戏台表演与观众的民俗插画" },
];

export default function HomePage() {
  const router = useRouter();
  const [scene, setScene] = useState<Scene>("游客路线");
  const [prompt, setPrompt] = useState("");
  const [city, setCity] = useState("自动判断");
  const [error, setError] = useState("");
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const current = tasks.find((task) => task.key === scene) ?? tasks[0];

  const applyInspiration = (item: typeof inspirations[number]) => {
    setScene(item.scene);
    setCity(item.city);
    setPrompt(item.prompt);
    setError("");
    document.getElementById("compose")?.scrollIntoView({ behavior: "smooth", block: "center" });
    requestAnimationFrame(() => inputRef.current?.focus({ preventScroll: true }));
  };

  const start = () => {
    if (!prompt.trim()) {
      setError("先简单描述你的想法，或选一条下方灵感示例。");
      inputRef.current?.focus();
      return;
    }
    const draft: TaskRequest = {
      ...DEFAULT_REQUEST,
      scene,
      city,
      raw_request: prompt.trim(),
      task_type: scene === "内容创作" ? "social" : scene === "非遗问答" ? "qa" : scene === "学生研学" ? "study" : "route",
    };
    try {
      sessionStorage.setItem("yuejian-launch-draft", JSON.stringify(draft));
      router.push("/studio");
    } catch {
      router.push("/studio?" + new URLSearchParams({ scene, prompt: draft.raw_request, city }).toString());
    }
  };

  return (
    <>
      <SiteHeader />
      <main className="festival-home" id="main-content">
        <section className="festival-hero" aria-label="粤见非遗文化探索">
          <div className="festival-hero-copy container">
            <span className="festival-overline">YUEJIAN · 粤见非遗</span>
            <h1>把岭南的<br/><em>鲜活故事</em><br/>装进旅程</h1>
            <p>从一条老街、一门手艺开始，找到属于你的文化体验。</p>
            <a href="#compose" className="festival-hero-cta">开始探索 <ArrowRight size={18} aria-hidden="true"/></a>
          </div>
        </section>

        <section className="festival-create" id="compose" aria-labelledby="festival-create-title">
          <div className="container festival-create-inner">
            <div className="festival-section-heading">
              <div>
                <span className="festival-kicker">你的非遗探索，从这里开始</span>
                <h2 id="festival-create-title">今天，想遇见什么？</h2>
              </div>
              <p>选一种体验，写下想法。其余的，交给粤见。</p>
            </div>
            <div className="festival-task-picker" role="group" aria-label="体验类型">
              {tasks.map((task) => {
                const Icon = task.icon;
                return <button key={task.key} type="button" className={"festival-task " + (scene === task.key ? "selected" : "")}
                  aria-pressed={scene === task.key} onClick={() => { setScene(task.key); setError(""); }}>
                  <Icon size={17} strokeWidth={2} aria-hidden="true"/>{task.label}
                </button>;
              })}
            </div>
            <form className="festival-form" onSubmit={(event) => { event.preventDefault(); start(); }}>
              <label htmlFor="festival-prompt">说说你的想法</label>
              <textarea ref={inputRef} id="festival-prompt" name="request" rows={3} maxLength={1200}
                value={prompt} onChange={(event) => { setPrompt(event.target.value); setError(""); }}
                aria-invalid={Boolean(error)} aria-describedby={error ? "festival-error" : "festival-counter"}
                placeholder={current.example}/>
              {error && <p className="festival-form-error" id="festival-error" role="alert">{error}</p>}
              <div className="festival-form-actions">
                <div className="festival-city"><MapPin size={17} aria-hidden="true"/><label htmlFor="festival-city">城市</label>
                  <select id="festival-city" value={city} onChange={(event) => setCity(event.target.value)}>
                    {CITIES.map((item) => <option key={item} value={item}>{item}</option>)}
                  </select>
                </div>
                <span className="festival-counter" id="festival-counter">{prompt.length}/1200</span>
                <button type="submit" className="festival-generate">生成我的方案 <ArrowUpRight size={18} aria-hidden="true"/></button>
              </div>
            </form>
          </div>
        </section>

        <section className="festival-inspirations container" aria-labelledby="festival-inspirations-heading">
          <div className="festival-inspirations-heading">
            <div><span className="festival-kicker"><Sparkles size={15} aria-hidden="true"/> 一点灵感</span><h2 id="festival-inspirations-heading">不知道从哪开始？</h2></div>
            <p>点击喜欢的主题，直接带入需求。</p>
          </div>
          <div className="festival-inspiration-grid">
            {inspirations.map((item) =>
              <button key={item.title} className="festival-inspiration" type="button" onClick={() => applyInspiration(item)}
                aria-label={"使用灵感：" + item.title}>
                <div className="festival-inspiration-picture">
                  <Image src={item.image} alt={item.alt} fill sizes="(max-width: 700px) 90vw, (max-width: 1100px) 45vw, 370px" loading="lazy"/>
                </div>
                <div className="festival-inspiration-body"><span>{item.kicker}</span><h3>{item.title}</h3><p>{item.description}</p><ArrowUpRight size={20} aria-hidden="true"/></div>
              </button>
            )}
          </div>
          <p className="festival-usage-note">生成的方案支持修改、复制和导出；开放时间、票价及预约信息请以官方渠道为准。</p>
        </section>
        <footer className="festival-footer"><div className="container"><strong>粤见非遗</strong><span>岭南的故事，还在继续。</span></div></footer>
      </main>
    </>
  );
}
