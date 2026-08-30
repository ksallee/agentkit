// Capture every screen `design/screens.json` names, as two artboard files each.
//
//   node design/capture.mjs
//   node design/capture.mjs --only Inbox
//   node design/capture.mjs --base http://localhost:4173
//
// The typescript pack's driver, and one of the two the `none` pack receives.
// `design/capture.py` is the python pack's, and `design/capture.js` is the
// contract they share, so both write the same bytes from the same screen. The
// stamp names which one ran. `design-process` step 6 is the method this runs
// and says how it picks a driver on a project holding both.
//
// This points at a URL and never starts the app. Building a fixture and
// starting a dev server is the most project-specific thing a capture does, and
// a template that guessed at it would guess wrong: `screens.json` names where
// the app answers, and the project owns whatever runs there.
//
// Two files per screen, from one page load:
//
//   <Name>.dc.html       curated computed styles, tokens written back as
//                        var(), one inline style per node. What the canvas
//                        opens.
//   <Name>.classes.html  the markup with the app's stylesheet carried whole.
//                        Smaller and pixel exact, so a pull request diffs this
//                        one and reads the design change.
//
// Neither is hand-edited. Both carry a provenance stamp on the root, so a
// designer who duplicates an artboard in the canvas and works on the copy can
// tell when its reference has moved.
//
// Every artboard is measured against the live page before it is written, and a
// box further than one grid unit from the app fails the run. An eye passes a
// capture that is two pixels out, and two pixels out is what somebody sees
// without knowing why.
//
// Puppeteer resolves from the project's own node_modules, which is the one
// third-party dependency a project that captures takes on.
import puppeteer from 'puppeteer';
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { readFileSync, writeFileSync } from 'node:fs';
import { dirname, relative, resolve } from 'node:path';

const HERE = import.meta.dirname;
const CONTRACT = resolve(HERE, 'capture.js');

// Chrome lays out on a 1/64 px grid, so one grid unit is the smallest
// difference a box can have and the tightest tolerance worth asserting.
const GRID = 1 / 64;

// The stamp's digest is the sha256 of the classes form's markup, first 16 hex
// characters. `design/capture.py` computes the same field the same way, and
// `design/capture.js` carries the definition.
const DIGEST_CHARS = 16;

// The stamp's driver field. A project on the `none` pack holds both drivers,
// so an artboard says which runtime wrote it and a box that moved between two
// artboards can be read as a browser difference rather than a screen change.
const DRIVER_NAME = 'capture.mjs';

// A screen that has not painted in this long is a screen that never will, and a
// run that hangs on it reports nothing at all.
const LOAD_TIMEOUT_MS = 30_000;

const args = process.argv.slice(2);
if (args.includes('--help') || args.includes('-h')) {
	console.log('Usage: node design/capture.mjs [--screens design/screens.json] [--only <Name>] [--base <url>] [--out <dir>]');
	process.exit(0);
}
const opt = (name, fallback) => {
	const i = args.indexOf(name);
	return i === -1 ? fallback : args[i + 1];
};

function fail(message) {
	console.error(message);
	process.exit(1);
}

const screensPath = resolve(opt('--screens', resolve(HERE, 'screens.json')));
let declared;
try {
	declared = JSON.parse(readFileSync(screensPath, 'utf8'));
} catch (exc) {
	fail(`${screensPath} could not be read as JSON: ${exc.message}`);
}
if (!declared.screens?.length) fail(`${screensPath} names no screens. Add one, with a name and a route.`);

const base = (opt('--base', declared.base) ?? '').replace(/\/$/, '');
if (!base) fail(`${screensPath} names no base URL, and --base was not given.`);
const out = resolve(opt('--out', dirname(screensPath)));
const only = opt('--only', null);
const wanted = only ? declared.screens.filter((s) => s.name === only) : declared.screens;
if (!wanted.length) fail(`no screen named ${only}. Known: ${declared.screens.map((s) => s.name).join(', ')}`);

const frame = (screen) => [
	Number(screen.width ?? declared.viewport?.width ?? 1440),
	Number(screen.height ?? declared.viewport?.height ?? 1000)
];

// The stamp names the commit the screen came from, marked `-dirty` when the
// tree has moved. A stamp naming a commit the screen was never at is worse than
// one saying the tree was dirty, because the whole drift story rests on it.
// Changes under the output directory are excluded: a capture writes there, so a
// second run in one session would otherwise report every screen dirty.
function stampCommit() {
	// `stderr: 'pipe'` because the catch below already treats a failure as "no
	// commit", and the default inherits: a capture run outside a checkout wrote
	// `fatal: not a git repository` to the terminal and then carried on. The
	// python driver passes `capture_output=True` for the same reason, and the
	// two drivers agreeing on what they print is as much the contract as the
	// bytes they write.
	const git = (...a) =>
		execFileSync('git', a, { cwd: process.cwd(), encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] }).trim();
	try {
		const head = git('rev-parse', '--short', 'HEAD');
		const rel = relative(process.cwd(), out).split('\\').join('/');
		const moved = git('status', '--porcelain')
			.split('\n')
			.filter((line) => line.trim() && !(rel && line.slice(3).startsWith(rel)));
		return head + (moved.length ? '-dirty' : '');
	} catch {
		return '';
	}
}

