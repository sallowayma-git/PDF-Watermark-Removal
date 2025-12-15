const { app, BrowserWindow, dialog } = require('electron');
const path = require('path');
const net = require('net');
const { spawn } = require('child_process');
const fs = require('fs');

let backendProcess = null;

function getBackendExecutableName() {
  return process.platform === 'win32' ? 'pdfwm_backend.exe' : 'pdfwm_backend';
}

function getBundledBackendCommandPath() {
  const exeName = getBackendExecutableName();
  if (app.isPackaged) {
    const base = path.join(process.resourcesPath, 'backend', 'pdfwm_backend');
    if (fs.existsSync(base) && fs.statSync(base).isFile()) return base;
    const nested = path.join(base, exeName);
    if (fs.existsSync(nested)) return nested;
    return path.join(process.resourcesPath, 'backend', exeName);
  }
  const base = path.join(app.getAppPath(), 'backend', 'pdfwm_backend');
  if (fs.existsSync(base) && fs.statSync(base).isFile()) return base;
  const nested = path.join(base, exeName);
  if (fs.existsSync(nested)) return nested;
  return path.join(app.getAppPath(), 'backend', exeName);
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

function getBackendScriptPath() {
  if (app.isPackaged) {
    return path.join(process.resourcesPath, 'backend', 'app.py');
  }
  return path.join(app.getAppPath(), 'app.py');
}

async function waitForHealth(origin, timeoutMs = 20000) {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    try {
      const resp = await fetch(`${origin}/health`, { method: 'GET' });
      if (resp.ok) return;
    } catch (_) {}
    await new Promise((r) => setTimeout(r, 300));
  }
  throw new Error('Backend health check timed out');
}

async function startBackend() {
  const port = await getFreePort();
  const origin = `http://127.0.0.1:${port}`;

  const bundledBackend = getBundledBackendCommandPath();
  const hasBundledBackend = require('fs').existsSync(bundledBackend);

  const pythonCmd =
    process.env.PYTHON_BIN || (process.platform === 'win32' ? 'python' : 'python3');
  const scriptPath = getBackendScriptPath();

  const command = hasBundledBackend ? bundledBackend : pythonCmd;
  const args = hasBundledBackend ? [] : [scriptPath];

  backendProcess = spawn(command, args, {
    env: {
      ...process.env,
      HOST: '127.0.0.1',
      PORT: String(port),
      FLASK_DEBUG: '0',
      DATA_DIR: path.join(app.getPath('userData'), 'backend-data')
    },
    stdio: 'pipe'
  });

  backendProcess.on('exit', (code, signal) => {
    backendProcess = null;
    if (code !== 0) {
      console.error(`[backend] exited: code=${code} signal=${signal}`);
    }
  });

  backendProcess.stdout.on('data', (d) => console.log(`[backend] ${String(d).trimEnd()}`));
  backendProcess.stderr.on('data', (d) => console.error(`[backend] ${String(d).trimEnd()}`));

  try {
    await waitForHealth(origin);
  } catch (err) {
    const message =
      `无法启动后端服务。\n\n` +
      (hasBundledBackend
        ? `- 后端可执行文件：${bundledBackend}\n\n`
        : `- Python 命令：${pythonCmd}\n- 脚本路径：${scriptPath}\n\n`) +
      (hasBundledBackend
        ? `请检查可执行文件是否存在/未被系统拦截（macOS Gatekeeper、Windows Defender 等）。`
        : `请确认已安装 Python 以及依赖（opencv-python、PyMuPDF/fitz、fpdf、flask 等），并且命令行可以运行：${pythonCmd} -V`);
    dialog.showErrorBox('Backend start failed', `${message}\n\n${err.message}`);
    throw err;
  }

  return { origin };
}

async function createWindow() {
  const win = new BrowserWindow({
    width: 1100,
    height: 760,
    webPreferences: {
      sandbox: true
    }
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
