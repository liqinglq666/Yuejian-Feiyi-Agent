"use client";

import Image from "next/image";
import { useRef, useState } from "react";
import { useRouter } from "next/navigation";
import {
  ArrowRight, BookOpenText, Compass, GraduationCap, Heart,
  MapPin, PenLine,
} from "lucide-react";
import { SiteHeader } from "@/components/site-header";
import { CITIES, DEFAULT_REQUEST, type Scene, type TaskRequest } from "@/lib/types";

const scenarios = [
  { key:"游客路线", label:"路线规划", icon:Compass, prompt:"帮我规划广州一天的粤剧和广绣体验路线，步行友好。" },
  { key:"学生研学", label:"学生研学", icon:GraduationCap, prompt:"为初中生设计一次潮汕英歌舞主题的研学活动。" },
  { key:"亲子体验", label:"亲子体验", icon:Heart, prompt:"周末带孩子去佛山体验醒狮和陶塑，安排轻松的半天行程。" },
  { key:"内容创作", label:"内容创作", icon:PenLine, prompt:"写一篇介绍香云纱制作工艺的小红书图文。" },
  { key:"非遗问答", label:"非遗问答", icon:BookOpenText, prompt:"广绣有哪些典型针法？适合怎样的初学者？" },
] as const;

const inspiration = [
  {
    title:"潮汕英歌", note:"研学观察", scene:"学生研学" as Scene, city:"汕头",
    question:"为初中生设计一份潮汕英歌舞研学观察任务，包含文化背景和记录问题。",
    image:"/heritage/heritage-folk-procession.webp",
  },
  {
    title:"端午龙舟", note:"体验路线", scene:"游客路线" as Scene, city:"佛山",
    question:"设计一条了解广东龙舟文化的一日体验路线，注明实际活动时间需提前核实。",
    image:"/heritage/heritage-dragon-boat.webp",
  },
  {
    title:"陆丰皮影", note:"文化问答", scene:"非遗问答" as Scene, city:"汕尾",
    question:"介绍陆丰皮影戏的历史和表演特色，适合第一次接触非遗的人阅读。",
    image:"/heritage/heritage-shadow-puppetry.webp",
  },
];