// The base URL has to answer before a browser is launched, so the failure is
// one readable line rather than a navigation timeout.
try {
	await fetch(base);
} catch {
	fail(
		`nothing answered at ${base}. This capture points at a running app and never starts one.\n` +
			`Start the app, then rerun. ${screensPath} names what it expects.`
	);
}

const contract = readFileSync(CONTRACT, 'utf8');
const commit = stampCommit();
const at = new Date().toISOString().replace(/\.\d+Z$/, 'Z');
const deviation = (a, b) => Math.max(...a.box.map((v, i) => Math.abs(v - b.box[i])));
const show = (e) => `${e.tag} ${e.box.map((v) => v.toFixed(4)).join(' ')}`;

const browser = await puppeteer.launch();
const rows = [];
let bad = 0;

for (const screen of wanted) {
	const [width, height] = frame(screen);
	const page = await browser.newPage();
	await page.setViewport({ width, height });
	const errors = [];
	page.on('pageerror', (e) => errors.push(String(e)));
	const response = await page.goto(base + screen.route, { waitUntil: 'networkidle0', timeout: LOAD_TIMEOUT_MS });
	if (!response?.ok()) fail(`${screen.route} answered ${response ? response.status() : 'nothing'}`);
	await page.evaluate(() => document.fonts.ready);
	// A screen that threw while mounting still renders its server markup, so
	// the capture would look right and carry a half-mounted component.
	if (errors.length) fail(`${screen.route} threw: ${errors[0]}`);

	// Order is the correctness of this block. `boxes` and `classes` only read.
	// `curated` rewrites every style attribute in the document, so a classes
	// form taken after it would carry the curated one's inline styles.
	await page.addScriptTag({ content: contract });
	const truth = await page.evaluate(() => agentkitCapture.boxes());
	const forms = {
		classes: await page.evaluate(() => agentkitCapture.classes()),
		curated: await page.evaluate(() => agentkitCapture.curated())
	};
	const stamp = {
		route: screen.route,
		commit,
		at,
		viewport: `${width}x${height}`,
		digest: createHash('sha256').update(forms.classes.body).digest('hex').slice(0, DIGEST_CHARS),
		driver: DRIVER_NAME
	};
	const written = {};
	for (const [form, data] of Object.entries(forms)) {
		if (data.lost) fail(`${screen.name}: ${data.lost} stylesheet(s) could be neither read nor linked`);
		written[form] = {
			canvas: await page.evaluate(
				([f, s, t]) => agentkitCapture.assemble(f, s, t),
				[data, stamp, screen.title ?? screen.name]
			),
			plain: await page.evaluate(([f, s]) => agentkitCapture.plain(f, s), [data, stamp])
		};
	}
	await page.close();

	for (const [form, docs] of Object.entries(written)) {
		const file = `${screen.name}.${form === 'classes' ? 'classes' : 'dc'}.html`;

		const check = await browser.newPage();
		await check.setViewport({ width, height });
		await check.setContent(docs.plain, { waitUntil: 'networkidle0' });
		await check.evaluate(() => document.fonts.ready);
		await check.addScriptTag({ content: contract });
		// The artboard root is one element the live page does not have.
		const got = (await check.evaluate(() => agentkitCapture.boxes())).slice(1);
		await check.close();

		if (got.length !== truth.length) fail(`${screen.name} ${form}: ${got.length} elements against ${truth.length} live`);
		const off = truth
			.map((v, i) => ({ live: v, here: got[i], by: deviation(v, got[i]) }))
			.filter((d) => d.by > 0)
			.sort((a, b) => b.by - a.by);
		const over = off.filter((d) => d.by > GRID + 1e-9);
		if (over.length) {
			bad++;
			console.error(`${screen.name} ${form}: ${over.length} box(es) further than one grid unit from the app`);
			for (const d of over.slice(0, 5)) console.error(`    off ${d.by.toFixed(4)}\n    live ${show(d.live)}\n    here ${show(d.here)}`);
		}

		writeFileSync(resolve(out, file), docs.canvas, 'utf8');
		rows.push({
			screen: screen.name,
			form,
			file,
			bytes: docs.canvas.length,
			elements: truth.length,
			moved: `${off.length}/${truth.length}`,
			'worst px': (off.length ? off[0].by : 0).toFixed(4),
			'var()': (docs.canvas.match(/var\(--/g) || []).length
		});
	}
}

await browser.close();
console.log(`\n${commit || 'no commit'}  ${wanted.length} screen(s) -> ${out}\n`);
console.table(rows);
if (bad) fail(`\n${bad} artboard(s) do not match the app.`);
process.exit(0);
