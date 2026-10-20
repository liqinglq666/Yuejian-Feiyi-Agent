import Link from "next/link";
import { ArrowDown, ArrowRight, ArrowUpRight, BookOpen, Camera, Compass, Feather, Flower2, GraduationCap, HeartHandshake, MapPin, Sparkles, WandSparkles } from "lucide-react";
import { SiteHeader } from "@/components/site-header";

const journeys = [
  { id:"01", title:"城市非遗漫游", en:"CITY WALK", icon:Compass, copy:"以街巷为线索，走进活着的文化遗产。发现粤剧、古建与手艺背后的城市记忆。", note:"路线 · 体验 · 攻略", scene:"游客路线" },
  { id:"02", title:"文化研学课堂", en:"LEARNING JOURNEY", icon:GraduationCap, copy:"从观察任务到研学报告，把看见变成理解，让每一次探索都有真实收获。", note:"任务卡 · 观察 · 报告", scene:"学生研学" },
  { id:"03", title:"亲子手作时光", en:"FAMILY EXPERIENCES", icon:HeartHandshake, copy:"让孩子触摸手艺的温度。在轻松有趣的节奏里，发现文化的另一种表达。", note:"互动 · 手作 · 陪伴", scene:"亲子体验" },
  { id:"04", title:"非遗创意表达", en:"CULTURAL CREATION", icon:Camera, copy:"让文化素材生长成故事。生成图文灵感、短视频分镜与可分享的内容。", note:"图文 · 视频 · 传播", scene:"内容创作" },
  { id:"05", title:"非遗百科问答", en:"HERITAGE STORIES", icon:BookOpen, copy:"从一道问题开始，认识工艺、风俗与传统表演，理解每一项技艺的来处。", note:"知识 · 故事 · 体验", scene:"非遗问答" },
];
const cities = [{name:"广州",tag:"广绣 · 粤剧"}, {name:"佛山",tag:"醒狮 · 陶塑"}, {name:"潮州",tag:"潮绣 · 工夫茶"}, {name:"汕头",tag:"英歌舞 · 潮汕"}, {name:"江门",tag:"侨乡 · 民俗"}];

