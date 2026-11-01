// Bundles the deck into dist/: index.html, deck.js, deck.css and assets/.
// Same setup as the talks on mehdio.com (React + esbuild, 1600 x 900 canvas).
//   npm run build     one build
//   npm run watch     rebuild on change
import { context } from 'esbuild'
import fs from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const root = path.dirname(fileURLToPath(import.meta.url))
const out = path.join(root, 'dist')
const watch = process.argv.includes('--watch')

const title = 'The Next Data Stack Has No UI · MotherDuck workshop'
const description =
  'Build an analytics agent end to end, and map each fundamental to MotherDuck. Mehdi Ouazza and Jacob Matson.'

await fs.mkdir(out, { recursive: true })
await fs.cp(path.join(root, 'assets'), path.join(out, 'assets'), { recursive: true })
await fs.writeFile(
  path.join(out, 'index.html'),
  `<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>${title}</title>
<meta name="description" content="${description}">
<link rel="stylesheet" href="deck.css"></head><body><div id="root"></div><script defer src="deck.js"></script></body></html>
`
)

const ctx = await context({
  absWorkingDir: root,
  entryPoints: ['src/main.tsx'],
  bundle: true,
  outfile: path.join(out, 'deck.js'),
  minify: !watch,
  format: 'iife',
  target: ['es2020'],
  jsx: 'automatic',
  define: { 'process.env.NODE_ENV': watch ? '"development"' : '"production"' },
  external: ['assets/*'],
  legalComments: 'eof',
  logLevel: 'info'
})

if (watch) {
  await ctx.watch()
  console.log('Watching. Open dist/index.html and reload after edits.')
} else {
  await ctx.rebuild()
  await ctx.dispose()
  console.log('Built deck at', path.relative(process.cwd(), out) || '.')
}
