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
      "event: snapshot\ndata: " + JSON.stringify({ text: answer.slice(0, 12) }),
      "event: delta\ndata: " + JSON.stringify({ text: answer.slice(12) }),
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
    await expect(page.getByRole("heading", { name: /去广东，.*鲜活的非遗/ })).toBeVisible();
    await checkNoHorizontalOverflow(page);
    await page.getByRole("button", { name: /亲子体验/ }).first().click();
    await expect(page.getByRole("button", { name: /亲子体验/ }).first()).toHaveAttribute("aria-pressed", "true");
    await page.locator("#fast-request").fill(draftText);
    await page.getByRole("button", { name: /生成我的方案/ }).click();
    await expect(page).toHaveURL(/\/studio$/);
    await expect(page.locator("#request-input")).toHaveValue(draftText);
    await expect(page.getByRole("heading", {name:"生成结果"})).toBeVisible();
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
  await expect(page.locator("#studio-error")).toContainText("请先写下你的需求");
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
  expect((await download).suggestedFilename()).toBe("yuejian-feiyi.docx");
  await expect(page.getByRole("status").last()).toContainText("已开始下载 Word");

  await page.getByRole("button", { name: "更适合亲子" }).click();
  await expect(page.getByText("已调整的亲子体验路线。")).toBeVisible();
});


test("inspiration is actionable, not a fake event or booking feature", async ({ page }) => {
  await page.setViewportSize({width:375,height:812});
  await mockService(page);
  await page.goto("/");
  await page.getByRole("button",{name:/陆丰皮影/}).click();
  await expect(page.locator("#fast-request")).toContainText("陆丰皮影戏");
  await expect(page.getByRole("button",{name:"非遗问答"})).toHaveAttribute("aria-pressed","true");
  await expect(page.locator("#fast-city")).toHaveValue("汕尾");
  await checkNoHorizontalOverflow(page);
});


test("status retry keeps the input draft intact after temporary outage", async ({ page }) => {
  let attempts = 0;
  await page.route("**/api/v1/status", (route) => {
    attempts += 1;
    if (attempts <= 3) {
      return route.fulfill({status:503,contentType:"application/json",body:'{"detail":"temporarily unavailable"}'});
    }
    return route.fulfill({status:200,contentType:"application/json",body:JSON.stringify(getStatus)});
  });
  await page.goto("/studio");
  await page.locator("#request-input").fill("想了解潮州木雕的工艺特色");
  await expect(page.getByRole("button",{name:"重新检查连接"})).toBeVisible();
  await page.getByRole("button",{name:"重新检查连接"}).click();
  await expect(page.getByText("平台服务可用")).toBeVisible();
  await expect(page.locator("#request-input")).toHaveValue("想了解潮州木雕的工艺特色");
});


test("CRLF SSE frames are accepted by the real browser event parser", async ({ page }) => {
  await mockService(page);
  await page.route("**/api/v1/generate", async (route) => {
    const body = route.request().postDataJSON() as { request: RequestInput };
    const text = "## 方案总览\n\n粤剧源自岭南传统戏剧。";
    const content = [
      "event: snapshot\ndata: " + JSON.stringify({ text: text.slice(0, 9) }),
      "event: delta\ndata: " + JSON.stringify({ text: text.slice(9) }),
      "event: complete\ndata: " + JSON.stringify({ answer:text, sources:"国级项目资料", request:body.request }),
      "",
      "",
    ].join("\n\n").replace(/\n/g,"\r\n");
    await route.fulfill({ status:200, contentType:"text/event-stream; charset=utf-8", body:content });
  });
  await page.goto("/studio");
  await page.locator("#request-input").fill("请介绍粤剧");
  await page.getByRole("button",{name:"生成方案",exact:true}).click();
  await expect(page.getByText("粤剧源自岭南传统戏剧。")).toBeVisible();
});


test("studio CTA focuses the composer instead of navigating to the same page", async ({ page }) => {
  await mockService(page);
  await page.goto("/studio");
  await page.getByRole("link", { name: /开始体验/ }).click();
  await expect(page.locator("#request-input")).toBeFocused();
});

