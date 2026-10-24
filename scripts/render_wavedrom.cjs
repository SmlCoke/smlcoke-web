/** Render one WaveJSON timing diagram from stdin; stdout contains only SVG. */
'use strict';

const fs = require('node:fs');
const path = require('node:path');
const { createRequire } = require('node:module');

function render(source, modules, theme) {
  if (!['light', 'dark'].includes(theme)) throw new Error('theme must be light or dark');
  const fromTools = createRequire(path.join(path.resolve(modules), '_diagram_entry.cjs'));
  const JSON5 = fromTools('json5');
  const wavedrom = fromTools('wavedrom');
  const onml = fromTools('onml');
  const skins = {
    ...fromTools('wavedrom/skins/default.js'),
    ...fromTools('wavedrom/skins/dark.js'),
  };
  const diagram = JSON5.parse(source);
  if (!diagram || !Array.isArray(diagram.signal) || !diagram.signal.length) {
    throw new Error('WaveDrom source must contain a non-empty signal array');
  }
  // Theme selection is build configuration, never extra work for the author.
  diagram.config = { ...diagram.config, skin: theme === 'dark' ? 'dark' : 'default' };
  const svg = wavedrom.renderAny(0, diagram, skins);
  // WaveDrom 3.7's renderer hardcodes a white canvas even with the dark skin.
  // Change only that canvas; keep all waveform colors supplied by the skin.
  const body = svg.find((item) => Array.isArray(item) && item[0] === 'g' && item[1]?.id === 'waves_0');
  if (!body || body[2]?.[0] !== 'rect') throw new Error('Unsupported WaveDrom canvas structure');
  body[2][1].style = `stroke:none;fill:${theme === 'dark' ? '#111827' : '#ffffff'}`;
  // Standalone SVG must carry a namespace even outside an HTML document.
  svg[1] = { ...svg[1], xmlns: 'http://www.w3.org/2000/svg',
    'xmlns:xlink': 'http://www.w3.org/1999/xlink' };
  return onml.stringify(svg);
}

module.exports = { render };
if (require.main === module) {
  try {
    const args = process.argv.slice(2);
    const value = (key) => args[args.indexOf(key) + 1];
    if (!args.includes('--modules') || !args.includes('--theme')) {
      throw new Error('Usage: node render_wavedrom.cjs --modules DIR --theme light|dark < source.json5');
    }
    process.stdout.write(render(fs.readFileSync(0, 'utf8'), value('--modules'), value('--theme')));
  } catch (error) {
    process.stderr.write(`WaveDrom: ${error.message}\n`);
    process.exitCode = 1;
  }
}