export default function HomePage() {
  const router = useRouter();
  const promptRef = useRef<HTMLTextAreaElement>(null);
  const [scene, setScene] = useState<Scene>("游客路线");
  const [city, setCity] = useState("自动判断");
  const [prompt, setPrompt] = useState("");
  const [error, setError] = useState("");
  const active = scenarios.find((item) => item.key === scene) ?? scenarios[0];

  function focusComposer() {
    document.getElementById("create")?.scrollIntoView({ behavior:"smooth", block:"start" });
    window.requestAnimationFrame(() => promptRef.current?.focus({preventScroll:true}));
  }

  function chooseExample(item: typeof inspiration[number]) {
    setScene(item.scene);
    setCity(item.city);
    setPrompt(item.question);
    setError("");
    focusComposer();
  }

  function submit() {
    if (!prompt.trim()) {
      setError("先描述你的需求，或者点选下方的文化示例。");
      promptRef.current?.focus();
      return;
    }
    const draft: TaskRequest = {
      ...DEFAULT_REQUEST,
      scene,
      city,
      raw_request: prompt.trim(),
      task_type:scene === "内容创作" ? "social" : null,
    };
    try {
      sessionStorage.setItem("yuejian-launch-draft", JSON.stringify(draft));
      sessionStorage.setItem("yuejian-start-immediately", "1");
      router.push("/studio");
    } catch {
      const query = new URLSearchParams({ scene, city, prompt:prompt.trim() });
      router.push("/studio?" + query.toString());
    }
  }

  return (
    <>
      <SiteHeader />
      <main id="main-content" className="folk-home">
        <section className="folk-hero" aria-labelledby="home-title">
          <div className="container folk-hero__inner" id="create">
            <div className="folk-hero__copy">
              <p className="folk-eyebrow">广东非遗 · 为真实的文化体验而设计</p>
              <h1 id="home-title">去广东，<br />遇见<span>鲜活的非遗。</span></h1>
              <p className="folk-lead">告诉我们你想了解什么，让一次出行、一堂研学课或一个文化故事，从这里开始。</p>

              <form className="folk-composer" onSubmit={(e) => {e.preventDefault(); submit();}}>
                <div className="folk-field-label" id="folk-scene-label">你想做什么？</div>
                <div className="folk-scenario-tabs" role="group" aria-labelledby="folk-scene-label">
                  {scenarios.map((item) => {
                    const Icon = item.icon;
                    return (
                      <button
                        type="button" key={item.key} aria-pressed={scene === item.key}
                        className={"folk-scenario" + (scene === item.key ? " is-active" : "")}
                        onClick={() => {setScene(item.key); setError("");}}
                      >
                        <Icon size={16} strokeWidth={1.8} aria-hidden="true" />
                        {item.label}
                      </button>
                    );
                  })}
                </div>

                <div className="folk-input-head">
                  <label htmlFor="fast-request">说说你的想法</label>
                  <span>{prompt.length}/1200</span>
                </div>
                <textarea
                  ref={promptRef} id="fast-request" name="request"
                  autoComplete="off" maxLength={1200} rows={3}
                  value={prompt} aria-invalid={!!error}
                  aria-describedby={error ? "fast-form-error" : undefined}
                  placeholder={active.prompt + "…"}
                  onChange={(event) => {setPrompt(event.target.value); setError("");}}
                />
                {error && <p id="fast-form-error" className="folk-error" role="alert">{error}</p>}
                <div className="folk-compose-footer">
                  <div className="folk-city-field">
                    <MapPin size={16} aria-hidden="true"/>
                    <label htmlFor="fast-city">城市</label>
                    <select id="fast-city" name="city" value={city} onChange={(e) => setCity(e.target.value)}>
                      {CITIES.map((name) => <option value={name} key={name}>{name}</option>)}
                    </select>
                  </div>
                  <button type="submit" className="folk-submit">生成我的方案 <ArrowRight size={18} aria-hidden="true" /></button>
                </div>
              </form>
              <p className="folk-form-note">生成后可继续修改，并保存为 Word、Markdown 或 TXT。</p>
            </div>

            <div className="folk-hero__visual">
              <Image
                src="/heritage/lingnan-festival-hero-desktop.webp"
                alt="岭南传统建筑前，民俗巡游队伍沿水岸前行的彩绘插画"
                fill priority unoptimized
                sizes="(max-width: 760px) 100vw, 48vw"
              />
            </div>
          </div>
        </section>

        <section className="folk-inspiration container" id="ideas" aria-labelledby="ideas-title">
          <div className="folk-inspiration__head">
            <h2 id="ideas-title">从一个文化主题开始</h2>
            <p>不知道怎么描述？点击示例，自动填入需求。</p>
          </div>
          <div className="folk-inspiration__list">
            {inspiration.map((item) => (
              <button type="button" className="folk-inspiration__item" key={item.title} onClick={() => chooseExample(item)}>
                <span className="folk-inspiration__image">
                  <Image src={item.image} alt="" fill unoptimized sizes="(max-width: 760px) 82px, 96px" />
                </span>
                <span className="folk-inspiration__text">
                  <strong>{item.title}</strong><small>{item.note}</small>
                </span>
                <ArrowRight className="folk-inspiration__arrow" size={17} aria-hidden="true" />
              </button>
            ))}
          </div>
        </section>
        <footer className="folk-footer">
          <div className="container">
            <strong>粤见非遗</strong>
            <span>内容由 AI 辅助生成；开放时间、票价及预约以官方信息为准。</span>
          </div>
        </footer>
      </main>
    </>
  );
}
