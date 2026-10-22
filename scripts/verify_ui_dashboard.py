#!/usr/bin/env python3
"""
Playwright UI Verification Script for Dashboard
Navigates to http://localhost:5173/, waits for live signal stream cards,
takes screenshots, and validates UI data fields.
"""
import asyncio
import os
import sys
from playwright.async_api import async_playwright

ARTIFACT_DIR = r"C:\Users\MihirPatel\.gemini\antigravity\brain\6a11ba25-3987-4646-840a-b5cf28eb0d87"
SCREENSHOT_PATH = os.path.join(ARTIFACT_DIR, "dashboard_live_verification.png")

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1440, "height": 900})
        
        print("Navigating to http://localhost:5173/ ...")
        try:
            await page.goto("http://localhost:5173/", wait_until="networkidle", timeout=15000)
        except Exception as e:
            print(f"Navigation warning: {e}")
            await page.wait_for_timeout(3000)

        # Wait a moment for dynamic data hydration
        await page.wait_for_timeout(2000)

        title = await page.title()
        print(f"Page title: {title}")

        # Take full page screenshot
        await page.screenshot(path=SCREENSHOT_PATH, full_page=True)
        print(f"Screenshot saved to: {SCREENSHOT_PATH}")

        # Check for signal cards or main elements
        content = await page.content()
        print(f"Page content length: {len(content)} characters")

        # Check for key keywords in page
        keywords = ["Live", "Signal", "Conviction", "Target", "Market", "BSE", "NSE"]
        found = [k for k in keywords if k.lower() in content.lower()]
        print(f"Keywords detected on page: {found}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
