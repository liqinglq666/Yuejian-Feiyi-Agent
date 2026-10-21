import { Compass, GraduationCap, HeartHandshake, PencilLine, MessageCircle } from "lucide-react";

export const SCENES = [
  { key:"游客路线", name:"城市漫游", desc:"从街巷走进传统", icon:Compass },
  { key:"学生研学", name:"文化研学", desc:"带着问题去观察", icon:GraduationCap },
  { key:"亲子体验", name:"亲子体验", desc:"让孩子亲手感知", icon:HeartHandshake },
  { key:"内容创作", name:"内容创作", desc:"传播鲜活的文化", icon:PencilLine },
  { key:"非遗问答", name:"非遗问答", desc:"听见技艺背后故事", icon:MessageCircle },
] as const;
