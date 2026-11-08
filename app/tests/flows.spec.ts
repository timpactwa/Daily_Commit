import { expect, test, type Page } from "@playwright/test";
import type { AnswerResult, PublicQuestion } from "../src/api";
import { learningFor } from "../src/learning/feedback";

test("teaching distinguishes exact search, insertion points and exponentiation", () => {
  const note = (topic: string, name: string) =>
    learningFor(
      { topic } as PublicQuestion,
      {
        provenance: { source_function: `pipeline/corpus/${name}.py::fn` },
      } as AnswerResult,
    );
  expect(note("binary-search", "binary_search")?.principle).toContain(
    "both valid candidate indices",
  );
  expect(note("binary-search", "lower_bound")?.principle).toContain(
    "half-open",
  );
  expect(note("binary-search", "lower_bound")?.example).toContain(
    "insertion point is 4",
  );
  expect(note("recursion", "power")?.example).toContain("2^5");
  expect(note("recursion", "power")?.reasoning).toContain("27");
  // New functions can still receive topic guidance without guessing a repair.
  expect(note("sorting", "future_function")?.concept).toBe(
    "Preserving order and elements",
  );
  expect(note("future-topic", "future_function")).toBeUndefined();
});
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
    page.getByText("Level 3", { exact: true }).first(),
  ).toBeVisible();
  await page.getByRole("link", { name: "Let’s make a daily habit" }).click();
  await expect(
    page.getByRole("heading", { name: "Keep showing up, Liam." }),
  ).toBeVisible();
}
test("placement, all four question formats, feedback, completion and progress", async ({
  page,
}) => {
  test.setTimeout(60000);
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await createAndPlace(page);
  await page.getByRole("link", { name: "Make today’s commit" }).click();
  for (let i = 0; i < 4; i++) {
    await selectQuestion(page);
    await expect(
      page.getByRole("heading", { name: "Why this works" }),
    ).toHaveCount(0);
    await page.getByRole("button", { name: "Check answer" }).click();
    await expect(
      page.getByRole("region", { name: "Answer feedback" }),
    ).toContainText("Elo");
    const feedback = page.getByRole("region", { name: "Answer feedback" });
    await expect(
      feedback.getByRole("heading", { name: "You got it. Here’s why." }),
    ).toBeFocused();
    await expect(
      feedback.getByRole("heading", { name: "Why this works" }),
    ).toBeVisible();
    await expect(
      feedback.getByRole("heading", { name: "A smaller example" }),
    ).toBeVisible();
    await feedback.getByText("Show the reasoning", { exact: true }).click();
    await expect(
      feedback.locator(".understanding-check details"),
    ).toHaveAttribute("open", "");
    await feedback
      .getByText("Read more about this concept", { exact: true })
      .click();
    const readings = feedback.locator(".further-reading a");
    await expect(readings).toHaveCount(2);
    for (const link of await readings.all()) {
      await expect(link).toBeVisible();
      await expect(link).toHaveAttribute("href", /^https:\/\//);
      await expect(link).toHaveAttribute("target", "_blank");
      await expect(link).toHaveAttribute("rel", /noopener/);
    }
    if (i === 3) {
      await feedback
        .getByText("Trace the failing case and the fix", { exact: true })
        .click();
      await expect(
        feedback.getByText("while lo < hi:", { exact: true }),
      ).toBeVisible();
      await expect(
        feedback.getByText("while lo <= hi:", { exact: true }),
      ).toBeVisible();
      await expect(feedback).toContainText("lo = hi = mid = 0");
    }
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBeTruthy();
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

test("wrong and partly ordered answers teach the reasoning and preserve the learner's answer", async ({
  page,
}) => {
  await createAndPlace(page);
  await page.getByRole("link", { name: "Make today’s commit" }).click();
  await page
    .getByRole("button", { name: "No cache; add read replicas" })
    .click();
  await page.getByRole("button", { name: "Check answer" }).click();
  const feedback = page.getByRole("region", { name: "Answer feedback" });
  await expect(
    feedback.getByRole("heading", { name: "Let’s work through it." }),
  ).toBeFocused();
  await expect(feedback).toContainText(
    "Your answer: No cache; add read replicas",
  );
  await expect(feedback).toContainText("Correct answer: Cache-aside");
  await expect(feedback).toContainText("A price update makes that copy stale");
  await page.getByRole("button", { name: "Continue" }).click();
  await selectQuestion(page);
  await page.getByRole("button", { name: "Check answer" }).click();
  await page.getByRole("button", { name: "Continue" }).click();
  // Swap the first two steps, preserving the other pairwise relationships.
  for (const text of [
    /API records/,
    /Client uploads/,
    /Worker pulls/,
    /Worker writes/,
    /Client is notified/,
  ]) {
    await page.getByRole("button", { name: text }).click();
  }
  await page.getByRole("button", { name: "Check answer" }).click();
  await expect(
    feedback.getByRole("heading", {
      name: "Partly there. Let’s connect the steps.",
    }),
  ).toBeVisible();
  await expect(feedback).toContainText("Your answer: API records");
  await expect(feedback).toContainText("Correct answer: Client uploads");
  await expect(
    feedback.getByRole("heading", { name: "Why this works" }),
  ).toBeVisible();
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

test("source citations are usable HTTPS links and other markup stays plain text", async ({ page }) => {
  await createAndPlace(page);
  await page.evaluate(async () => {
    const clientPath = "/src/api/client.ts";
    const mockPath = "/src/api/mock.ts";
    const { setTransport } = await import(clientPath);
    const { mockTransport } = await import(mockPath);
    setTransport(async (method: string, path: string, body: unknown, headers: Record<string, string>) => {
      const response = await mockTransport(method, path, body, headers);
      if (path === "/v1/answers") {
        response.json = { ...response.json, explanation: 'Check the rule. Source: [RFC 9111](https://www.rfc-editor.org/rfc/rfc9111.html) <img src=x onerror=alert(1)> [unsafe](javascript:alert(1)) [invalid](https://[)' };
      }
      return response;
    });
  });
  await page.getByRole("link", { name: "Make today’s commit" }).click();
  await selectQuestion(page);
  await page.getByRole("button", { name: "Check answer" }).click();
  const feedback = page.getByRole("region", { name: "Answer feedback" });
  const citation = feedback.getByRole("link", { name: "RFC 9111" });
  await expect(citation).toHaveAttribute("href", "https://www.rfc-editor.org/rfc/rfc9111.html");
  await expect(citation).toHaveAttribute("rel", "noopener noreferrer");
  await expect(feedback.getByRole("link")).toHaveCount(1);
  await expect(feedback.locator("img")).toHaveCount(0);
  await expect(feedback).toContainText("[unsafe](javascript:alert(1))");
});

test("failing tests precede code and skill levels explain the higher thresholds", async ({ page }) => {
  await createAndPlace(page);
  await page.getByRole('link', { name: 'Make today’s commit' }).click();
  for (let i = 0; i < 3; i++) {
    await selectQuestion(page);
    await page.getByRole('button', { name: 'Check answer' }).click();
    await page.getByRole('button', { name: 'Continue' }).click();
  }
  const failures = page.getByRole('region', { name: 'Failing tests' });
  const code = page.getByLabel('Select the buggy line');
  await expect(failures).toBeVisible();
  await expect(code).toBeVisible();
  expect(await failures.evaluate(el => !!(el.compareDocumentPosition(document.querySelector('.question .code')!) & Node.DOCUMENT_POSITION_FOLLOWING))).toBeTruthy();
  const testBox = await failures.boundingBox();
  const codeBox = await code.boundingBox();
  expect(testBox!.y + testBox!.height).toBeLessThanOrEqual(codeBox!.y);
  await page.getByRole('link', { name: 'Progress', exact: false }).last().click();
  const ladder = page.getByRole('region', { name: 'Skill level requirements' });
  await expect(ladder.locator('li')).toHaveCount(7);
  await expect(ladder).toContainText('1650–1899 Elo');
  await expect(ladder).toContainText('Level 7');
});

test("background flows faster and respects reduced motion", async ({ page }) => {
  await page.goto('/');
  const duration = await page.locator('.b1').evaluate(el => parseFloat(getComputedStyle(el).animationDuration));
  expect(duration).toBeGreaterThan(0);
  expect(duration).toBeLessThanOrEqual(15);
  await page.emulateMedia({ reducedMotion: 'reduce' });
  expect(await page.locator('.b1').evaluate(el => getComputedStyle(el).animationName)).toBe('none');
});
