import test from 'node:test';
import assert from 'node:assert/strict';
import { parseArgs, pythonArgs } from '../scripts/playwright-android.mjs';

test('help requires no Android connection', () => {
  assert.equal(parseArgs(['--help']).help, true);
});
test('offer listing invokes original Python without checkout', () => {
  const o = parseArgs(['offers', '--plan', 'pro6', '--serial', 'emulator-5554']);
  assert.deepEqual(pythonArgs(o, o.serial), ['ultra0.py', '--account', 'current@device', '--no-add', '--list', '--plan', 'pro6', '--serial', 'emulator-5554']);
});
test('live checkout cannot start accidentally', () => {
  assert.throws(() => parseArgs(['run', '--step', '1', '--email', 'test@example.com']), /acknowledge-live-checkout/);
  assert.throws(() => parseArgs(['run', '--step', '1', '--email', 'current@device', '--acknowledge-live-checkout']), /actual target/);
});
test('each step maps onto original named offer without --force', () => {
  for (const step of ['1','2','3','extra']) {
    const o = parseArgs(['run','--step',step,'--email','test@example.com','--dry-run']);
    const args = pythonArgs(o,'emulator-5554');
    assert.ok(args.includes('--no-switch'));
    assert.ok(!args.includes('--force'));
    assert.equal(args.includes('--stack'), step !== '1');
    assert.ok(args.includes('--serial'));
  }
});
test('bad options fail before Android connect', () => {
  assert.throws(() => parseArgs(['wat']), /Unknown command/);
  assert.throws(() => parseArgs(['doctor', '--step', '1']), /apply to run/);
  assert.throws(() => parseArgs(['offers', '--plan', 'not-a-plan']), /Invalid plan/);
});
