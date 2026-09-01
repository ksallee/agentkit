// Write every wireframe artboard, and the canvas layout that holds them.
//
//   node design/build.mjs
//
// `design-process` step 3: one generator writes every frame, so a number or a
// label changes in one place and the frames stay consistent. Greyscale on
// purpose, because structure and behaviour come first and colour and the type
// pair stay the designer's call. Real numbers, scaled from a measurement,
// never lorem ipsum.
//
// What ships here is the method's half. The constants below are defaults a
// project edits in place, `Palette.dc.html` renders whatever they say, and
// `canvas.json` lays out every artboard beside the screens
// `design/capture.mjs` writes. The components a project draws with are the
// project's, and they are found while drawing rather than guessed at here: a
// shipped table, chart or row would be one project's shape imposed on every
// other.
//
// A number appears once. Every grey is read out of `GREYS`, every type size
// out of `TYPE`, every step out of `SPACE`, and the sheet renders what it
// finds, so changing a value changes the artboard and the documentation of
// that value together.
//
// A rerun is byte identical. Nothing here reads a clock or a commit, so a
// generated artboard changes only when the generator does, and a diff on this
// directory is a design change every time.
//
// `design/build.py` is the same generator for a project whose pack is python,
// and `tests/test_design.py` holds them to the same bytes.
//
// Node's standard library only, so this runs before the project installs.
import { createHash } from 'node:crypto';
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';

const HERE = import.meta.dirname;

// The frame every screen artboard opens at, and the space between two of them
// on the canvas. A project working at another size changes these two numbers.
const FRAME_W = 1440;
const FRAME_H = 1000;
const GUTTER = 120;

// A sheet is wider than a screen, because it draws several things side by side.
const SHEET_W = 1440;
const SHEET_H = 1000;

// The greys, each with the one meaning it carries. `DESIGNER.md` says one
// meaning per colour, and a grey is a colour. A project that needs a seventh
// adds it here with what it means, and the palette sheet grows a row.
const GREYS = [
	['ink', '#111111', 'text, and the answer a screen leads with'],
	['ink2', '#555555', 'secondary text'],
	['ink3', '#8a8a8a', 'a label read once'],
	['line', '#d9d9d9', 'a border'],
	['panel', '#f3f3f3', 'a surface above the page'],
	['bg', '#ffffff', 'the page']
];
const GREY = Object.fromEntries(GREYS.map(([name, value]) => [name, value]));

// The type scale, as (name, px, weight). Sizes are a scale rather than a list
// of one-off values, so a screen at a size nobody named is a screen to look at.
const TYPE = [
	['answer', 40, 600],
	['heading', 20, 600],
	['body', 15, 400],
	['label', 13, 400],
	['note', 11, 400]
];
const SIZE = Object.fromEntries(TYPE.map(([name, px]) => [name, px]));

// The spacing scale. Every gap, pad and margin on an artboard is one of these.
const SPACE = [4, 8, 12, 16, 24, 40];

const RADIUS = 3;

// A system stack on purpose. The type pair is the designer's call, and a
// generator that picked one would be making it.
const SANS = "-apple-system, 'Helvetica Neue', Helvetica, Arial, sans-serif";
const MONO = 'ui-monospace, Menlo, Consolas, monospace';

// The stamp on a generated artboard's root. A capture stamps a route, a commit
// and a time because its reference is a screen that moves on its own. A
// generated artboard has no such reference: this file is the reference. So the
// stamp names the function that drew it, the frame it was drawn at, and a
// digest of its own markup. A designer who duplicates an artboard in the canvas
// regenerates, compares digests, and learns whether the original moved. Neither
// a commit nor a timestamp would add anything the digest lacks, and both would
// churn every file on every run.
const DIGEST_CHARS = 16;

/** HTML-escape, for anything that reaches an attribute or a text node. */
const esc = (text) =>
	String(text).replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('"', '&quot;');

const box = (style, inner) => `<div style="${style}">${inner}</div>`;

