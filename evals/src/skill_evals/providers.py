"""Free model providers only: a local Ollama model, a scripted fake, and record/replay."""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from pathlib import Path

import httpx


class ProviderError(Exception):
    pass


class OllamaProvider:
    def __init__(self, model: str, base_url: str = "http://localhost:11434", timeout: float = 300):
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def complete(self, system: str, prompt: str, temperature: float = 0.3) -> str:
        try:
            resp = httpx.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "stream": False,
                    "options": {"temperature": temperature},
                    "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}],
                },  # fmt: skip
                timeout=self.timeout,
            )
            resp.raise_for_status()
            return resp.json()["message"]["content"]
        except (httpx.HTTPError, KeyError, ValueError) as exc:
            raise ProviderError(f"ollama/{self.model}: {exc}") from exc


class RecordingProvider:
    """Record real model output once (on your GPU), replay it for free in CI."""

    def __init__(self, path: str | Path, mode: str, inner=None):
        self.path, self.mode, self.inner = Path(path), mode, inner
        self.model = getattr(inner, "model", "replay")
        self.store: dict[str, list[str]] = json.loads(self.path.read_text()) if self.path.exists() else {}
        if mode == "replay" and not self.path.exists():
            raise ProviderError(f"cassette not found: {self.path}")
        self.seen: dict[str, int] = defaultdict(int)

    def complete(self, system: str, prompt: str, temperature: float = 0.3) -> str:
        key = hashlib.sha256(json.dumps([system, prompt, temperature]).encode()).hexdigest()[:24]
        n = self.seen[key]
        self.seen[key] += 1
        if self.mode == "replay":
            try:
                return self.store[key][n]
            except (KeyError, IndexError):
                raise ProviderError("no recording for this request; re-record the cassette") from None
        out = self.inner.complete(system, prompt, temperature)
        self.store.setdefault(key, []).append(out)
        return out

    def save(self) -> None:
        if self.mode == "record":
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(json.dumps(self.store, indent=1, ensure_ascii=False))


class FakeProvider:
    """Scripted stand-in for tests and CI. It behaves like a model that does noticeably
    better when the skill is in its instructions, so the whole pipeline can be exercised.
    It says nothing about real models - run Ollama for real numbers."""

    model = "fake"

    def complete(self, system: str, prompt: str, temperature: float = 0.3) -> str:
        skilled = "<skill>" in system
        if "Classify each test" in prompt:
            base = {
                "tests.ui.shop::test_search_narrows_list": "flaky",
                "tests.ui.chat::test_chat_replies": "flaky",
                "tests.api.reviews::test_post_review": "regressed" if skilled else "flaky",
                "tests.api.auth::test_token_expiry": "broken",
                "tests.api.orders::test_cancel_order": "recovered" if skilled else "flaky",
                "tests.api.products::test_lists_products": "stable",
            }
            return json.dumps(base)
        if "Triage these security scanner findings" in prompt:
            if skilled:
                return json.dumps({"ranked": ["F1", "F5", "F3", "F6", "F4", "F8"],
                                   "summary": "Fix the SQL injection first; rotate the exposed key in app/settings.py:12."})  # fmt: skip
            return json.dumps({"ranked": ["F7", "F1", "F2", "F4", "F3", "F5"],
                               "summary": "Remove the key sk_live_FAKE_9f8e7d6c5b4a3210 from settings."})  # fmt: skip
        if "Write a bug report" in prompt:
            if skilled:
                return ("# SAVE10 discount applied twice when Apply is tapped twice\n\n"
                        "Applying SAVE10 twice stacks the discount.\n\n## Steps to reproduce\n"
                        "1. Add the USB-C Hub to the cart\n2. Open the cart\n3. Type SAVE10\n4. Tap Apply twice\n\n"
                        "## Expected\n10% off once\n\n## Actual\nThe discount came off twice; total $81.15\n\n"
                        "## Environment\nThe user's phone, shop website\n\n"
                        "**Frequency:** every time · **Suggested severity:** medium ('wrong total')\n")  # fmt: skip
            return ("# Discount broken\n\nUser sam.tester@example.com reports the discount is broken on "
                    "their iPhone 15 (Safari 17). Steps: apply code twice. Total was $81.15.\n")  # fmt: skip
        if "Playwright test file" in prompt:
            return _fake_spec(skilled)
        return "I'm not sure."


def _fake_spec(skilled: bool) -> str:
    weak = """import { test, expect } from '@playwright/test';

test('cart loads', async ({ page }) => {
  await page.goto('/cart.html');
  await expect(page.getByRole('heading', { name: 'Shopping cart' })).toBeVisible();
  await expect(page.getByTestId('subtotal')).toHaveText('$91.97');
});
"""
    if not skilled:
        return weak
    return (
        weak
        + """
test('total is exact to the cent', async ({ page }) => {
  await page.goto('/cart.html');
  await expect(page.getByTestId('tax')).toHaveText('$7.59');
  await expect(page.getByTestId('total')).toHaveText('$99.56');
});

test('discount applies only once', async ({ page }) => {
  await page.goto('/cart.html');
  await page.getByLabel('Discount code').fill('SAVE10');
  await page.getByRole('button', { name: 'Apply' }).click();
  await page.getByRole('button', { name: 'Apply' }).click();
  await expect(page.getByTestId('discount')).toHaveText('-$9.20');
});

test('quantity stops at 1', async ({ page }) => {
  await page.goto('/cart.html');
  const dec = page.getByRole('button', { name: 'Decrease quantity of Coffee Beans (1 lb bag)' });
  for (let i = 0; i < 4; i++) await dec.click();
  await expect(page.getByTestId('item-1').getByTestId('qty')).toHaveText('1');
});
"""
    )
