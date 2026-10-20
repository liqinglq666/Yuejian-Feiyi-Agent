"use client";

import { useRef, useState } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import { ArrowRight, BookOpen, Compass, GraduationCap, HeartHandshake, MapPin, PenLine, Sparkles } from "lucide-react";
import { SiteHeader } from "@/components/site-header";
import { CITIES, DEFAULT_REQUEST, type Scene, type TaskRequest } from "@/lib/types";

const scenarios = [
  {key:"游客路线",label:"路线规划",hint:"走进广东，安排一次在地体验",icon:Compass, example:"帮我规划广州一天的粤剧和广绣体验路线，步行友好。"},
  {key:"学生研学",label:"学生研学",hint:"为课堂和研学准备观察任务",icon:GraduationCap,example:"为初中生设计一次潮汕英歌舞主题的研学活动。"},
  {key:"亲子体验",label:"亲子体验",hint:"让小朋友在动手中认识文化",icon:HeartHandshake,example:"周末带孩子去佛山体验醒狮和陶塑，安排轻松的半天行程。"},
  {key:"内容创作",label:"内容创作",hint:"把见闻写成图文或短视频脚本",icon:PenLine,example:"写一篇介绍香云纱制作工艺的小红书图文。"},
  {key:"非遗问答",label:"非遗问答",hint:"了解工艺、民俗与背后的故事",icon:BookOpen,example:"广绣有哪些典型针法？适合怎样的初学者？"},
] as const;

const inspiration = [
  {title:"潮汕民俗",note:"研学观察",scene:"学生研学" as Scene, city:"汕头",question:"为初中生设计一份潮汕英歌舞研学观察任务，包含文化背景和记录问题。",image:"/heritage/heritage-folk-procession.webp"},
  {title:"端午龙舟",note:"体验路线",scene:"游客路线" as Scene,city:"佛山",question:"设计一条了解广东龙舟文化的一日体验路线，注明实际活动时间需提前核实。",image:"/heritage/heritage-dragon-boat.webp"},
  {title:"陆丰皮影",note:"文化问答",scene:"非遗问答" as Scene,city:"汕尾",question:"介绍陆丰皮影戏的历史和表演特色，适合第一次接触非遗的人阅读。",image:"/heritage/heritage-shadow-puppetry.webp"},
];