/** One line at a named step of the type scale. */
function text(name, body, colour = '', extra = '') {
	const px = SIZE[name];
	const weight = TYPE.find(([n]) => n === name)[2];
	const style = `font-size: ${px}px; font-weight: ${weight}; line-height: 1.3; color: ${colour || GREY.ink}`;
	return box(style + (extra ? `; ${extra}` : ''), body);
}

function stack(gap, inner, extra = '') {
	const style = `display: flex; flex-direction: column; gap: ${gap}px`;
	return box(style + (extra ? `; ${extra}` : ''), inner);
}

const row = (gap, inner, align = 'center') => box(`display: flex; align-items: ${align}; gap: ${gap}px`, inner);

const swatch = (value, size) =>
	box(
		`width: ${size}px; height: ${size}px; flex: none; background: ${value}; ` +
			`border: 1px solid ${GREY.line}; border-radius: ${RADIUS}px`,
		''
	);

const mono = (body, colour = '') =>
	box(`font-family: ${MONO}; font-size: ${SIZE.label}px; color: ${colour || GREY.ink2}`, body);

function section(title, note, inner) {
	const head = stack(SPACE[0], text('heading', esc(title)) + text('note', esc(note), GREY.ink3));
	return stack(SPACE[3], head + inner);
}

/** One `.dc.html` file: the stamp, then one root sized to its canvas slot.
 *
 *  The same extension and the same root shape as a captured artboard, so the
 *  canvas and a pull request read one set of files. The prefix differs because
 *  the provenance differs: `data-captured-*` names a screen that ran,
 *  `data-generated-*` names the function that drew one that has not.
 *
 *  The head loads `./support.js`, which the canvas editor serves beside the
 *  artboards. Without that line an artboard opens in the canvas as flat markup
 *  and nothing on it can be selected or edited. */
function artboard(name, title, body, width, height) {
	const digest = createHash('sha256').update(body, 'utf8').digest('hex').slice(0, DIGEST_CHARS);
	const root =
		`width: ${width}px; height: ${height}px; box-sizing: border-box; overflow: hidden; ` +
		`padding: ${SPACE[5]}px; display: flex; flex-direction: column; gap: ${SPACE[4]}px; ` +
		`background: ${GREY.bg}; color: ${GREY.ink}; font-family: ${SANS}`;
	const marks =
		`data-generated-by="${esc(name)}" ` +
		`data-generated-viewport="${width}x${height}" ` +
		`data-generated-digest="${digest}"`;
	return `<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <script src="./support.js"></script>
</head>
<body>
<x-dc>
<helmet>
  <title>${esc(title)}</title>
  <style>body { margin: 0; }</style>
</helmet>
<!-- generated by=${name} viewport=${width}x${height} digest=${digest} -->
<div ${marks} style="${root}">
${body}
</div>
</x-dc>
</body>
</html>
`;
}

/** The defaults this generator ships, rendered from the constants that hold them.
 *
 *  The one artboard agentkit draws for a project, and the only one it can:
 *  every other frame needs components only the project has. This one documents
 *  the palette and the two scales by rendering them, so a project that edits a
 *  grey sees the edit on the artboard and in the legend at once. */
function palette_sheet() {
	const greys = GREYS.map(([name, value, meaning]) =>
		row(
			SPACE[2],
			swatch(value, SIZE.answer) +
				stack(SPACE[0], text('label', esc(name)) + mono(esc(value)) + text('note', esc(meaning), GREY.ink3))
		)
	).join('');
	const sizes = TYPE.map(([name, px]) =>
		row(SPACE[3], box('width: 96px; flex: none', mono(`${name} ${px}`)) + text(name, 'Four hours on one project'))
	).join('');
	const steps = SPACE.map((step) =>
		row(
			SPACE[2],
			box('width: 40px; flex: none', mono(String(step))) +
				box(`width: ${step}px; height: ${SPACE[2]}px; background: ${GREY.ink3}; border-radius: ${RADIUS}px`, '')
		)
	).join('');
	const frame = mono(`frame ${FRAME_W}x${FRAME_H}, gutter ${GUTTER}, radius ${RADIUS}`);

	return stack(
		SPACE[5],
		stack(
			SPACE[1],
			text('answer', 'Greyscale, and the two scales under it') +
				text(
					'body',
					'Every number on this sheet is read out of design/build.py. Edit a value there and ' +
						'this artboard says so on the next run. Colour and the type pair stay the ' +
						"designer's call, which is what step 3 means by greyscale on purpose.",
					GREY.ink2,
					'max-width: 760px'
				)
		) +
			row(
				SPACE[5],
				section('Greys', 'one meaning each, and used nowhere else', stack(SPACE[2], greys)) +
					stack(
						SPACE[5],
						section('Type', 'a scale, so a one-off size is a thing to look at', stack(SPACE[2], sizes)) +
							section('Space', 'every gap, pad and margin is one of these', stack(SPACE[1], steps)) +
							section('Frame', 'what an artboard opens at', frame)
					),
				'flex-start'
			)
	);
}

