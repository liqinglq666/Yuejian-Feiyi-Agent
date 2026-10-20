import { expect, test } from "@playwright/test";

type RequestInput = {
  scene: string;
  raw_request: string;
  city: string;
  duration: string;
  identity: string;
  interests: string[];
  output_style: string;
};

const getStatus = {
  service: "ok",
  platform_ready: true,
  platform_quota_protected: true,
  scenes: ["游客路线", "学生研学", "亲子体验", "内容创作", "非遗问答"],
  revision_presets: ["压缩成半天", "更适合亲子", "生成小红书文案", "生成短视频脚本", "加研学记录表"],
};
const draftText = "周末带孩子体验佛山醒狮与陶塑，安排半天的文化路线。";

async function mockService(page: import("@playwright/test").Page) {
  await page.route("**/api/v1/status", (route) =>
    route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(getStatus) }),
  );

  const mockStream = (answer: string, request: RequestInput) =>
    [
      "event: stage\ndata: " + JSON.stringify({ value: "generating", label: "正在整理文化方案…" }),
      "event: snapshot\ndata: " + JSON.stringify({ text: answer }),
      "event: complete\ndata: " + JSON.stringify({ answer, sources: "广东文化知识库", request }),
      "",
      "",
    ].join("\n\n");

  await page.route("**/api/v1/generate", async (route) => {
    const body = route.request().postDataJSON() as { request: RequestInput };
    await route.fulfill({
      status: 200,
      contentType: "text/event-stream; charset=utf-8",
      body: mockStream("## 方案总览\n\n非遗路线推荐：体验醒狮与陶塑。\n\n## 体验亮点\n\n适合亲子手作。", body.request),
    });
  });
  await page.route("**/api/v1/revise", async (route) => {
    const body = route.request().postDataJSON() as { request: RequestInput };
    await route.fulfill({
      status: 200,
      contentType: "text/event-stream; charset=utf-8",
      body: mockStream("## 方案总览\n\n已调整的亲子体验路线。", body.request),
    });
  });
  await page.route("**/api/v1/export", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
      headers: { "content-disposition": 'attachment; filename="yuejian-feiyi.docx"' },
      body: "test-export-content",
    }),
  );
}

async function checkNoHorizontalOverflow(page: import("@playwright/test").Page) {
  const sizes = await page.evaluate(() => ({
    scroll: document.documentElement.scrollWidth,
    viewport: window.innerWidth,
  }));
  expect(sizes.scroll, "Document must not overflow horizontally").toBeLessThanOrEqual(sizes.viewport + 1);
}

for (const width of [375, 768, 1440]) {
  test("home → studio handoff and layout at " + width + "px", async ({ page }) => {
    await page.setViewportSize({ width, height: 900 });
    await mockService(page);
    await page.goto("/");
    await expect(page.getByRole("heading", { name: "找到适合你的非遗体验" })).toBeVisible();
    await checkNoHorizontalOverflow(page);
    await page.getByRole("button", { name: /亲子体验/ }).first().click();
    await expect(page.getByRole("button", { name: /亲子体验/ }).first()).toHaveAttribute("aria-pressed", "true");
    await page.getByLabel("你希望体验什么？").fill(draftText);
    await page.getByRole("button", { name: /下一步：生成方案/ }).click();
    await expect(page).toHaveURL(/\/studio$/);
    await expect(page.locator("#request-input")).toHaveValue(draftText);
    await checkNoHorizontalOverflow(page);

    if (width <= 760) {
      await page.locator(".mobile-scene-bar button").first().click();
      await expect(page.locator("#studio-scenes")).toHaveClass(/sidebar-open/);
      await page.locator(".sidebar-close").click();
      await expect(page.locator("#studio-scenes")).not.toHaveClass(/sidebar-open/);
    }

    const settingsOpener = page.getByRole("button", { name: "AI 设置" }).first();
    await settingsOpener.click();
    await expect(page.getByRole("dialog", { name: "AI 服务设置" })).toBeVisible();
    await expect(page.getByRole("button", { name: "关闭设置" })).toBeFocused();
    await page.keyboard.press("Escape");
    await expect(page.getByRole("dialog", { name: "AI 服务设置" })).toBeHidden();
    await expect(settingsOpener).toBeFocused();
    await checkNoHorizontalOverflow(page);
  });
}

test("generation, editing, exporting and empty-field error", async ({ page }) => {
  await mockService(page);
  await page.goto("/studio");
  await page.getByRole("button", { name: "生成方案", exact: true }).click();
  await expect(page.getByRole("alert")).toContainText("请先写下你的需求");
  await expect(page.locator("#request-input")).toBeFocused();

  await page.locator("#request-input").fill(draftText);
  await page.locator(".generate-button").click();
  await expect(page.getByRole("heading", { name: "生成结果" })).toBeVisible();
  await expect(page.getByText("非遗路线推荐：体验醒狮与陶塑。")).toBeVisible();
  await page.getByRole("button", { name: "体验亮点", exact: true }).click();
  await expect(page.getByText("适合亲子手作。")).toBeVisible();

  await page.getByRole("button", { name: "资料来源" }).click();
  await expect(page.getByText("广东文化知识库")).toBeVisible();
  await page.getByRole("button", { name: "完整方案" }).click();

  const download = page.waitForEvent("download");
  await page.getByRole("button", { name: "Word" }).click();
  await expect(await download).toHaveProperty("suggestedFilename", "yuejian-feiyi.docx");
  await expect(page.getByRole("status").last()).toContainText("已开始下载 Word");

  await page.getByRole("button", { name: "更适合亲子" }).click();
  await expect(page.getByText("已调整的亲子体验路线。")).toBeVisible();
});