test("failed regeneration keeps previous result clearly labeled", async ({ page }) => {
  await mockService(page);
  await page.goto("/studio");
  await page.locator("#request-input").fill("广州的一日非遗文化路线");
  await page.getByRole("button", { name: "生成方案", exact: true }).click();
  await expect(page.getByRole("heading", { name: "生成结果" })).toBeVisible();

  await page.route("**/api/v1/generate", (route) =>
    route.fulfill({ status: 503, contentType: "application/json", body: JSON.stringify({ detail: "平台服务暂时中断" }) }),
  );
  await page.locator("#request-input").fill("为潮州安排新的文化行程");
  await page.getByRole("button", { name: "生成方案", exact: true }).click();
  await expect(page.locator("#studio-error")).toContainText("平台服务暂时中断");
  await expect(page.getByRole("heading", { name: "上次成功的方案" })).toBeVisible();
  await expect(page.locator("#proposal")).toContainText("本次生成没有完成");
  await expect(page.locator("#proposal")).toContainText("非遗路线推荐：体验醒狮与陶塑。");
  await expect(page.locator("#proposal")).not.toContainText("为潮州安排新的文化行程");
});

test("stream failure is reported without presenting an unfinished proposal", async ({ page }) => {
  await mockService(page);
  await page.route("**/api/v1/generate", (route) =>
    route.fulfill({
      status: 200, contentType: "text/event-stream; charset=utf-8",
      body: 'event: snapshot\ndata: {"text":"## 未完成的方案"}\n\nevent: failure\ndata: {"message":"模型生成中途失败"}\n\n',
    }),
  );
  await page.goto("/studio");
  await page.locator("#request-input").fill("广州一天了解粤剧");
  await page.getByRole("button", { name: "生成方案", exact: true }).click();
  await expect(page.locator("#studio-error")).toContainText("模型生成中途失败");
  await expect(page.locator("#proposal")).toHaveCount(0);
  await expect(page.getByRole("button", { name: "生成方案", exact: true })).toBeEnabled();
});

test("homepage launch is not unexpectedly resumed after a disabled platform recovers", async ({ page }) => {
  let ready = false;
  let generationCalls = 0;
  await page.route("**/api/v1/status", (route) =>
    route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ ...getStatus, platform_ready: ready }) }),
  );
  await page.route("**/api/v1/generate", (route) => {
    generationCalls += 1;
    return route.fulfill({ status: 500, body: "unexpected generation" });
  });
  await page.goto("/");
  await page.locator("#fast-request").fill("规划一条广州非遗路线");
  await page.getByRole("button", { name: /生成我的方案/ }).click();
  await expect(page).toHaveURL(/\/studio$/);
  await expect(page.locator("#request-input")).toHaveValue("规划一条广州非遗路线");
  await expect(page.locator(".studio-notice")).toContainText("需求已保留");
  ready = true;
  await page.getByRole("button", { name: "重新检查状态" }).click();
  await expect(page.getByText("平台服务可用")).toBeVisible();
  expect(generationCalls).toBe(0);
  await expect(page.locator("#proposal")).toHaveCount(0);
});

test("mobile new-plan action is disabled during a pending request and cancel recovers", async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 812 });
  await mockService(page);
  await page.route("**/api/v1/generate", async (route) => {
    await new Promise((resolve) => setTimeout(resolve, 2000));
    try {
      await route.fulfill({ status: 503, contentType: "application/json", body: '{"detail":"delayed request"}' });
    } catch { /* Aborting the browser request can dispose of the route. */ }
  });
  await page.goto("/studio");
  await page.locator("#request-input").fill("佛山半天醒狮文化体验");
  await page.getByRole("button", { name: "生成方案", exact: true }).click();
  await expect(page.locator(".mobile-scene-bar button").nth(1)).toBeDisabled();
  await page.getByRole("button", { name: "取消生成" }).click();
  await expect(page.getByRole("button", { name: "生成方案", exact: true })).toBeEnabled();
  await expect(page.locator("#proposal")).toHaveCount(0);
  await expect(page.locator(".studio-notice")).toContainText("已停止接收内容");
});
