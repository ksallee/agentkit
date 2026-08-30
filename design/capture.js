// The capture contract. Both drivers evaluate this file in the page and call
// the four functions it defines, so a python project and a typescript project
// write byte-identical artboards from the same screen.
//
// One page load per screen produces two files:
//
//   <Name>.dc.html       curated computed styles, tokens written back as
//                        var(), one inline style per node. What the canvas
//                        opens, because a properties panel reads and writes
//                        the element's own style attribute and has nothing to
//                        read when the padding lives in a stylesheet.
//   <Name>.classes.html  the markup with the app's stylesheet carried whole.
//                        Several times smaller and pixel exact, so a pull
//                        request diffs this one and reads the design change.
//
// Call order per load, and it matters: boxes() and classes() only read, and
// curated() rewrites every style attribute in the document. A classes form
// taken after a curated one carries the curated one's inline styles.
//
//   boxes()      the live geometry, kept as the truth every check compares to
//   classes()    the read-only form
//   curated()    the rewriting form
//   assemble()   one artboard file, from a form and a stamp
//   plain()      the same artboard as a bare document, which is what a driver
//                reloads to measure the capture against boxes()
//
// The provenance stamp is the driver's to build and this file's to write. Its
// digest field is the sha256 of the classes form's `body`, first 16 hex
// characters, computed by the driver in its own language. Two artboards with
// one digest came off one screen state; a designer working on a duplicate
// compares that field and learns whether the reference moved, which a commit
// alone cannot answer over a dirty tree.

