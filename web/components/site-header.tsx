"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ArrowUpRight, Menu, X } from "lucide-react";
import { useEffect, useState } from "react";

export function SiteHeader() {
  const pathname = usePathname();
  const [menuOpen, setMenuOpen] = useState(false);
  useEffect(() => {
    const onEscape = (event: KeyboardEvent) => { if (event.key === "Escape") setMenuOpen(false); };
    window.addEventListener("keydown", onEscape);
    return () => window.removeEventListener("keydown", onEscape);
  }, []);
  return (
    <header className="site-header">
      <div className="nav-inner container">
        <Link href="/" aria-label="粤见非遗首页" className="wordmark" onClick={() => setMenuOpen(false)}>
          <span className="brand-seal" aria-hidden="true">粤</span><span className="brand-words"><strong>粤见非遗</strong><small>YUEJIAN</small></span>
        </Link>
        <nav id="site-main-nav" className={`main-nav ${menuOpen ? "is-open" : ""}`} aria-label="主导航">
          <Link className={pathname === "/" ? "nav-active" : ""} href="/" onClick={() => setMenuOpen(false)}>首页</Link>
          <Link className={pathname === "/studio" ? "nav-active" : ""} href="/studio" onClick={() => setMenuOpen(false)}>AI 工作台</Link>
          <Link href={pathname === "/" ? "/#start" : "/studio"} className="nav-cta" onClick={() => setMenuOpen(false)}>开始体验 <ArrowUpRight size={16} aria-hidden="true"/></Link>
        </nav>
        <button className="nav-menu-toggle" type="button" aria-controls="site-main-nav" aria-label={menuOpen ? "关闭菜单" : "打开菜单"} aria-expanded={menuOpen} onClick={() => setMenuOpen(!menuOpen)}>{menuOpen ? <X size={24}/> : <Menu size={24}/>}</button>
      </div>
    </header>
  );
}
