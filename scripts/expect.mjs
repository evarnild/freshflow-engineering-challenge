// The handful of `expect` matchers the kit's tests use, on top of node:assert,
// so `node --test` runs them with no dependency whatever stack the project
// picks. Add a matcher here when a test needs one; keep the names Vitest's.
import assert from 'node:assert/strict';

export function expect(actual, message) {
  return {
    toBe: (v) => assert.strictEqual(actual, v, message),
    toEqual: (v) => assert.deepStrictEqual(actual, v, message),
    toMatchObject: (v) => {
      for (const [k, x] of Object.entries(v)) assert.deepStrictEqual(actual?.[k], x, message ?? `.${k}`);
    },
    toBeNull: () => assert.strictEqual(actual, null, message),
    toBeUndefined: () => assert.strictEqual(actual, undefined, message),
    toContain: (v) => assert.ok(actual.includes(v), message ?? `expected ${JSON.stringify(actual)} to contain ${JSON.stringify(v)}`),
    toMatch: (re) => assert.match(actual, re, message),
    toHaveLength: (n) => assert.strictEqual(actual.length, n, message ?? `expected length ${n}, got ${JSON.stringify(actual)}`),
    toThrow: (re) => assert.throws(actual, re, message),
  };
}
