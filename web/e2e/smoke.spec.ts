import { test, expect } from "@playwright/test";

async function loginDemo(page: import("@playwright/test").Page) {
  await page.goto("/login");
  await page.getByRole("button", { name: "Crear cuenta demo" }).click();
  await expect(page.locator("code")).toBeVisible({ timeout: 15_000 });
  await page.getByRole("button", { name: "Entrar al panel" }).click();
  await expect(page.getByRole("heading", { name: "Overview" })).toBeVisible({ timeout: 15_000 });
}

test("login demo y ver overview", async ({ page }) => {
  await loginDemo(page);
  await expect(page).toHaveURL("/");
});

test("navegar a whales", async ({ page }) => {
  await loginDemo(page);
  await page.getByRole("link", { name: "Whales" }).click();
  await expect(page.getByRole("heading", { name: "Whales" })).toBeVisible();
});
