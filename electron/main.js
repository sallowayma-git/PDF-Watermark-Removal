const { app, BrowserWindow, dialog } = require('electron');
const { spawn } = require('child_process');
const fs = require('fs');
const net = require('net');
const path = require('path');

let backendProcess = null;

function getBackendExecutableName() {
  return process.platform === 'win32' ? 'pdfwm_backend.exe' : 'pdfwm_backend';
}

function getBundledBackendCommandPath() {
  const exeName = getBackendExecutableName();
  const baseDir = app.isPackaged
    ? path.join(process.resourcesPath, 'backend', 'pdfwm_backend')
    : path.join(app.getAppPath(), 'backend', 'pdfwm_backend');
  return path.join(baseDir, exeName);
}

async function getFreePort() {
  return await new Promise((resolve, reject) => {
    const server = net.createServer();
    server.unref();
    server.on('error', reject);
    server.listen(0, '127.0.0.1', () => {
      const { port } = server.address();
      server.close(() => resolve(port));
    });
  });
}

async function waitForHealth(origin, timeoutMs = 20000) {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    try {
      const resp = await fetch(`${origin}/health`, { method: 'GET' });
      if (resp.ok) return;
    } catch (_) {}
    await new Promise((r) => setTimeout(r, 250));
  }
  throw new Error('Backend health check timed out');
}

async function startBackend() {
  const port = await getFreePort();
  const origin = `http://127.0.0.1:${port}`;

  const bundledBackend = getBundledBackendCommandPath();
  const hasBundledBackend = fs.existsSync(bundledBackend);

  if (!hasBundledBackend) {
    throw new Error(`Bundled backend not found: ${bundledBackend}`);
  }

  const logDir = app.getPath('userData');
  const logPath = path.join(logDir, 'backend.log');
  try {
    fs.mkdirSync(logDir, { recursive: true });
  } catch (_) {}
  const logStream = fs.createWriteStream(logPath, { flags: 'a' });
  logStream.write(`\n\n=== backend start ${new Date().toISOString()} ===\n`);
  logStream.write(`command: ${bundledBackend}\n`);
  logStream.write(`origin: ${origin}\n`);

  backendProcess = spawn(bundledBackend, [], {
    env: {
      ...process.env,
      HOST: '127.0.0.1',
      PORT: String(port),
      FLASK_DEBUG: '0',
      DATA_DIR: path.join(app.getPath('userData'), 'backend-data')
    },
    stdio: 'pipe'
  });

  backendProcess.stdout.on('data', (d) => {
    const s = String(d);
    try {
      logStream.write(s);
    } catch (_) {}
  });
  backendProcess.stderr.on('data', (d) => {
    const s = String(d);
    try {
      logStream.write(s);
    } catch (_) {}
  });

  backendProcess.on('exit', (code, signal) => {
    backendProcess = null;
    try {
      logStream.write(`\n=== backend exit code=${code} signal=${signal} ===\n`);
      logStream.end();
    } catch (_) {}
  });

  try {
    await waitForHealth(origin);
  } catch (err) {
    dialog.showErrorBox(
      'Backend start failed',
      `无法启动内置后端服务。\n\n后端：${bundledBackend}\n日志：${logPath}\n\n${err.message}`
    );
    throw err;
  }

  return { origin };
}

async function createWindow() {
  const win = new BrowserWindow({
    width: 1100,
    height: 760
  });

  const { origin } = await startBackend();
  await win.loadURL(origin);
}

app.whenReady().then(async () => {
  try {
    await createWindow();
  } catch (_) {
    app.quit();
  }
});

app.on('window-all-closed', () => {
  if (backendProcess) {
    backendProcess.kill();
    backendProcess = null;
  }
  if (process.platform !== 'darwin') app.quit();
});