export default function HomePage() {
  const router=useRouter();
  const promptRef=useRef<HTMLTextAreaElement>(null);
  const [scene,setScene]=useState<Scene>("游客路线");
  const [prompt,setPrompt]=useState("");
  const [city,setCity]=useState("自动判断");
  const [error,setError]=useState("");
  const active=scenarios.find(item=>item.key===scene)??scenarios[0];

  function focusComposer() {
    document.getElementById("create")?.scrollIntoView({behavior:"smooth",block:"start"});
    window.requestAnimationFrame(()=>promptRef.current?.focus({preventScroll:true}));
  }
  function chooseExample(item:typeof inspiration[number]) {
    setScene(item.scene);
    setCity(item.city);
    setPrompt(item.question);
    setError("");
    focusComposer();
  }
  function start() {
    if(!prompt.trim()){
      setError("先写下想了解或体验的内容，也可以选择右侧示例。");
      promptRef.current?.focus();
      return;
    }
    const draft:TaskRequest={
      ...DEFAULT_REQUEST,
      scene,
      city,
      raw_request:prompt.trim(),
      task_type:scene==="内容创作"?"social":null,
    };
    try {
      sessionStorage.setItem("yuejian-launch-draft",JSON.stringify(draft));
      router.push("/studio");
    } catch {
      const query=new URLSearchParams({scene,prompt:prompt.trim(),city});
      router.push("/studio?"+query.toString());
    }
  }
  return (
    <>
      <SiteHeader/>
      <main id="main-content" className="folk-home">
        <section className="folk-hero" aria-label="粤见非遗">
          <div className="container folk-hero__inner">
            <div className="folk-hero__copy">
              <span className="folk-eyebrow"><span aria-hidden="true" className="folk-eyebrow__dot"/> 广东非遗文化体验</span>
              <h1>去广东，<br/>遇见<span>鲜活的非遗。</span></h1>
              <p>想去哪里、体验什么？从一个想法开始，生成属于自己的岭南文化体验方案。</p>
              <div className="folk-hero__actions">
                <button type="button" className="folk-primary" onClick={focusComposer}>开始设计方案 <ArrowRight size={18} aria-hidden="true"/></button>
                <a className="folk-secondary" href="#ideas">看看文化灵感 <span aria-hidden="true">↗</span></a>
              </div>
            </div>
            <div className="folk-hero__visual" aria-hidden="true"/>
            <div className="folk-hero__caption" aria-hidden="true">LINGNAN · CULTURE IN MOTION</div>
          </div>
        </section>

        <section id="create" className="folk-creation container" aria-labelledby="create-title">
          <div className="folk-creation__heading">
            <div><span className="folk-section-kicker">01 / START HERE</span><h2 id="create-title">把你的想法，变成一份好方案。</h2></div>
            <span className="folk-creation__side">不需要复杂设置，写下需求即可开始</span>
          </div>
          <div className="folk-creation__layout">
            <form className="folk-composer" onSubmit={e=>{e.preventDefault();start();}}>
              <div className="folk-field-label">我想做什么？</div>
              <div className="folk-scenario-tabs" role="group" aria-label="选择体验类型">
                {scenarios.map(item=>{
                  const Icon=item.icon;
                  return <button type="button" key={item.key}
                    aria-pressed={scene===item.key}
                    className={"folk-scenario"+(scene===item.key?" is-active":"")}
                    onClick={()=>{setScene(item.key);setError("");}}
                    title={item.hint}>
                    <Icon size={18} strokeWidth={1.9} aria-hidden="true"/><span>{item.label}</span>
                  </button>;
                })}
              </div>
              <div className="folk-input-head">
                <label htmlFor="fast-request">{active.hint}</label>
                <span>{prompt.length}/1200</span>
              </div>
              <textarea ref={promptRef} id="fast-request" name="request" rows={5} maxLength={1200}
                value={prompt} aria-invalid={Boolean(error)} aria-describedby={error?"fast-form-error":undefined}
                onChange={e=>{setPrompt(e.target.value);setError("");}}
                placeholder={active.example}/>
              {error&&<p role="alert" id="fast-form-error" className="folk-error">{error}</p>}
              <div className="folk-compose-footer">
                <div className="folk-city-field">
                  <MapPin size={17} aria-hidden="true"/>
                  <label htmlFor="fast-city">城市</label>
                  <select id="fast-city" value={city} onChange={e=>setCity(e.target.value)}>
                    {CITIES.map(item=><option value={item} key={item}>{item}</option>)}
                  </select>
                </div>
                <button className="folk-submit" type="submit">前往生成 <ArrowRight size={19} aria-hidden="true"/></button>
              </div>
              <p className="folk-form-note">方案生成后可继续修改，并导出为 Word、Markdown 或 TXT。</p>
            </form>

            <aside className="folk-inspiration" id="ideas" aria-labelledby="ideas-title">
              <div className="folk-inspiration__head">
                <span className="folk-section-kicker">02 / INSPIRATION</span>
                <h3 id="ideas-title">从这些文化开始 <Sparkles size={18} aria-hidden="true"/></h3>
                <p>点击示例，直接填入你的需求。</p>
              </div>
              <div className="folk-inspiration__list">
                {inspiration.map(item=><button className="folk-inspiration__item" key={item.title} type="button" onClick={()=>chooseExample(item)}>
                  <span className="folk-inspiration__image"><Image src={item.image} alt="" fill sizes="(max-width: 720px) 90px, 112px"/></span>
                  <span className="folk-inspiration__text"><strong>{item.title}</strong><small>{item.note}</small></span>
                  <span className="folk-inspiration__arrow" aria-hidden="true">↗</span>
                </button>)}
              </div>
            </aside>
          </div>
          <p className="folk-disclaimer">提示：AI 生成内容仅供参考。演出、开放时间与预约信息请以官方渠道为准。</p>
        </section>
        <div className="folk-footer-ornament" aria-hidden="true"/>
        <footer className="folk-footer">
          <div className="container"><span><strong>粤见非遗</strong> · YUEJIAN</span><span>在广东，遇见正在发生的文化。</span></div>
        </footer>
      </main>
    </>
  );
}
