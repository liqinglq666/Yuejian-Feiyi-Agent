import type { ModelOptions, StreamEvent, TaskRequest } from "./types";

const ROOT = "/api/v1";

async function errorMessage(response: Response): Promise<string> {
  try {
    const data = await response.json();
    if (typeof data.detail === "string") return data.detail;
  } catch {
    // A proxy may return HTML for an unavailable API process.
  }
  return `请求失败（HTTP ${response.status}），请检查后端服务。`;
}

/** Read a real event-stream, including events split across arbitrary network chunks. */
export async function streamProposal(
  route: "generate" | "revise",
  request: TaskRequest,
  model: ModelOptions,
  revise: { current_answer: string; instruction?: string; preset?: string } | null,
  onEvent: (event: StreamEvent) => void,
  signal: AbortSignal,
): Promise<void> {
  const response = await fetch(`${ROOT}/${route}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    cache: "no-store",
    body: JSON.stringify({ request, model, ...(revise ?? {}) }),
    signal,
  });
  if (!response.ok) throw new Error(await errorMessage(response));
  if (!response.body) throw new Error("浏览器不支持此流式响应。");

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let completed = false;

  const processFrame = (frame: string) => {
    const lines = frame.split("\n");
    const kind = lines.find((line) => line.startsWith("event:"))?.slice(6).trim();
    const payload = lines.filter((line) => line.startsWith("data:")).map((line) => line.slice(5).trimStart()).join("\n");
    if (!kind || !payload) return;
    const value = JSON.parse(payload) as Record<string, unknown>;
    if (kind === "stage") onEvent({ type: "stage", value: String(value.value), label: String(value.label) });
    if (kind === "snapshot") onEvent({ type: "snapshot", text: String(value.text) });
    if (kind === "delta") onEvent({ type: "delta", text: String(value.text) });
    if (kind === "complete") {
      completed = true;
      onEvent({ type: "complete", answer: String(value.answer), sources: String(value.sources), request: value.request as unknown as TaskRequest, metrics: value.metrics as {first_token_ms:number|null;total_ms:number}|undefined });
    }
    if (kind === "failure") {
      completed = true;
      onEvent({ type: "failure", message: String(value.message) });
    }
  };

  try {
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true }).replace(/\r\n/g, "\n");
      let boundary: number;
      while ((boundary = buffer.indexOf("\n\n")) >= 0) {
        processFrame(buffer.slice(0, boundary));
        buffer = buffer.slice(boundary + 2);
      }
    }
    buffer += decoder.decode();
    if (buffer.trim()) processFrame(buffer.trim());
  } finally {
    reader.releaseLock();
  }
  if (!completed && !signal.aborted) throw new Error("连接中断，未收到完整的生成结果。");
}

export async function exportProposal(
  request: TaskRequest,
  answer: string,
  sources: string,
  format: "md" | "txt" | "docx",
): Promise<void> {
  const response = await fetch(`${ROOT}/export`, {
    method: "POST", headers: { "Content-Type": "application/json" }, cache: "no-store",
    body: JSON.stringify({ request, answer, sources, format }),
  });
  if (!response.ok) throw new Error(await errorMessage(response));
  const objectUrl = URL.createObjectURL(await response.blob());
  try {
    const link = document.createElement("a");
    link.href = objectUrl;
    link.download = `yuejian-feiyi.${format}`;
    document.body.appendChild(link);
    link.click();
    link.remove();
  } finally {
    setTimeout(() => URL.revokeObjectURL(objectUrl), 1500);
  }
}

/** Split a Markdown document by canonical level-2 sections without dropping intro text. */
export function splitSections(answer: string): { title: string; content: string }[] {
  const lines = answer.split("\n");
  const sections: { title: string; content: string }[] = [];
  let title = "方案引言";
  let content: string[] = [];
  for (const line of lines) {
    const match = /^##\s+(.+)$/.exec(line);
    if (match) {
      if (content.join("").trim()) sections.push({ title, content: content.join("\n") });
      title = match[1];
      content = [line];
    } else {
      content.push(line);
    }
  }
  if (content.join("").trim()) sections.push({ title, content: content.join("\n") });
  return sections;
}
