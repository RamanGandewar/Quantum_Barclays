import { expect, test } from "@playwright/test";

test("dashboard renders PRD views", async ({ page }) => {
  await page.goto("http://127.0.0.1:3000");
  await expect(page.getByText("Post-Quantum Migration Control Plane")).toBeVisible();
  await expect(page.getByText("Handshake Comparison")).toBeVisible();
  await expect(page.getByText("Migration State Machine")).toBeVisible();
  await expect(page.getByText("Risk Analysis")).toBeVisible();
  await expect(page.getByText("Live Connection Evidence")).toBeVisible();
});
