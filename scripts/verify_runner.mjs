import { spawn } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';

import http from 'node:http';

const ROUTES = [
  '/',
  '/terms',
  '/privacy',
  '/support'
];

const OUT = './shots';
const PORT = process.env.CHROME_PORT ? parseInt(process.env.CHROME_PORT, 10) : 9520;
const HTTP_PORT = process.env.HTTP_PORT ? parseInt(process.env.HTTP_PORT, 10) : 4185;
const BASE = `http://127.0.0.1:${HTTP_PORT}`;
const USER_DATA = path.resolve('./shots/chrome-profile');

const VIEWPORTS = {
  mobile: { width: 375, height: 667, mobile: true, deviceScaleFactor: 2 },
  tablet: { width: 768, height: 1024, mobile: true, deviceScaleFactor: 1 },
  desktop: { width: 1440, height: 900, mobile: false, deviceScaleFactor: 1 },
};

fs.mkdirSync(OUT, { recursive: true });

const mimeTypes = {
  '.html': 'text/html; charset=UTF-8',
  '.css': 'text/css; charset=UTF-8',
  '.js': 'application/javascript; charset=UTF-8',
  '.json': 'application/json; charset=UTF-8',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.ico': 'image/x-icon',
  '.txt': 'text/plain; charset=UTF-8',
  '.xml': 'application/xml; charset=UTF-8'
};

const server = http.createServer((req, res) => {
  let reqPath = decodeURI(req.url.split('?')[0]);
  let filePath = path.join(path.resolve('./public'), reqPath);
  if (fs.existsSync(filePath) && fs.statSync(filePath).isDirectory()) {
    filePath = path.join(filePath, 'index.html');
  } else if (!fs.existsSync(filePath) && fs.existsSync(filePath + '.html')) {
    filePath = filePath + '.html';
  } else if (!fs.existsSync(filePath)) {
    filePath = path.join(path.resolve('./public'), 'index.html');
  }

  try {
    const ext = path.extname(filePath).toLowerCase();
    const contentType = mimeTypes[ext] || 'application/octet-stream';
    const content = fs.readFileSync(filePath);
    res.writeHead(200, { 'Content-Type': contentType });
    res.end(content);
  } catch (err) {
    res.writeHead(404);
    res.end('Not found');
  }
});

await new Promise(r => server.listen(HTTP_PORT, '127.0.0.1', r));

const chrome = spawn('google-chrome', [
  '--headless=new',
  `--remote-debugging-port=${PORT}`,
  '--no-first-run',
  '--no-default-browser-check',
  '--autoplay-policy=no-user-gesture-required',
  '--mute-audio',
  '--renderer-process-limit=2',
  `--user-data-dir=${USER_DATA}`,
  'about:blank'
], { stdio: 'ignore' });

const sleep = (ms) => new Promise(r => setTimeout(r, ms));

let ws;
let seq = 0;
const pending = new Map();
let errors = [];

async function connect() {
  for (let i = 0; i < 60 && !ws; i++) {
    try {
      const list = await (await fetch(`http://127.0.0.1:${PORT}/json`)).json();
      const page = list.find(t => t.type === 'page');
      if (page) ws = new WebSocket(page.webSocketDebuggerUrl);
    } catch (e) {}
    if (!ws) await sleep(200);
  }
  if (!ws) throw new Error('Chrome did not expose a page target');
  await new Promise(r => ws.addEventListener('open', r));
  ws.addEventListener('message', (e) => {
    const m = JSON.parse(e.data);
    if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); }
    if (m.method === 'Runtime.exceptionThrown') {
      const d = m.params.exceptionDetails;
      errors.push(d.exception?.description || d.text);
    }
    if (m.method === 'Runtime.consoleAPICalled' && m.params.type === 'error') {
      errors.push(m.params.args.map(a => a.value ?? a.description).join(' '));
    }
  });
}

const send = (method, params = {}) => new Promise((r) => {
  const id = ++seq;
  pending.set(id, r);
  ws.send(JSON.stringify({ id, method, params }));
});

const evaluate = async (expression) =>
  (await send('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true })).result?.result?.value;

async function shot(file) {
  const r = await send('Page.captureScreenshot', { format: 'jpeg', quality: 72 });
  fs.writeFileSync(path.join(OUT, file), Buffer.from(r.result.data, 'base64'));
}

const slug = (p) => (p === '/' ? 'home' : p.replace(/^\//, '').replace(/[^\w-]+/g, '_'));

const report = [];

async function run() {
  try {
    await connect();
    await send('Runtime.enable');
    await send('Page.enable');
    await send('Network.enable');

    for (const route of ROUTES) {
      for (const [vpName, vp] of Object.entries(VIEWPORTS)) {
        await send('Emulation.setDeviceMetricsOverride', vp);
        errors = [];
        const url = `${BASE}${route}`;
        await send('Page.navigate', { url });
        await sleep(800);
        const base = `${slug(route)}_${vpName}.jpg`;
        await shot(base);

        const metrics = await evaluate(`({
          scrollWidth: document.documentElement.scrollWidth,
          clientWidth: document.documentElement.clientWidth,
          bodyScrollWidth: document.body ? document.body.scrollWidth : 0,
          overflowPx: document.documentElement.scrollWidth - document.documentElement.clientWidth,
          buttons: document.querySelectorAll("button, [role=button], a[href]").length,
          textLength: (document.body ? document.body.innerText : "").trim().length,
          imgsMissingAlt: [...document.images].filter(i => !i.hasAttribute("alt") || !i.alt.trim()).length,
          title: document.title
        })`);

        report.push({
          route,
          viewport: vpName,
          ...metrics,
          errors: [...errors]
        });
      }
    }
  } finally {
    try { ws?.close(); } catch(e) {}
    chrome.kill('SIGKILL');
    server?.close();
  }

  console.log('=== HEADLESS CHROME MULTI-VIEWPORT VERIFICATION REPORT ===');
  console.log(JSON.stringify(report, null, 2));
}

run();
