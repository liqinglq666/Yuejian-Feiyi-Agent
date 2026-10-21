"use client";
import { ArrowRight, Check, FileText, X } from "lucide-react";
import type { RefObject } from "react";
import { SCENES } from "./studio-data";
import type { Plan, Scene, TaskRequest } from "@/lib/types";

type Props = {
  drawerOpen: boolean;
  busy: boolean;
  request: TaskRequest;
  recents: Plan[];
  sidebarRef: RefObject<HTMLElement | null>;
  sidebarCloseRef: RefObject<HTMLButtonElement | null>;
  onClose: () => void;
  onSceneChange: (scene: Scene) => void;
  onRestore: (plan: Plan) => void;
};

export function StudioSidebar({ drawerOpen, busy, request, recents, sidebarRef, sidebarCloseRef, onClose, onSceneChange, onRestore }: Props) {
  return (
<aside ref={sidebarRef} id="studio-scenes" className={`studio-sidebar ${drawerOpen ? "sidebar-open" : ""}`}>
          <div className="sidebar-topline"><div className="sidebar-brand">粤见非遗</div><button ref={sidebarCloseRef} aria-label="关闭菜单" type="button" onClick={onClose} className="sidebar-close"><X size={19}/></button></div>
          <h2 className="sidebar-heading">选择体验</h2>
          <div className="sidebar-section-label">体验类型</div>
          <div className="sidebar-scene-list">
            {SCENES.map((scene) => {
              const Icon = scene.icon;
              return <button className={`sidebar-scene ${request.scene === scene.key ? "selected" : ""}`} key={scene.key} type="button" onClick={() => onSceneChange(scene.key)} disabled={busy} aria-pressed={request.scene === scene.key}>
                <span className="sidebar-scene-icon"><Icon size={19} strokeWidth={1.6}/></span>
                <span className="sidebar-scene-text"><strong>{scene.name}</strong><small>{scene.desc}</small></span>
                {request.scene === scene.key ? <span className="sidebar-selected-mark"><Check size={14} aria-hidden="true"/></span> : <ArrowRight className="sidebar-arrow" size={15}/>}
              </button>;
            })}
          </div>
          <div className="sidebar-library">
            <div className="sidebar-section-label">最近生成</div>
            {recents.length ? recents.map((plan) => <button type="button" key={plan.id} className="recent-plan" onClick={() => onRestore(plan)}><FileText size={17}/><span><strong>{plan.request.city !== "自动判断" ? plan.request.city : "非遗"} · {plan.request.scene}</strong><small>{plan.createdAt}</small></span></button>) : <p className="no-recents">生成的方案会暂存在这个浏览器会话中。</p>}
          </div>
          
        </aside>
  );
}
