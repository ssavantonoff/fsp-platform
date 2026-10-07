import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { runInNewContext } from "node:vm";
import ts from "typescript";
import { ApiError } from "../src/api";
import type { useInvitationPage } from "../src/components/invitation-page";

// Execute the production hook/handler bodies with deterministic state and refs.
export function functionSource(file: string, parent: string, name?: string): string {
  const source = ts.createSourceFile(file, readFileSync(file, "utf8"), ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
  let found: ts.FunctionDeclaration | undefined;
  function find(node: ts.Node) {
    if (ts.isFunctionDeclaration(node) && node.name?.text === (name ?? parent)) found = node;
    ts.forEachChild(node, find);
  }
  if (name) {
    const container = source.statements.find((node) => ts.isFunctionDeclaration(node) && node.name?.text === parent);
    assert.ok(container); find(container);
  } else find(source);
  assert.ok(found?.body, `${parent}/${name} production function is present`);
  return ts.transpileModule(found.getText(source).replace(/^export /, ""), { compilerOptions: { target: ts.ScriptTarget.ES2022 } }).outputText;
}
export function pageHarness<T extends { id: string }>(fetchPage: Parameters<typeof useInvitationPage<T>>[0]) {
  const values: unknown[] = [];
  let index = 0;
  let effect: (() => void) | undefined;
  let cleanup: (() => void) | void;
  const hooks = {
    ApiError,
    useState(initial: unknown) {
      const slot = index++;
      if (!(slot in values)) values[slot] = initial;
      return [values[slot], (next: unknown) => { values[slot] = typeof next === "function" ? next(values[slot]) : next; }];
    },
    useRef(initial: unknown) {
      const slot = index++;
      if (!(slot in values)) values[slot] = { current: initial };
      return values[slot];
    },
    useCallback(callback: unknown) { return callback; },
    useEffect(callback: () => (() => void)) { effect = callback; },
  };
  const hook = runInNewContext(`${functionSource("src/components/invitation-page.tsx", "useInvitationPage")}\nuseInvitationPage`, hooks) as typeof useInvitationPage<T>;
  function render() { index = 0; return hook(fetchPage); }
  return { render, mount() { cleanup = effect?.(); }, unmount() { cleanup?.(); } };
}
export function handler(file: string, parent: string, name: string, scope: object) {
  return runInNewContext(`${functionSource(file, parent, name)}\n${name}`, scope);
}
export function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (error: unknown) => void;
  const promise = new Promise<T>((yes, no) => { resolve = yes; reject = no; });
  return { promise, resolve, reject };
}
export async function settle() { await new Promise<void>((resolve) => setImmediate(resolve)); }
