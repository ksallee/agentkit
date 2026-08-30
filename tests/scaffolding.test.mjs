/**
 * The scaffolding a project adopted holds together, checked from inside it.
 *
 *     pnpm test
 *
 * agentkit seeds this file, so a project's `test` gate collects something on
 * its first run and the green says the scaffolding is sound instead of saying
 * the directory was empty. It is also where a project's own tests go: write
 * them beside it, and this file stays as the one agentkit replaces on a rerun.
 *
 * It is the `check` gate's subject too. `tsconfig.json` sets `checkJs`, and its
 * `include` reaches `tests/`, so `pnpm check` type-checks this file on a
 * project that has written no TypeScript yet. Widen that `include` as the
 * project grows.
 *
 * `node --test` is built into Node and needs nothing installed. Everything
 * below reads `package.json`, `tsconfig.json` and `.agentkit/gates.toml`,
 * which every adopted project has. Nothing here runs a gate. `bin/verify` runs
 * the gates, and one of them runs this file.
 *
 * The `typescript` pack seeds these three files at the repository root and the
 * `python+typescript` pack seeds them in `web/`, so the package directory is
 * walked to from this file rather than named.
 */

import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { dirname, join, parse, resolve } from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";

/** The directory holding the `package.json` whose `test` script ran this file. */
const PACKAGE_DIR = resolve(dirname(fileURLToPath(import.meta.url)), "..");

/**
 * Whatever a JSON file holds, parsed.
 *
 * @param {string} path
 * @returns {any}
 */
function json(path) {
  return JSON.parse(readFileSync(path, "utf8"));
}

/** The manifest the two pnpm gates run against. */
function packageJson() {
  return json(join(PACKAGE_DIR, "package.json"));
}

/**
 * The nearest ancestor holding `.agentkit/gates.toml`, or an empty string.
 *
 * The `typescript` pack puts that directory beside `package.json` and the
 * `python+typescript` pack puts it one level up, so neither depth is assumed.
 *
 * @returns {string}
 */
function repositoryRoot() {
  let here = PACKAGE_DIR;
  for (;;) {
    if (existsSync(join(here, ".agentkit", "gates.toml"))) {
      return here;
    }
    const up = dirname(here);
    if (up === here || up === parse(here).root) {
      return "";
    }
    here = up;
  }
}

/**
 * Every script name a declared gate invokes through pnpm, in declaration order.
 *
 * `.agentkit/gates.toml` is read with a regular expression rather than a TOML
 * parser, because Node ships none and a gate command is one quoted string on
 * one line. A command this misses is a command shaped in a way the runner does
 * not accept either.
 *
 * @param {string} declaration
 * @returns {string[]}
 */
function pnpmScripts(declaration) {
  const found = declaration.matchAll(/^\s*command\s*=\s*"pnpm\s+([^"]+)"/gm);
  return [...found].map((hit) => hit[1].trim());
}

test("package.json parses and is private", () => {
  const manifest = packageJson();
  assert.equal(manifest.private, true, "a scaffolding package is never published");
});

test("the test script is the one that collected this file", () => {
  assert.equal(packageJson().scripts.test, "node --test");
});

test("the check script type-checks and emits nothing", () => {
  assert.equal(packageJson().scripts.check, "tsc --noEmit");
});

test("typescript is a devDependency, so the check gate resolves tsc", () => {
  const manifest = packageJson();
  assert.ok(
    manifest.devDependencies?.typescript,
    "pnpm check runs tsc, which resolves from node_modules/.bin after an install",
  );
});

test("tsconfig.json reaches this file, so the check gate has something to check", () => {
  const config = json(join(PACKAGE_DIR, "tsconfig.json"));
  assert.equal(config.compilerOptions.checkJs, true);
  assert.ok(
    config.include.some((/** @type {string} */ pattern) => pattern.startsWith("tests/")),
    `tsconfig.json includes ${JSON.stringify(config.include)} and none of it is tests/`,
  );
});

test("the gate declaration is somewhere above this package", () => {
  assert.notEqual(repositoryRoot(), "", ".agentkit/gates.toml is above no directory here");
});

test("every pnpm script a gate names is declared here", () => {
  const declaration = readFileSync(join(repositoryRoot(), ".agentkit", "gates.toml"), "utf8");
  const named = pnpmScripts(declaration);
  assert.ok(named.length > 0, "no gate runs pnpm, so this package answers to nothing");
  const scripts = packageJson().scripts;
  for (const script of named) {
    assert.ok(scripts[script], `a gate runs \`pnpm ${script}\` and package.json declares no such script`);
  }
});
