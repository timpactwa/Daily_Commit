import { expect, test } from "@playwright/test";
import { readFileSync } from "node:fs";
import { BANK } from "../../sites/generated.mjs";
import type { PublicQuestion, ResponseValue } from "../src/api";

async function choosePracticeAnswer(page: import("@playwright/test").Page, q: PublicQuestion, value: ResponseValue) {
  if (q.format === "tap_line") await page.getByRole("button", { name: new RegExp(`^Line ${value}:`) }).click();
  else if (q.format === "reorder") {
    for (const id of value as string[]) {
      const text = q.options!.find(o => o.id === id)!.text;
      await page.locator(".reorder .options button").filter({ hasText: text }).click();
    }
  } else if (q.format === "tap_node") {
    await page.locator(".diagram-node").filter({ hasText: q.diagram!.nodes.find(n => n.id === value)!.label }).click();
  } else await page.locator(".question .options button").nth(q.options!.findIndex(o => o.id === value)).click();
}

test("six-question practice blocks three correct, saves second tries, and passes a four-correct retry", async ({ page, request }) => {
  test.setTimeout(120000);
  const user = await (await request.post('/v1/users', { data: { display_name: 'Mastery QA' } })).json();
  const headers = { 'X-User-Id': user.user_id };
  const placement = await (await request.get('/v1/placement?limit=4', { headers })).json();
  const placed = await request.post('/v1/placement', { headers, data: { responses: placement.questions.map((q: PublicQuestion) => ({ question_id: q.id, response: BANK[q.id].answer })) } });
  expect(placed.ok()).toBeTruthy();
  await page.addInitScript(id => localStorage.setItem('dc.user_id', id), user.user_id);
  const lesson = await (await request.get('/v1/lessons/today', { headers })).json();
  expect(lesson.items).toHaveLength(6); expect(lesson.mastery.required).toBe(4);
  await page.goto('/#/lesson');
  async function finishQuestion(item: typeof lesson.items[number], right: boolean, checkReload = false) {
    const q = item.question as PublicQuestion, answer = BANK[q.id].answer;
    const wrong = q.format === 'tap_line' ? q.code!.split('\n').map((_,i) => i + 1).filter(i => i !== answer)
      : q.format === 'reorder' ? [[...(answer as string[])].reverse()]
      : (q.options ?? q.diagram!.nodes).map(o => o.id).filter(id => id !== answer);
    const choices = right ? [answer] : wrong.slice(0, item.attempt_limit);
    for (let attempt = 0; attempt < choices.length; attempt++) {
      await choosePracticeAnswer(page, q, choices[attempt]);
      await page.getByRole('button', { name: 'Check answer' }).click();
      if (!right && attempt + 1 < choices.length) {
        await expect(page.getByRole('status')).toContainText('one try left');
        await expect(page.getByRole('region', { name: 'Answer feedback' })).toHaveCount(0);
        if (checkReload) {
          await page.reload();
          await expect(page.getByRole('status')).toContainText('one try left');
          const saved = await (await request.get('/v1/lessons/today', { headers })).json();
          expect(saved.items.find((i: typeof item) => i.question.id === q.id).attempts_used).toBe(1);
        }
      }
    }
    await expect(page.getByRole('region', { name: 'Answer feedback' })).toBeVisible();
    await page.getByRole('button', { name: 'Continue', exact: false }).click();
  }
  for (let i = 0; i < lesson.items.length; i++) await finishQuestion(lesson.items[i], i < 3, true);
  await expect(page.getByText('KEEP PRACTICING', { exact: true })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Finish lesson' })).toHaveCount(0);
  expect((await request.post(`/v1/lessons/${lesson.lesson_id}/complete`, { headers, data: {} })).status()).toBe(409);
  const future = await (await request.get('/v1/lessons/today', { headers: { ...headers, 'X-Client-Date': '2027-01-01' } })).json();
  expect(future.lesson_id).toBe(lesson.lesson_id);
  await page.screenshot({ path: 'test-results/mastery-needs-retry.png', fullPage: true });
  const before = await (await request.get('/v1/progress', { headers })).json();
  await page.getByRole('button', { name: 'Retry practice' }).click();
  for (let i = 0; i < lesson.items.length; i++) await finishQuestion(lesson.items[i], i < 4);
  const after = await (await request.get('/v1/progress', { headers })).json();
  expect(after.topics).toEqual(before.topics);
  await page.getByRole('button', { name: 'Finish lesson' }).click();
  await expect(page.getByText('4 of 6 answers correct.', { exact: false })).toBeVisible();
});

test("ranked suggests one difficulty by level and leaves every test available", async ({ page }) => {
  test.setTimeout(60000);
  let number = 1;
  await page.route("**/v1/config", route => route.fulfill({ json: { features: { learn: true, ranked: true, accounts: true } } }));
  await page.route("**/v1/ranked", route => route.fulfill({ json: {
    has_account: true, ranked_level: number, ranked_rating: [0,600,1000,1200,1400,1650,1900,2100][number],
    tiers: [["beginner","Easy",1,3],["intermediate","Intermediate",4,5],["advanced","Advanced",6,7]].map(([id,title,min,max]) => ({
      id, title, min_level: min, max_level: max, description: "Practice at this difficulty.",
      time_limit_s: 600, question_count: 10, takers: 0, attempt: null,
      suggested: number >= Number(min) && number <= Number(max),
    })),
  } }));
  for (const current of [1,3,4,5,6,7]) {
    number = current;
    await page.goto("/#/ranked");
    await page.reload();
    await expect(page.getByText(`Your ranked level: Level ${number}`, { exact: true })).toBeVisible();
    const suggested = number <= 3 ? "Easy" : number <= 5 ? "Intermediate" : "Advanced";
    await expect(page.getByRole("article", { name: `${suggested} ranked test` }).getByText("SUGGESTED", { exact: true })).toBeVisible();
    await expect(page.getByText("SUGGESTED", { exact: true })).toHaveCount(1);
    for (const title of ["Easy", "Intermediate", "Advanced"]) {
      await expect(page.getByRole("article", { name: `${title} ranked test` }).getByRole("button", { name: "Take test", exact: true })).toBeEnabled();
    }
    if (number === 6) {
      const easy = page.getByRole("article", { name: "Easy ranked test" });
      await easy.getByRole("button", { name: "Take test", exact: true }).click();
      await expect(easy.getByRole("button", { name: "Start the clock" })).toBeVisible();
      await easy.getByRole("button", { name: "Not yet", exact: true }).click();
      for (const viewport of [{ width: 393, height: 851 }, { width: 1280, height: 900 }]) {
        await page.setViewportSize(viewport);
        expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBeTruthy();
        await page.screenshot({ path: `test-results/ranked-level-six-${viewport.width}.png`, fullPage: true });
      }
    }
  }
});
test("built PWA against real API: demo, feedback, completion, progress, offline retry", async ({
  page,
  request,
  context,
}) => {
  test.setTimeout(60000);
  const errors: string[] = [];
  page.on("pageerror", (err) => errors.push(err.message));
  const reset = await request.post("/v1/demo/reset", {
    data: { user_id: "demo" },
  });
  expect(reset.ok()).toBeTruthy();
  await page.goto("/");
  const logo = page.getByRole("button", { name: /^Daily Commit home/ });
  await logo.dispatchEvent("pointerdown");
  await page.waitForTimeout(1100);
  await logo.dispatchEvent("pointerup");
  await expect(
    page.getByRole("heading", { name: /Keep showing up/ }),
  ).toBeVisible();
  await expect(page.getByLabel("6 day streak")).toBeVisible();
  await page.screenshot({
    path: "test-results/home-phone.png",
    fullPage: true,
  });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBeTruthy();
  const date = await page.evaluate(() => {
    const d = new Date();
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
  });
  const response = await request.get("/v1/lessons/today", {
    headers: { "X-User-Id": "demo", "X-Client-Date": date },
  });
  expect(response.ok()).toBeTruthy();
  const lesson = await response.json();
  await page.getByRole("link", { name: "Make today’s commit" }).click();
  for (const item of lesson.items) {
    const q = item.question;
    await expect(
      page.getByRole("heading", { name: q.prompt, exact: true }),
    ).toBeVisible();
    await choosePracticeAnswer(page, q, BANK[q.id].answer);
    await page.getByRole("button", { name: "Check answer" }).click();
    await expect(
      page.getByRole("region", { name: "Answer feedback" }),
    ).toContainText("Elo");
    const feedback = page.getByRole("region", { name: "Answer feedback" });
    await expect(
      feedback.getByRole("heading", { name: "Why this works" }),
    ).toBeVisible();
    await expect(
      feedback.getByRole("heading", { name: "Check your understanding" }),
    ).toBeVisible();
    await feedback
      .getByText("Read more about this concept", { exact: true })
      .click();
    await expect(feedback.locator(".further-reading a")).toHaveCount(2);
    if (q.format === "tap_line") {
      await feedback
        .getByText("Trace the failing case and the fix", { exact: true })
        .click();
      await expect(
        feedback.getByRole("heading", { name: "Observed failure" }),
      ).toBeVisible();
      await expect(
        feedback.getByRole("heading", { name: "Corrected line" }),
      ).toBeVisible();
    }
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBeTruthy();
    await page.getByRole("button", { name: "Continue" }).click();
  }
  await page.getByRole("button", { name: "Finish lesson" }).click();
  await expect(page.getByLabel("7 day streak")).toBeVisible();
  await page.getByRole("link", { name: "View my progress" }).click();
  await expect(page.getByRole("progressbar")).toHaveCount(10);
  await page.evaluate(async () => {
    await navigator.serviceWorker.ready;
  });
  await page.reload();
  await expect(page.getByText("OVERALL READINESS")).toBeVisible();
  await context.setOffline(true);
  await page.reload();
  await expect(page.getByRole("alert")).toContainText("Check your connection");
  await expect(
    page.getByRole("button", { name: "Retry", exact: true }),
  ).toBeVisible();
  await context.setOffline(false);
  await page.getByRole("button", { name: "Retry", exact: true }).click();
  await expect(page.getByText("OVERALL READINESS")).toBeVisible();
  expect(errors).toEqual([]);
});

test("four-chapter learning path saves checkpoints, unlocks the next part and fits both screens", async ({ page, request }) => {
  test.setTimeout(60000);
  const module = JSON.parse(readFileSync(new URL("../../content/learn/arrays-strings.json", import.meta.url), "utf8"));
  const user = await (await request.post("/v1/users", { data: { display_name: "Learning QA" } })).json();
  await page.addInitScript(uid => localStorage.setItem("dc.user_id", uid), user.user_id);
  await page.goto("/#/learn/arrays-strings");
  const outline = page.getByRole("list", { name: "Module chapters" });
  await expect(outline.getByRole("button")).toHaveCount(4);
  await expect(outline.getByRole("button").nth(1)).toBeDisabled();
  for (let i = 0; i < module.sections.length; i++) {
    const section = module.sections[i];
    const chapter = page.locator(`#chapter-${section.id}`);
    await expect(chapter).toBeVisible();
    if (i === 0) {
      const wrong = section.check.options.find((o: { id: string }) => o.id !== section.check.answer);
      await chapter.locator(".options button").nth(section.check.options.indexOf(wrong)).click();
      await chapter.getByRole("button", { name: "Check answer", exact: true }).click();
      await expect(chapter.getByRole("status")).toContainText("Not quite");
      await expect(outline.getByRole("button").nth(1)).toBeDisabled();
    }
    const answer = section.check.options.find((o: { id: string }) => o.id === section.check.answer);
    await chapter.locator(".options button").nth(section.check.options.indexOf(answer)).click();
    await chapter.getByRole("button", { name: "Check answer", exact: true }).click();
    await expect(chapter).toContainText("CHECK PASSED");
    if (i < 3) {
      await expect(outline.getByRole("button").nth(i + 1)).toBeEnabled();
      await chapter.getByRole("button", { name: "Continue to next chapter" }).click();
      await expect(page.locator(`#chapter-${module.sections[i + 1].id}`)).toBeFocused();
    }
    if (i === 0) {
      await page.reload();
      await expect(page.locator(`#chapter-${section.id}`)).toContainText("CHECK PASSED");
    }
  }
  await expect(page.getByText("GUIDE COMPLETE", { exact: true })).toBeVisible();
  await page.reload();
  await expect(page.getByText("4 / 4 complete", { exact: true })).toBeVisible();
  for (const viewport of [{ width: 393, height: 851 }, { width: 1280, height: 900 }]) {
    await page.setViewportSize(viewport);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBeTruthy();
    await page.screenshot({ path: `test-results/learning-${viewport.width}.png`, fullPage: true });
  }
});
