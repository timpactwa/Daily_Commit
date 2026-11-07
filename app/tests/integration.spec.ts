import { expect, test } from "@playwright/test";
test("built PWA against real API: demo, feedback, completion, progress, offline retry", async ({
  page,
  request,
  context,
}) => {
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
