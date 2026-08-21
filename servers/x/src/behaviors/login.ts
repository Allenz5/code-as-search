import "dotenv/config";

import { BrowserContext, Page } from "playwright";
import { chromium, devices } from "playwright-extra";
import StealthPlugin from "puppeteer-extra-plugin-stealth";
import path from "path";

import { recordRateLimitHit } from "../utils";

function attachRateLimitListener(page: Page) {
  page.on("response", (response) => {
    if (response.status() !== 429) return;
    const url = response.url();
    if (!url.includes("x.com") && !url.includes("twitter.com")) return;
    recordRateLimitHit(page, { status: 429, url, at: Date.now() });
  });
}

chromium.use(StealthPlugin());

const authDir = process.env.AUTH_DIR || "playwright/.auth";
const authFile = path.join(authDir, "twitter.json");

const MANUAL_LOGIN_TIMEOUT_MS = parseInt(
  process.env.MANUAL_LOGIN_TIMEOUT_MS || "300000",
  10
);

function getProxyConfig() {
  const proxyUrl = process.env.PROXY_URL;
  if (!proxyUrl) {
    return undefined;
  }

  const proxyConfig = {
    server: proxyUrl,
    username: process.env.PROXY_USERNAME,
    password: process.env.PROXY_PASSWORD,
  };

  if (proxyUrl.includes("@")) {
    const match = proxyUrl.match(/^(https?:\/\/)(?:([^:]+):([^@]+)@)?(.+)$/);
    if (match) {
      proxyConfig.server = match[1] + match[4];
      proxyConfig.username = proxyConfig.username || match[2];
      proxyConfig.password = proxyConfig.password || match[3];
    }
  }

  console.log("Using proxy config:", proxyConfig);
  return {
    server: proxyConfig.server,
    ...(proxyConfig.username && { username: proxyConfig.username }),
    ...(proxyConfig.password && { password: proxyConfig.password }),
  };
}

async function createBrowser(opts: { headless?: boolean } = {}) {
  const proxyConfig = getProxyConfig();
  const headless =
    opts.headless ?? process.env.NODE_ENV !== "development";

  const browser = await chromium.launch({
    timeout: 60000,
    headless,
    slowMo: 1000,
    args: [
      "--no-sandbox",
      "--disable-setuid-sandbox",
      "--disable-dev-shm-usage",
      "--disable-accelerated-2d-canvas",
    ],
    ...(proxyConfig && { proxy: proxyConfig }),
  });

  return browser;
}

function isOnLoginFlow(page: Page) {
  const url = page.url();
  return (
    url.includes("/i/flow/login") ||
    url.includes("twitter.com/login") ||
    url.includes("x.com/login")
  );
}

async function waitForManualLogin(page: Page) {
  console.log(
    `Please log in manually in the visible Chromium window. ` +
      `Waiting up to ${Math.round(
        MANUAL_LOGIN_TIMEOUT_MS / 1000
      )}s for login to complete...`
  );

  const deadline = Date.now() + MANUAL_LOGIN_TIMEOUT_MS;
  while (Date.now() < deadline) {
    const cookies = await page.context().cookies();
    const authToken = cookies.find(
      (c) =>
        c.name === "auth_token" &&
        (c.domain.includes("x.com") || c.domain.includes("twitter.com"))
    );
    if (authToken && authToken.value) {
      console.log("Login detected. Saving auth state...");
      await saveState(page);
      return;
    }
    await page.waitForTimeout(1500);
  }

  throw new Error(
    `Manual login was not completed within ${Math.round(
      MANUAL_LOGIN_TIMEOUT_MS / 1000
    )}s (no auth_token cookie observed).`
  );
}

async function newContextWithStealth(
  browser: Awaited<ReturnType<typeof createBrowser>>,
  opts: { storageState?: string } = {}
): Promise<BrowserContext> {
  const context = await browser.newContext({
    ...devices["Desktop Chrome"],
    locale: "en-US",
    ...(opts.storageState ? { storageState: opts.storageState } : {}),
  });
  await context.addInitScript(
    "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
  );
  return context;
}

export async function getUnauthenticatedPage() {
  const browser = await createBrowser();
  const context = await newContextWithStealth(browser);
  const page = await context.newPage();
  attachRateLimitListener(page);

  return {
    page,
    close: async () => {
      await page.close();
      await context.close();
      await browser.close();
    },
  };
}

export async function getAuthenticatedPage() {
  let browser = await createBrowser();

  let context: BrowserContext;
  try {
    context = await newContextWithStealth(browser, { storageState: authFile });
  } catch (error) {
    console.log("No auth file found, creating new context...");
    context = await newContextWithStealth(browser);
  }

  let page = await context.newPage();
  attachRateLimitListener(page);
  await page.goto("https://x.com/home");

  if (isOnLoginFlow(page)) {
    console.log(
      "Not logged in. Relaunching browser in visible mode for manual login..."
    );
    await context.close();
    await browser.close();

    browser = await createBrowser({ headless: false });
    context = await newContextWithStealth(browser);

    page = await context.newPage();
    attachRateLimitListener(page);
    await page.goto("https://x.com/i/flow/login");

    await waitForManualLogin(page);
  }

  return {
    page,
    close: async () => {
      await page.close();
      await context.close();
      await browser.close();
    },
  };
}

export async function saveState(page: Page) {
  return page.context().storageState({ path: authFile });
}

export async function login() {
  const browser = await createBrowser({ headless: false });
  const context = await newContextWithStealth(browser);
  const page = await context.newPage();

  await page.goto("https://x.com/i/flow/login");

  await waitForManualLogin(page);

  await page.close();
  await context.close();
  await browser.close();

  console.log("Done!");
}
