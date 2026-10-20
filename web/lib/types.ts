export type Scene = "游客路线" | "学生研学" | "亲子体验" | "内容创作" | "非遗问答";
export type TaskType = "route" | "study" | "social" | "video" | "qa";

export interface TaskRequest {
  scene: Scene;
  raw_request: string;
  city: string;
  duration: string;
  identity: string;
  interests: string[];
  output_style: string;
  task_type?: TaskType | null;
}

export interface ModelOptions {
  mode: "auto" | "user";
  provider: string;
  api_key: string;
  base_url: string;
  model_name: string;
  temperature: number;
}

export interface Plan {
  id: string;
  request: TaskRequest;
  answer: string;
  sources: string;
  createdAt: string;
  revisions: { instruction: string; createdAt: string }[];
  metrics?: { first_token_ms: number | null; total_ms: number };
  quality?: { sections_complete:boolean; missing_sections:string[]; official_source_count:number; needs_fact_verification:boolean };
}

export interface AppStatus {
  service: string;
  platform_ready: boolean;
  platform_quota_protected: boolean;
  scenes: Scene[];
  revision_presets: string[];
}

export type StreamEvent =
  | { type: "stage"; value: string; label: string }
  | { type: "snapshot"; text: string }
  | { type: "delta"; text: string }
  | { type: "complete"; answer: string; sources: string; request: TaskRequest; metrics?: {first_token_ms:number|null;total_ms:number}; quality?: {sections_complete:boolean; missing_sections:string[]; official_source_count:number; needs_fact_verification:boolean} }
  | { type: "failure"; message: string };

export const CITIES = ["自动判断", "广州", "佛山", "潮州", "汕头", "深圳", "梅州", "江门", "珠海", "东莞", "肇庆", "惠州", "中山", "湛江", "茂名", "韶关", "清远", "河源", "阳江", "云浮", "揭阳", "汕尾"];
export const DURATIONS = ["自动判断", "半天", "一天", "两天", "周末", "不限"];
export const IDENTITIES = ["自动匹配", "外地游客", "学生研学", "亲子家庭", "本地居民", "内容创作者"];
export const INTERESTS = ["醒狮", "粤剧", "广绣", "岭南建筑", "潮汕工夫茶", "龙舟", "陶塑", "美食", "拍照", "研学", "短视频"];
export const STYLES = ["清晰实用", "游客友好", "研学报告", "小红书风格", "专业讲解"];

export const DEFAULT_REQUEST: TaskRequest = {
  scene: "游客路线",
  raw_request: "",
  city: "自动判断",
  duration: "自动判断",
  identity: "自动匹配",
  interests: [],
  output_style: "清晰实用",
  task_type: "route",
};
export const DEFAULT_MODEL: ModelOptions = {
  mode: "auto",
  provider: "阿里云百炼",
  api_key: "",
  base_url: "https://dashscope.aliyuncs.com/compatible-mode/v1",
  model_name: "qwen3.7-flash",
  temperature: 0.62,
};
export const MODEL_PROVIDERS = {
  "阿里云百炼": { base_url:"https://dashscope.aliyuncs.com/compatible-mode/v1", model_name:"qwen3.7-flash" },
  "DeepSeek": { base_url:"https://api.deepseek.com", model_name:"deepseek-v4-flash" },
  "OpenAI": { base_url:"https://api.openai.com/v1", model_name:"gpt-5" },
  "自定义 OpenAI-compatible": { base_url:"", model_name:"" },
};
