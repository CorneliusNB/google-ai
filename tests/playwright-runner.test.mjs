import test from 'node:test';
import assert from 'node:assert/strict';
import { parseArgs, pythonArgs } from '../scripts/playwright-android.mjs';

test('help requires no Android connection', () => {
  assert.equal(parseArgs(['--help']).help, true);
});
test('offer listing invokes original Python without checkout', () => {
  const o = parseArgs(['offers', '--plan', 'pro6', '--serial', 'emulator-5554']);
  assert.deepEqual(pythonArgs(o, o.serial), ['ultra0.py', '--account', 'current@device', '--no-add', '--force', '--list', '--plan', 'pro6', '--serial', 'emulator-5554']);
});
test('live checkout cannot start accidentally', () => {
  assert.throws(() => parseArgs(['run', '--step', '1', '--email', 'test@example.com']), /acknowledge-live-checkout/);
  assert.throws(() => parseArgs(['run', '--step', '1', '--email', 'not-an-email', '--acknowledge-live-checkout']), /Invalid --email/);
});
test('each step maps to the exact original .bat flags by default', () => {
  for (const step of ['1','2','3','extra']) {
    const o = parseArgs(['run','--step',step,'--dry-run']);
    const args = pythonArgs(o,'emulator-5554');
    assert.ok(args.includes('--force'));
    assert.ok(!args.includes('--no-switch'));
    assert.deepEqual(args.slice(0, 4), ['ultra0.py', '--account', 'current@device', '--no-add']);
    assert.equal(args.includes('--stack'), step !== '1');
    assert.ok(args.includes('--serial'));
  }
});
test('bad options fail before Android connect', () => {
  assert.throws(() => parseArgs(['wat']), /Unknown command/);
  assert.throws(() => parseArgs(['doctor', '--step', '1']), /apply to run/);
  assert.throws(() => parseArgs(['offers', '--plan', 'not-a-plan']), /Invalid plan/);
});

test('optional email overrides original account placeholder without changing flags', () => {
  const o = parseArgs(['run','--step','2','--email','example@example.com','--dry-run']);
  assert.deepEqual(pythonArgs(o, null), ['ultra0.py','--account','example@example.com','--no-add','--force','--plan','pro6','--stack']);
});
