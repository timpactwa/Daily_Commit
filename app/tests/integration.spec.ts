import { expect, test } from "@playwright/test";
import { readFileSync } from "node:fs";

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
    if (q.format === "tap_line")
      await page.getByRole("button", { name: /^Line 1:/ }).click();
    else if (q.format === "reorder") {
      for (let i = 0; i < q.options.length; i++)
        await page.locator(".reorder .options button").first().click();
    } else await page.locator(".options button").first().click();
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
