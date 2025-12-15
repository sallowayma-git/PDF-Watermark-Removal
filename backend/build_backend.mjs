import { spawnSync } from 'node:child_process';

function tryRun(cmd, args) {
  const res = spawnSync(cmd, args, { stdio: 'inherit' });
  if (res.status === 0) return true;
  return false;
}

const python = process.env.PYTHON_BIN || process.env.PYTHON || null;
const args = ['backend/build_backend.py'];

if (python) {
  process.exit(tryRun(python, args) ? 0 : 1);
}

if (tryRun('python3', args)) process.exit(0);
if (tryRun('python', args)) process.exit(0);

console.error('Python not found. Set PYTHON_BIN (or PYTHON) to your Python executable.');
process.exit(1);