// Every artboard this generator writes, as file name to the title, the frame
// and the function that draws it. A project adds a row and a function, and both
// the file and its slot in `canvas.json` follow. One entry point is the whole
// point of step 3.
const ARTBOARDS = {
	'Palette.dc.html': ['Greyscale, and the two scales under it', SHEET_W, SHEET_H, palette_sheet]
};

/** The names `design/capture.mjs` owns, as slots to reserve rather than draw.
 *
 *  A capture that has failed, or that has never run, must not be able to move
 *  an artboard this file wrote, and two writers on one file is the thing to
 *  avoid. The slot's size is the viewport the capture opens the screen at, so a
 *  frame changed in `screens.json` takes effect on the next capture. */
function captured(screens) {
	let declared;
	try {
		declared = JSON.parse(readFileSync(screens, 'utf8'));
	} catch {
		return [];
	}
	const viewport = declared.viewport ?? {};
	return (declared.screens ?? []).map((screen) => [
		`${screen.name}.dc.html`,
		screen.title ?? screen.name,
		Number(screen.width ?? viewport.width ?? FRAME_W),
		Number(screen.height ?? viewport.height ?? FRAME_H)
	]);
}

/** The layout: one row of drawn artboards, one row of captured screens. */
function canvas(drawn, reserved) {
	const artboards = [];
	let x = 0;
	for (const [file, title, w, h] of drawn) {
		artboards.push({ file, x, y: 0, w, h, title });
		x += w + GUTTER;
	}
	const tall = drawn.length ? Math.max(...drawn.map(([, , , h]) => h)) : 0;
	x = 0;
	for (const [file, title, w, h] of reserved) {
		artboards.push({ file, x, y: tall + GUTTER, w, h, title });
		x += w + GUTTER;
	}
	return { artboards };
}

const args = process.argv.slice(2);
if (args.includes('--help') || args.includes('-h')) {
	console.log('Usage: node design/build.mjs [--out <dir>] [--screens design/screens.json]');
	process.exit(0);
}
const opt = (name, fallback) => {
	const i = args.indexOf(name);
	return i === -1 ? fallback : args[i + 1];
};

const out = resolve(opt('--out', HERE));
const screens = resolve(opt('--screens', resolve(HERE, 'screens.json')));

const reserved = captured(screens);
const clash = reserved.map(([file]) => file).filter((file) => file in ARTBOARDS);
if (clash.length) {
	console.error(`the capture owns ${clash.sort().join(', ')}. Remove them from ARTBOARDS.`);
	process.exit(1);
}

mkdirSync(out, { recursive: true });
const drawn = [];
for (const [file, [title, width, height, draw]] of Object.entries(ARTBOARDS)) {
	writeFileSync(resolve(out, file), artboard(draw.name, title, draw(), width, height), 'utf8');
	drawn.push([file, title, width, height]);
}
writeFileSync(resolve(out, 'canvas.json'), `${JSON.stringify(canvas(drawn, reserved), null, 2)}\n`, 'utf8');

console.log(`wrote ${Object.keys(ARTBOARDS).length} artboard(s) and canvas.json to ${out}`);
if (reserved.length) {
	console.log(`reserved ${reserved.length} slot(s) for the capture: ${reserved.map(([file]) => file).join(', ')}`);
}
