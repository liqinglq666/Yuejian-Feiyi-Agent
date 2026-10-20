"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ArrowUpRight, Menu, X } from "lucide-react";
import { useState } from "react";

export function SiteHeader() {
  const pathname = usePathname();
  const [menuOpen, setMenuOpen] = useState(false);
  return (
    <header className="site-header">
      <div className="nav-inner container">
        <Link href="/" aria-label="粤见非遗首页" className="wordmark" onClick={() => setMenuOpen(false)}>
          <span className="brand-seal">粤</span>
          <span className="brand-words">
            <strong>粤见非遗</strong>
            <small>YUEJIAN · LINGNAN CULTURE</small>
          </span>
        </Link>
        <nav className={`main-nav ${menuOpen ? "is-open" : ""}`} aria-label="主导航">
          <Link className={pathname === "/" ? "nav-active" : ""} href="/" onClick={() => setMenuOpen(false)}>首页</Link>
          <Link href="/#experiences" onClick={() => setMenuOpen(false)}>探索非遗</Link>
          <Link href="/#story" onClick={() => setMenuOpen(false)}>关于粤见</Link>
          <Link href="/studio" className={pathname === "/studio" ? "nav-active" : ""} onClick={() => setMenuOpen(false)}>创作工作台</Link>
          <Link href="/studio" className="nav-cta" onClick={() => setMenuOpen(false)}>开启体验 <ArrowUpRight size={16} strokeWidth={1.8}/></Link>
        </nav>
        <button className="nav-menu-toggle" type="button" aria-label={menuOpen ? "关闭菜单" : "打开菜单"} aria-expanded={menuOpen} onClick={() => setMenuOpen(!menuOpen)}>
          {menuOpen ? <X size={24}/> : <Menu size={24}/>}
        </button>
      </div>
    </header>
  );
}
