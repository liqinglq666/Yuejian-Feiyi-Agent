import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  metadataBase: new URL("https://yuejian-feiyi.vercel.app"),
  title: {
    default: "粤见非遗 YUEJIAN | 让岭南文化触手可及",
    template: "%s | 粤见非遗",
  },
  description: "粤见非遗：以智能文化体验，探索广东非遗路线、研学活动、亲子旅程与文化内容创作。",
  keywords: ["广东非遗", "岭南文化", "非遗研学", "智能文旅", "粤见非遗"],
  openGraph: {
    title: "粤见非遗 · YUEJIAN",
    description: "遇见岭南，让非遗可感。用 AI 定制独一无二的非遗文化体验。",
    images: ["/heritage-hero.png"],
  },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="zh-CN">
      <body><a href="#main-content" className="skip-link">跳转到主要内容</a>{children}</body>
    </html>
  );
}
