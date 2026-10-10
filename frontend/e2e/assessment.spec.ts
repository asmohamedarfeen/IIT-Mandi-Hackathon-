import { test, expect } from '@playwright/test';
import { readFile } from 'node:fs/promises';

test('saved assessment, vessel focus, edit invalidation, reassessment and PDF', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByText('Model service ready', { exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Use this case' }).click();
  await page.getByRole('button', { name: 'Run assessment' }).click();
  const downloadButton = page.getByRole('button', { name: 'Download evidence report' });
  await expect(downloadButton).toBeEnabled();
  await page.getByRole('button', { name: 'Risk map', exact: true }).click();
  const vessels = page.getByLabel('Focus a coronary vessel');
  await vessels.getByRole('button', { name: /^RCA/ }).click();
  await expect(page.getByText('RCA · reference anatomy', { exact: true })).toBeVisible();
  const download = page.waitForEvent('download');
  await downloadButton.click();
  const report = await download;
  const path = await report.path();
  expect(path).toBeTruthy();
  expect((await readFile(path!)).subarray(0, 5).toString()).toBe('%PDF-');

  // Invalid edits must hide earlier evidence rather than display stale colors.
  const age = page.getByLabel(/^Age/).first();
  await age.fill('');
  await expect(downloadButton).toBeDisabled();
  await expect(page.getByText('Inputs changed — reassess', { exact: true })).toBeVisible();
  await age.fill('61');
  await expect(downloadButton).toBeEnabled({ timeout: 90_000 });
});

test('unavailable API leaves assessment disabled and retry visible', async ({ page }) => {
  await page.route('**/api/v1/health', route => route.fulfill({ status: 503, contentType: 'application/json', body: '{"models_ready":false}' }));
  await page.goto('/');
  await expect(page.getByText('Model service unavailable', { exact: true })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Run assessment' })).toBeDisabled();
  await expect(page.getByRole('button', { name: 'Recheck model service' })).toBeEnabled();
});

test('WebGL unavailable keeps vessel details accessible by keyboard', async ({ page }) => {
  await page.addInitScript(() => {
    const original = HTMLCanvasElement.prototype.getContext;
    Object.defineProperty(HTMLCanvasElement.prototype, 'getContext', {
      value: function (kind: string, ...args: unknown[]) {
        return kind.includes('webgl') ? null : Reflect.apply(original, this, [kind, ...args]);
      },
    });
  });
  await page.goto('/');
  await page.getByRole('button', { name: 'Risk map', exact: true }).click();
  await expect(page.getByText('The 3D view is unavailable in this browser.', { exact: true })).toBeVisible();
  const table = page.getByRole('table', { name: 'Coronary vessel assessment · reference anatomy' });
  await expect(table).toBeVisible();
  await expect(table.getByText('Awaiting assessment', { exact: true })).toHaveCount(3);
  const rca = table.getByRole('button', { name: 'Select RCA detail' });
  await rca.focus();
  await page.keyboard.press('Enter');
  await expect(rca).toHaveAttribute('aria-pressed', 'true');
  await expect(page.getByText('RCA · reference anatomy', { exact: true })).toBeVisible();
  const detail = page.getByRole('region', { name: /detail$/ });
  await expect(detail.getByRole('heading')).toBeVisible();
  // Playwright hit-testing verifies the fallback overlay does not cover details.
  await detail.getByRole('heading').click({ trial: true });
  await detail.getByRole('link', { name: 'View complete artery evidence ↓' }).click({ trial: true });
  await expect(page.getByRole('button', { name: 'Retry 3D view' })).toBeEnabled();
});

test('context loss presents fallback and retry replaces the canvas', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('button', { name: 'Risk map', exact: true }).click();
  const canvas = page.getByLabel('Interactive BodyParts3D reference heart', { exact: true });
  await expect(canvas).toBeVisible();
  // Dispatch the browser event to exercise recovery; this is not a hardware GPU test.
  await canvas.dispatchEvent('webglcontextlost', { cancelable: true });
  await expect(page.getByRole('table', { name: 'Coronary vessel assessment · reference anatomy' })).toBeVisible();
  await page.getByRole('button', { name: 'Retry 3D view' }).click();
  await expect(page.getByText('The 3D view is unavailable in this browser.', { exact: true })).toBeHidden();
  await expect(canvas).toHaveCount(1);
  await expect(canvas).toBeVisible();
});
