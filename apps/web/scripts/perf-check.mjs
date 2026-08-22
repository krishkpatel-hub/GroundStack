import { readdir, stat } from "node:fs/promises";
import { join } from "node:path";

async function walk(dir) {
  const entries = await readdir(dir, { withFileTypes: true }).catch(() => []);
  const files = [];
  for (const entry of entries) {
    const path = join(dir, entry.name);
    if (entry.isDirectory()) files.push(...(await walk(path)));
    if (entry.isFile() && /\.(js|css)$/.test(entry.name)) files.push(path);
  }
  return files;
}

const root = new URL("../.next/static", import.meta.url).pathname;
const files = await walk(root);
const rows = await Promise.all(
  files.map(async (file) => ({ file, bytes: (await stat(file)).size })),
);
const total = rows.reduce((sum, row) => sum + row.bytes, 0);
const largest = rows.sort((a, b) => b.bytes - a.bytes).slice(0, 8);

console.log(`static_asset_count=${rows.length}`);
console.log(`static_asset_bytes=${total}`);
for (const row of largest) {
  console.log(`${row.bytes}\t${row.file.replace(process.cwd(), "")}`);
}

if (total > 2_500_000) {
  console.error("Static asset budget exceeded: 2.5 MB");
  process.exit(1);
}