globalThis.agentkitCapture = (() => {
	// The properties a designer edits. The whole computed set runs to about 340
	// per node, which is what makes a naive dump 75 times larger than it needs
	// to be.
	const EDITED = [
		'display', 'position', 'top', 'right', 'bottom', 'left', 'z-index',
		'flex-direction', 'flex-wrap', 'flex', 'align-items', 'align-content',
		'justify-content', 'justify-items', 'justify-self', 'gap',
		'grid-template-columns', 'grid-template-rows', 'grid-auto-flow',
		'grid-auto-columns', 'grid-auto-rows', 'grid-column', 'grid-row',
		'width', 'height', 'min-width', 'max-width', 'min-height', 'max-height',
		'margin-top', 'margin-right', 'margin-bottom', 'margin-left',
		'padding-top', 'padding-right', 'padding-bottom', 'padding-left',
		'border-top', 'border-right', 'border-bottom', 'border-left',
		'border-radius', 'background-color', 'color', 'opacity', 'box-shadow',
		'overflow', 'overflow-x', 'overflow-y', 'font-family', 'font-size',
		'font-weight', 'font-style', 'line-height', 'letter-spacing',
		'text-align', 'text-transform', 'white-space', 'font-variant-numeric',
		'transform', 'cursor', 'box-sizing', 'vertical-align', 'align-self',
		'order', 'visibility',
		// The independent transform properties, which never appear in the
		// `transform` matrix. A tick centred on its hour with `translate: -50%`
		// lands half its own width to the right without them.
		'translate', 'rotate', 'scale',
		'border-collapse', 'border-spacing', 'table-layout',
		// A hatched or gradient fill is a background-image, and a capture that
		// keeps only background-color drops it.
		'background-image', 'background-size', 'background-position',
		'background-repeat',
		// Antialiasing changes glyph advances by hundredths of a pixel, so a
		// capture that drops it lays every line of text out slightly narrow.
		'-webkit-font-smoothing',
		// The shorthand `text-decoration` reads as `none solid rgb(...)` and
		// re-declaring it repaints the colour. The line is the part that moves.
		'text-decoration-line'
	];

	// Reading an inherited property back onto every child triples the file and
	// says nothing: the value is already true by inheritance.
	const INHERITED = [
		'color', 'font-family', 'font-size', 'font-weight', 'line-height',
		'letter-spacing', 'text-align', 'white-space', 'font-variant-numeric',
		'cursor', '-webkit-font-smoothing'
	];

	// Inheritance carries a value only where the user agent has no opinion of
	// its own. A bare <a> is blue and underlined however its parent is painted,
	// and a <button> takes the platform font, so an inherited property has to
	// be stated on those. Listing the tags where skipping is safe fails towards
	// a larger file rather than towards a wrong one.
	const PLAIN = new Set([
		'DIV', 'SPAN', 'P', 'SECTION', 'MAIN', 'NAV', 'HEADER', 'FOOTER',
		'ARTICLE', 'ASIDE', 'UL', 'OL', 'LI', 'FIGURE', 'FIGCAPTION', 'DL',
		'DD', 'DT', 'TR', 'TBODY', 'THEAD', 'TFOOT', 'PICTURE', 'TIME', 'HR',
		'BR', 'IMG', 'SVG', 'PATH', 'G', 'CIRCLE', 'RECT', 'LINE', 'POLYGON',
		'POLYLINE', 'DEFS', 'CLIPPATH', 'USE'
	]);

	// A cross-origin sheet throws on .cssRules and cannot be inlined. Dropping
	// its <link> renders the capture in a fallback face at other metrics and
	// nothing in the markup says so, so the link is carried instead and a sheet
	// that can be neither read nor linked is counted in `lost` for the driver
	// to stop on.
	const sheets = () => {
		const links = [];
		const rules = [];
		let lost = 0;
		for (const sheet of document.styleSheets) {
			try {
				rules.push([...sheet.cssRules]);
			} catch {
				if (sheet.href) links.push(sheet.href);
				else lost++;
			}
		}
		return { links, rules, lost };
	};

	const classes = () => {
		const { links, rules, lost } = sheets();
		return {
			links,
			css: rules.map((set) => set.map((r) => r.cssText).join('\n')).join('\n'),
			body: document.body.innerHTML,
			lost,
			root: ''
		};
	};

	const curated = () => {
		const rootCS = getComputedStyle(document.documentElement);
		const { links, rules, lost } = sheets();
		const tokenBlocks = [];
		const names = new Set();
		for (const set of rules) {
			for (const rule of set) {
				if (rule.selectorText && /^:root|\[data-theme/.test(rule.selectorText)) tokenBlocks.push(rule.cssText);
				if (rule.style) for (const property of rule.style) if (property.startsWith('--')) names.add(property);
			}
		}

		// A token's declared text and the same value read off a computed
		// property are two spellings of one value: `--bg: #121117` against
		// `background-color: rgb(18, 17, 23)`. Matching on the declared text
		// alone leaves every colour token unmatched, so each one is normalised
		// through the browser's own parser. A value that will not parse as the
		// property leaves the sentinel behind and is not that kind of token.
		const probe = document.createElement('span');
		document.body.append(probe);
		const SENTINEL = { color: 'rgb(1, 2, 3)', fontFamily: 'x-sentinel' };
		const parses = (property, value) => {
			probe.style[property] = SENTINEL[property];
			probe.style[property] = value;
			const out = getComputedStyle(probe)[property];
			return out === SENTINEL[property] ? null : out;
		};

		// One map per kind, and a token is only ever written back into a
		// property of its own kind. A single value-keyed map turns every `none`
		// in the document into whichever token happens to be `none`, which is
		// how a link picks up an underline from a shadow token.
		const colours = new Map();
		const fonts = new Map();
		const lengths = new Map();
		const index = (map, value, name) => {
			if (value && !map.has(value)) map.set(value, name);
		};
		for (const name of names) {
			const raw = rootCS.getPropertyValue(name).trim();
			if (!raw) continue;
			const colour = parses('color', raw);
			if (colour) index(colours, colour, name);
			else if (/,|['"]/.test(raw) && parses('fontFamily', raw)) index(fonts, parses('fontFamily', raw), name);
			else if (/^-?[\d.]+(px|em|rem|%)$/.test(raw)) index(lengths, raw, name);
		}
		probe.remove();

		const ref = (map, value) => (map.has(value) ? `var(${map.get(value)})` : null);

		// Chrome lays out on a 1/64 px grid and prints a length truncated to six
		// significant digits, so a used width of 24.90625px reads back as
		// `24.9062px` and re-parses one grid unit lower. Every text run in an
		// unsnapped capture comes out 1/64 px narrow. Six digits is the
		// signature of a value that came out of layout: a shorter one, an
		// 18.2px line height among them, is exact as printed and snapping it
		// would move it.
		const snap = (value) =>
			value.replace(/-?\d*\.?\d+px/g, (found) => {
				const digits = found.slice(0, -2).replace(/[-.]/g, '').replace(/^0+/, '').length;
				return digits < 6 ? found : `${Math.round(parseFloat(found) * 64) / 64}px`;
			});

		const tok = (property, value) => {
			const v = snap(value.trim());
			if (property === 'background-color' || property === 'color') return ref(colours, v) ?? v;
			if (property === 'font-family') return ref(fonts, v) ?? v;
			if (property === 'border-radius') return ref(lengths, v) ?? v;
			// A border or a shadow is a compound value whose colour is always
			// serialised as rgb() or rgba(), so the colour alone is replaceable.
			if (property.startsWith('border-') || property === 'box-shadow')
				return v.replace(/rgba?\([^)]*\)/g, (found) => ref(colours, found) ?? found);
			return v;
		};

		// Two passes, and this is the whole correctness of the form. Writing a
		// style while iterating changes the layout and the inherited values
		// getComputedStyle reports for every element after it, so the tail of
		// the document would be measured against a page already half rewritten.
		const els = [document.body, ...document.querySelectorAll('body *')];
		const styles = els.map((el) => {
			const cs = getComputedStyle(el);
			const plain = PLAIN.has(el.tagName.toUpperCase());
			const parent = el.parentElement ? getComputedStyle(el.parentElement) : null;
			// Most nodes have no background image, and their size, position and
			// repeat say nothing while costing four declarations each.
			const flat = cs.getPropertyValue('background-image') === 'none';
			const declarations = [];
			for (const property of EDITED) {
				if (flat && /^background-(image|size|position|repeat)$/.test(property)) continue;
				const value = cs.getPropertyValue(property);
				if (!value) continue;
				if (plain && parent && INHERITED.includes(property) && parent.getPropertyValue(property) === value) continue;
				declarations.push(`${property}: ${tok(property, value)}`);
			}
			return declarations.join('; ');
		});
		els.forEach((el, i) => {
			if (styles[i]) el.setAttribute('style', styles[i]);
		});

		// body's own declarations move to the artboard root, the element that
		// stands in for body once the screen is one board among fifty.
		return { links, css: tokenBlocks.join('\n'), body: document.body.innerHTML, lost, root: styles[0] };
	};

	const boxes = () =>
		[...document.querySelectorAll('body *')].map((el) => {
			const r = el.getBoundingClientRect();
			return { tag: el.tagName, box: [r.x, r.y, r.width, r.height] };
		});

	const attr = (value) => String(value).replaceAll('"', '&quot;');

	const links = (form) => form.links.map((href) => `<link rel="stylesheet" href="${attr(href)}">`).join('\n  ');

	/** The artboard: the provenance comment, then one root sized to the frame. */
	const artboard = (form, stamp) => {
		const [width, height] = stamp.viewport.split('x');
		const root =
			(form.root || 'background-color: #ffffff; color: #111111') +
			`; width: ${width}px; height: ${height}px; box-sizing: border-box; overflow: hidden`;
		const marks = ['route', 'commit', 'at', 'viewport', 'digest']
			.map((key) => `data-captured-${key}="${attr(stamp[key])}"`)
			.join(' ');
		const comment = ['route', 'commit', 'at', 'viewport', 'digest']
			.map((key) => `${key}=${stamp[key]}`)
			.join(' ');
		return `<!-- captured ${comment} -->\n<div ${marks} style="${attr(root)}">\n${form.body}\n</div>\n`;
	};

	/** One artboard file, which is what the canvas opens. */
	const assemble = (form, stamp, title) => `<!doctype html>
<html>
<head>
  <meta charset="utf-8">
</head>
<body>
<x-dc>
<helmet>
  <title>${attr(title)}</title>
  ${links(form)}
  <style>${form.css}</style>
</helmet>
${artboard(form, stamp)}</x-dc>
</body>
</html>
`;

	/** The same artboard as a bare document, which is what a driver measures.
	 *  `<x-dc>` and `<helmet>` are unknown inline elements outside the canvas,
	 *  so a browser gives them a line box and pushes the artboard down. The
	 *  canvas strips them; this page never has them. */
	const plain = (form, stamp) => `<!doctype html><html lang="en"><head><meta charset="utf-8">${links(form)}<style>${form.css}</style>
<style>body { margin: 0; }</style></head><body>${artboard(form, stamp)}</body></html>`;

	return { boxes, classes, curated, assemble, plain };
})();
