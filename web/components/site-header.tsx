"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { ArrowUpRight, Menu, X } from "lucide-react";
import { useEffect,useRef,useState } from "react";
export function SiteHeader(){
  const pathname=usePathname();
  const [open,setOpen]=useState(false);
  const menuRef=useRef<HTMLButtonElement>(null);
  useEffect(()=>{
    const close=(event:KeyboardEvent)=>{if(event.key==="Escape"&&open){setOpen(false);menuRef.current?.focus();}};
    window.addEventListener("keydown",close);
    return()=>window.removeEventListener("keydown",close);
  },[open]);
  return <header className="site-header">
    <div className="nav-inner container">
      <Link href="/" className="wordmark" aria-label="粤见非遗首页" onClick={()=>setOpen(false)}>
        <span className="brand-seal" aria-hidden="true">粤</span>
        <span className="brand-words"><strong>粤见非遗</strong><small>YUEJIAN · GUANGDONG</small></span>
      </Link>
      <nav className={"main-nav"+(open?" is-open":"")} id="site-main-nav" aria-label="主导航">
        <Link href="/" className={pathname==="/"?"nav-active":""} onClick={()=>setOpen(false)}>首页</Link>
        <Link href="/studio" className={pathname==="/studio"?"nav-active":""} onClick={()=>setOpen(false)}>AI 工作台</Link>
        <Link href={pathname==="/"?"/#create":"/studio"} className="nav-cta" onClick={()=>setOpen(false)}>开始体验 <ArrowUpRight size={16} aria-hidden="true"/></Link>
      </nav>
      <button ref={menuRef} type="button" className="nav-menu-toggle" aria-controls="site-main-nav" aria-expanded={open} aria-label={open?"关闭菜单":"打开菜单"} onClick={()=>setOpen(!open)}>{open?<X size={22}/>:<Menu size={22}/>}</button>
    </div>
  </header>;
}