export default function HomePage() {
  return (
    <>
      <SiteHeader />
      <main id="top">
        <section className="home-hero" aria-labelledby="hero-title">
          <div className="hero-image" role="img" aria-label="岭南传统文化与非遗插画，包括醒狮、粤剧与工艺" />
          <div className="hero-overlay"/>
          <div className="hero-content container">
            <div className="hero-kicker"><span className="kicker-line"/>A LIVING HERITAGE JOURNEY · 岭南文化新体验</div>
            <h1 id="hero-title">走近岭南，<br/><em>遇见</em>非遗之美<span className="hero-dot">。</span></h1>
            <p className="hero-description">文化不应只停留在展柜里。<br/>从一条城市路线、一段非遗故事开始，让传统真正走入生活。</p>
            <div className="hero-buttons">
              <Link href="/studio" className="button button-accent">开启我的非遗探索 <ArrowUpRight size={18}/></Link>
              <Link href="#experiences" className="button button-outline-light">浏览体验方式 <ArrowDown size={17}/></Link>
            </div>
            <div className="hero-proof">
              <div className="hero-proof-mark"><Flower2 size={28} strokeWidth={1.3}/></div>
              <div><strong>五种文化探索方式</strong><span>非遗知识 × 个性化路线 × 智能创作</span></div>
            </div>
          </div>
          <div className="hero-side-caption">GUANGDONG INTANGIBLE CULTURAL HERITAGE <span>01 — 05</span></div>
          <div className="hero-scroll-cue">SCROLL TO EXPLORE <span/></div>
        </section>

        <section className="intro-section container" id="story">
          <div className="intro-tag"><span className="eyebrow">OUR PHILOSOPHY</span><span className="intro-accent">见 · 闻 · 行 · 思</span></div>
          <div className="intro-grid">
            <h2 className="display-title">让文化被看见，<br/><span>更被亲身感受。</span></h2>
            <div className="intro-copy"><p>非遗是镌刻在城市街巷里的生活美学，也是传承于手艺人与一代代家庭之间的共同记忆。</p><p>粤见非遗以广东文化知识为底色，将 AI 的理解与规划能力融入旅途，让每一个人都能找到贴近自己的探索方式。</p><Link href="/studio" className="text-link">从此刻开始你的文化旅程 <ArrowUpRight size={17}/></Link></div>
          </div>
          <div className="intro-metrics">
            <div><strong>05</strong><span>多元体验场景</span></div>
            <div><strong>21</strong><span>广东城市可选择</span></div>
            <div><strong>AI</strong><span>智能文化体验生成</span></div>
            <div className="metric-quote"><Feather size={20}/><span>让传统文化，以当代方式继续生长。</span></div>
          </div>
        </section>

        <section className="journeys-section" id="experiences">
          <div className="container">
            <div className="section-heading-row">
              <div><div className="eyebrow">01 — CURATED EXPERIENCES</div><h2 className="display-title">你的岭南，<span>有无数种打开方式。</span></h2></div>
              <p>无论是第一次到访，还是重新认识故乡，<br/>总有一种探索，适合此刻的你。</p>
            </div>
            <div className="journey-grid">
              {journeys.map((journey) => {
                const Icon = journey.icon;
                return (
                  <Link className="journey-card" key={journey.id} href={`/studio?scene=${encodeURIComponent(journey.scene)}`}>
                    <div className="journey-card-top"><span>{journey.id} / {journey.en}</span><ArrowUpRight size={20}/></div>
                    <div className="journey-icon"><Icon size={30} strokeWidth={1.35}/></div>
                    <h3>{journey.title}</h3><p>{journey.copy}</p>
                    <div className="journey-card-footer"><span>{journey.note}</span><span className="journey-circle"><ArrowRight size={16}/></span></div>
                  </Link>
                );
              })}
              <div className="journey-feature-card">
                <div className="feature-pattern" aria-hidden="true">粤</div>
                <Sparkles size={26} strokeWidth={1.4}/>
                <div><span className="eyebrow">CREATE YOUR OWN JOURNEY</span><h3>不只是参观，<br/>更是一次与你有关的文化相遇。</h3><Link href="/studio">定制专属提案 <ArrowUpRight size={17}/></Link></div>
              </div>
            </div>
          </div>
        </section>

        <section className="city-section container">
          <div className="city-section-heading"><div><div className="eyebrow">02 — TRACES OF LINGNAN</div><h2 className="display-title">循着城市，<span>寻访文化印记。</span></h2></div><div className="city-note">从珠江水畔到潮汕街巷<br/>将好奇心交给下一站。</div></div>
          <div className="city-list">{cities.map((city,index)=><Link href={`/studio?city=${encodeURIComponent(city.name)}`} key={city.name} className="city-row"><span className="city-index">0{index+1}</span><strong>{city.name}</strong><span>{city.tag}</span><ArrowUpRight size={19}/></Link>)}</div>
          <div className="city-disclaimer"><MapPin size={15}/> 城市示例用于激发灵感，具体开放与预约信息请以官方平台公告为准。</div>
        </section>

        <section className="process-section">
          <div className="container process-grid">
            <div className="process-intro"><div className="eyebrow">03 — HOW IT WORKS</div><h2>从一句心愿，<br/>到一份<span>文化提案。</span></h2><p>复杂的资料检索与个性化规划，交给技术。把时间留给感受真正的文化。</p><Link className="button button-accent" href="/studio">进入体验工作台 <ArrowUpRight size={17}/></Link></div>
            <div className="process-steps">
              <div><span>01</span><div><h3>选择体验场景</h3><p>漫游、亲子、研学、创作或非遗问答。</p></div><Compass size={23}/></div>
              <div><span>02</span><div><h3>告诉我们你的兴趣</h3><p>城市、时间、同行者与好奇的主题。</p></div><WandSparkles size={23}/></div>
              <div><span>03</span><div><h3>生成并完善你的方案</h3><p>分场景呈现，支持持续修改和文档导出。</p></div><Feather size={23}/></div>
            </div>
          </div>
        </section>
        <section className="final-cta container"><div className="eyebrow">THE JOURNEY BEGINS HERE</div><h2>下一段非遗故事，<br/><em>由你开启。</em></h2><Link href="/studio" className="button button-dark">开始探索岭南 <ArrowUpRight size={18}/></Link><span className="cta-watermark">粤见</span></section>
      </main>
      <footer className="site-footer"><div className="container footer-inner"><div><strong>粤见非遗 YUEJIAN</strong><p>让岭南文化触手可及</p></div><div className="footer-links"><Link href="/">首页</Link><Link href="/#experiences">体验场景</Link><Link href="/studio">AI 工作台</Link></div><small>文化知识仅供参考 · 开放时间与预约信息请以官方公告为准</small></div></footer>
    </>
  );
}
