import { expect, test } from "@playwright/test";

test("dashboard renders PRD views", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByText("Post-Quantum Migration Control Plane")).toBeVisible();
  await expect(page.getByText("Handshake Comparison")).toBeVisible();
  await expect(page.getByText("Migration State Machine")).toBeVisible();
  await expect(page.getByText("Risk Analysis")).toBeVisible();
  await expect(page.getByText("Live Connection Evidence")).toBeVisible();
});

test("toolbar profile buttons are visible", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("button", { name: /Classical/ })).toBeVisible();
  await expect(page.getByRole("button", { name: /Hybrid/ })).toBeVisible();
  await expect(page.getByRole("button", { name: /PQC Native/ })).toBeVisible();
  await expect(page.getByRole("button", { name: /KEMTLS/ })).toBeVisible();
});

test("KPI panels render with data", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByText("Endpoint")).toBeVisible();
  await expect(page.getByText("Risk")).toBeVisible();
  await expect(page.getByText("Certificate")).toBeVisible();
  await expect(page.getByText("Handshake")).toBeVisible();
  await expect(page.getByText("SSH State")).toBeVisible();
});

test("risk analysis controls are interactive", async ({ page }) => {
  await page.goto("/");
  const slider = page.locator('input[type="range"]');
  await expect(slider).toBeVisible();
  const select = page.locator("select");
  await expect(select).toBeVisible();
});

test("live indicator shows connection status", async ({ page }) => {
  await page.goto("/");
  const indicator = page.locator(".live-dot");
  await expect(indicator).toBeVisible();
  await expect(indicator).toHaveText(/LIVE|OFFLINE/);
});

test("state machine SVG renders", async ({ page }) => {
  await page.goto("/");
  const svg = page.locator('svg[aria-label="SMSM state diagram"]');
  await expect(svg).toBeVisible();
  const circles = svg.locator("circle");
  await expect(circles).toHaveCount(5);
});

test("API docs are reachable", async ({ request }) => {
  const response = await request.get("http://127.0.0.1:8000/docs");
  expect(response.ok()).toBeTruthy();
});
