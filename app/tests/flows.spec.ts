import { expect, test, type Page } from "@playwright/test";
async function selectQuestion(page: Page) {
  await expect(page.locator(".question h2")).toBeVisible();
  if (
    await page
      .getByRole("heading", { name: "Which caching strategy fits best?" })
      .isVisible()
  )
    await page.getByRole("button", { name: /Cache-aside with a TTL/ }).click();
  else if (
    await page.getByRole("heading", { name: "Tap the bottleneck." }).isVisible()
  )
    await page
      .getByRole("button", { name: /Session store/ })
      .first()
      .click();
  else if (
    await page.getByRole("heading", { name: /Put the steps/ }).isVisible()
  ) {
    for (const text of [
      /Client uploads/,
      /API records/,
      /Worker pulls/,
      /Worker writes/,
      /Client is notified/,
    ])
      await page.getByRole("button", { name: text }).click();
  } else await page.getByRole("button", { name: /^Line 3:/ }).click();
}
async function createAndPlace(page: Page) {
  await page.goto("/");
  await page.getByLabel("What should we call you?").fill("Liam");
  await page.getByRole("button", { name: "Find my starting point" }).click();
  for (let i = 0; i < 4; i++) {
    await expect(page.getByRole("progressbar")).toHaveAttribute(
      "value",
      String(i),
    );
    await selectQuestion(page);
    await page
      .getByRole("button", {
        name: i === 3 ? "See my starting point" : "Next question",
      })
      .click();
  }
  await expect(
    page.getByText("YOUR STARTING POINT", { exact: true }),
  ).toBeVisible();
  await expect(
    page.getByText("advanced", { exact: true }).first(),
  ).toBeVisible();
  await page.getByRole("link", { name: "Let’s make a daily habit" }).click();
  await expect(
    page.getByRole("heading", { name: "Keep showing up, Liam." }),
  ).toBeVisible();
}
test("placement, all four question formats, feedback, completion and progress", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await createAndPlace(page);
  await page.getByRole("link", { name: "Make today’s commit" }).click();
  for (let i = 0; i < 4; i++) {
    await selectQuestion(page);
    await page.getByRole("button", { name: "Check answer" }).click();
    await expect(
      page.getByRole("region", { name: "Answer feedback" }),
    ).toContainText("Elo");
    await page.getByRole("button", { name: "Continue" }).click();
  }
  await page.getByRole("button", { name: "Finish lesson" }).click();
  await expect(
    page.getByRole("heading", { name: "You showed up. That’s what counts." }),
  ).toBeVisible();
  await expect(page.getByText("4 of 4 answers correct.")).toBeVisible();
  await page.getByRole("link", { name: "View my progress" }).click();
  await expect(page.getByText("OVERALL READINESS")).toBeVisible();
  await expect(page.getByRole("progressbar")).toHaveCount(10);
  expect(errors).toEqual([]);
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBeTruthy();
});
test("long press switches to demo and completion extends streak from six to seven", async ({
  page,
}) => {
  await page.goto("/");
  const logo = page.getByRole("button", { name: /^Daily Commit home/ });
  await logo.dispatchEvent("pointerdown");
  await page.waitForTimeout(1100);
  await logo.dispatchEvent("pointerup");
  await expect(
    page.getByRole("heading", { name: "Keep showing up, Tim." }),
  ).toBeVisible();
  await expect(page.getByLabel("6 day streak")).toBeVisible();
  await page.getByRole("link", { name: "Make today’s commit" }).click();
  for (let i = 0; i < 4; i++) {
    await selectQuestion(page);
    await page.getByRole("button", { name: "Check answer" }).click();
    await page.getByRole("button", { name: "Continue" }).click();
  }
  await page.getByRole("button", { name: "Finish lesson" }).click();
  await expect(page.getByLabel("7 day streak")).toBeVisible();
});
test("reorder allows undo and requires every step", async ({ page }) => {
  await page.goto("/");
  await page.getByLabel("What should we call you?").fill("Liam");
  await page.getByRole("button", { name: "Find my starting point" }).click();
  for (let i = 0; i < 2; i++) {
    await selectQuestion(page);
    await page.getByRole("button", { name: "Next question" }).click();
  }
  await expect(
    page.getByRole("button", { name: "Next question" }),
  ).toBeDisabled();
  await page.getByRole("button", { name: /Client uploads/ }).click();
  await page.getByRole("button", { name: /^Remove step 1/ }).click();
  await expect(page.getByText("0 of 5 steps ordered")).toBeVisible();
  await selectQuestion(page);
  await expect(
    page.getByRole("button", { name: "Next question" }),
  ).toBeEnabled();
});
