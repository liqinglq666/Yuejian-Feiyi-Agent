import { Suspense } from "react";
import { StudioApp } from "@/components/studio-app";

export const metadata = {
  title: "AI 非遗文化工作台",
  description: "智能规划岭南文化路线、研学任务、亲子体验及非遗图文视频创作。",
};

export default function StudioPage() {
  return (
    <Suspense fallback={<div className="studio-loading" role="status"><span className="loading-indicator" aria-hidden="true"/>正在打开工作台…</div>}>
      <StudioApp />
    </Suspense>
  );
}
