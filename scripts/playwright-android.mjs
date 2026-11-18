#!/usr/bin/env node
/**
 * Additive Android/Playwright wrapper. Does not modify ultra0.py.
 * Without --acknowledge-live-checkout, this file never invokes a checkout.
 */
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';
import { spawn } from 'node:child_process';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
export const STEPS = Object.freeze({
  '1': { plan: 'pro12', stack: false },
  '2': { plan: 'pro6', stack: true },
  '3': { plan: 'pro6b', stack: true },
  extra: { plan: 'pro6c', stack: true },
});

const HELP = `Android Playwright wrapper (preserves the original Python/Frida logic)

Usage:
  node scripts/playwright-android.mjs doctor [--serial SERIAL] [--browser-check] [--screenshot PATH]
  node scripts/playwright-android.mjs offers [--serial SERIAL] [--plan pro12|pro6|pro6b|pro6c]
  node scripts/playwright-android.mjs run --step 1|2|3|extra --email ACCOUNT [--serial SERIAL] [--dry-run]
  node scripts/playwright-android.mjs run --step 1|2|3|extra --email ACCOUNT --acknowledge-live-checkout

This requires a connected Android emulator/device (ADB), Python and Frida.
Playwright only does device checks and optional browser checks; the ORIGINAL
Python script handles BillingClient. It may automatically tap Subscribe.
The tool does not guarantee any discount, offer eligibility, or term length.
`;

export function parseArgs(argv) {
  const options = { command: null, serial: null, plan: 'pro12', step: null,
    email: null, screenshot: null, browserCheck: false,
    dryRun: false, acknowledge: false, help: false };
  const flags = new Set(['--browser-check', '--dry-run', '--acknowledge-live-checkout']);
  const values = new Map([
    ['--serial', 'serial'], ['--plan', 'plan'], ['--step', 'step'],
    ['--email', 'email'], ['--screenshot', 'screenshot'],
  ]);
  let i = 0;
  if (argv[i] === '--help' || argv[i] === '-h' || argv.length === 0) {
    options.help = true;
    return options;
  }
  const command = argv[i++];
  if (!['doctor', 'offers', 'run'].includes(command)) {
    throw new Error(`Unknown command: ${command}`);
  }
  options.command = command;
  const used = new Set();
  for (; i < argv.length; i++) {
    const arg = argv[i];
    if (arg === '--help' || arg === '-h') { options.help = true; return options; }
    if (used.has(arg)) throw new Error(`Duplicate option: ${arg}`);
    used.add(arg);
    if (flags.has(arg)) {
      if (arg === '--browser-check') options.browserCheck = true;
      if (arg === '--dry-run') options.dryRun = true;
      if (arg === '--acknowledge-live-checkout') options.acknowledge = true;
      continue;
    }
    if (values.has(arg)) {
      const value = argv[++i];
      if (!value || value.startsWith('--')) throw new Error(`Expected value after ${arg}`);
      options[values.get(arg)] = value;
      continue;
    }
    throw new Error(`Unknown argument: ${arg}`);
  }
  if (options.plan && !['pro12', 'pro6', 'pro6b', 'pro6c'].includes(options.plan)) {
    throw new Error('Invalid plan; expected pro12, pro6, pro6b or pro6c');
  }
  if (options.command === 'run') {
    if (!STEPS[options.step]) throw new Error('run requires --step 1|2|3|extra');
    if (!options.email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(options.email)) {
      throw new Error('run requires an actual target --email (current@device is not accepted)');
    }
    if (!options.dryRun && !options.acknowledge) {
      throw new Error('Original checkout may auto-confirm purchases; supply --acknowledge-live-checkout or --dry-run');
    }
  } else if (options.step || options.email || options.acknowledge || options.dryRun) {
    throw new Error('--step, --email, --dry-run and --acknowledge-live-checkout apply to run only');
  }
  if (options.browserCheck && command !== 'doctor') throw new Error('--browser-check applies to doctor only');
  if (options.screenshot && command !== 'doctor') throw new Error('--screenshot applies to doctor only');
  return options;
}

export function pythonArgs(options, serial) {
  if (options.command === 'offers') {
    return ['ultra0.py', '--account', 'current@device', '--no-add', '--list', '--plan', options.plan,
      ...(serial ? ['--serial', serial] : [])];
  }
  if (options.command === 'run') {
    const step = STEPS[options.step];
    return ['ultra0.py', '--account', options.email, '--no-add', '--no-switch', '--plan', step.plan,
      ...(step.stack ? ['--stack'] : []), ...(serial ? ['--serial', serial] : [])];
  }
  throw new Error('doctor does not run Python');
}

async function checkDevice(options) {
  let android;
  try {
    ({ _android: android } = await import('playwright'));
  } catch {
    throw new Error('Playwright is not installed. Run npm install first.');
  }
  const devices = await android.devices();
  if (devices.length === 0) throw new Error('No Android device found. Start MuMu, enable ADB, and check adb devices.');
  const matching = options.serial ? devices.filter(d => d.serial() === options.serial) : devices;
  if (matching.length !== 1) {
    const choices = devices.map(d => `${d.serial()} (${d.model()})`).join(', ');
    throw new Error(`Expected exactly one device; use --serial SERIAL. Found: ${choices}`);
  }
  const device = matching[0];
  try {
    console.log(`Playwright Android: ${device.model()} (${device.serial()})`);
    for (const pkg of ['com.android.vending', 'com.google.android.apps.subscriptions.red']) {
      const reply = (await device.shell(`pm path ${pkg}`)).toString('utf8').trim();
      if (!reply.includes('package:')) throw new Error(`Required Android package not installed: ${pkg}`);
      console.log(`Verified Android package: ${pkg}`);
    }
    if (options.screenshot) {
      await device.screenshot({ path: resolve(options.screenshot) });
      console.log('Device screenshot saved locally; do not upload it to public CI artifacts.');
    }
    if (options.browserCheck) {
      const context = await device.launchBrowser();
      try {
        const page = await context.newPage();
        await page.goto('https://example.com/', { waitUntil: 'domcontentloaded', timeout: 20_000 });
        console.log(`Chrome smoke test: ${await page.title()}`);
      } finally { await context.close(); }
    }
    return device.serial();
  } finally {
    await device.close();
  }
}

async function runPython(args) {
  const python = process.env.PYTHON || (process.platform === 'win32' ? 'python' : 'python3');
  const child = spawn(python, args, { cwd: ROOT, stdio: 'inherit', shell: false,
    env: { ...process.env, PYTHONIOENCODING: 'utf-8' } });
  return await new Promise((resolve, reject) => {
    child.once('error', reject);
    child.once('exit', (code, signal) => resolve(signal ? 1 : (code ?? 1)));
  });
}

async function main(argv) {
  const options = parseArgs(argv);
  if (options.help) { console.log(HELP); return 0; }
  if (options.dryRun) {
    console.log('Dry-run only; no device, Python or checkout launched.');
    console.log(`Python arguments: ${JSON.stringify(pythonArgs(options, options.serial))}`);
    return 0;
  }
  const serial = await checkDevice(options);
  if (options.command === 'doctor') return 0;
  if (options.command === 'run') {
    console.warn('WARNING: Running the ORIGINAL Python code. It may auto-click Subscribe.');
    console.warn('Verify the signed-in account and Google Play payment/renewal terms.');
  }
  return await runPython(pythonArgs(options, serial));
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main(process.argv.slice(2)).then(code => { process.exitCode = code; }).catch(err => {
    console.error(`ERROR: ${err.message}`);
    process.exitCode = 1;
  });
}
