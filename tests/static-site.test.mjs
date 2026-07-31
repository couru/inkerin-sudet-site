import assert from "node:assert/strict";
import { access, readFile } from "node:fs/promises";
import test from "node:test";

test("builds a framework-free static site", async () => {
  const [source, output, script, stylesheet] = await Promise.all([
    readFile(new URL("../index.html", import.meta.url), "utf8"),
    readFile(new URL("../dist/client/index.html", import.meta.url), "utf8"),
    readFile(new URL("../script.js", import.meta.url), "utf8"),
    readFile(new URL("../styles.css", import.meta.url), "utf8"),
  ]);

  assert.match(source, /<html lang="ru">/);
  assert.match(source, /id="trial-form"/);
  assert.match(source, /href="\.\/styles\.css\?v=20260731-4"/);
  assert.match(source, /src="\.\/script\.js"/);
  assert.match(source, /class="brandEmblem"[\s\S]*src="\.\/brand\/crest-blue\.png"/);
  assert.match(source, /<small>ингерманландские волки<\/small>/);
  assert.match(source, /href="mailto:couru@mail\.ru">couru@mail\.ru<\/a>/);
  assert.doesNotMatch(source, /(?:В СТАЕ|ИГРА|ОДНА ЦЕЛЬ|ЛЁД)\.<\/span>/);
  assert.doesNotMatch(source, /(?:src|href|content)="\/(?:brand|og\.png|styles\.css|script\.js)/);
  assert.doesNotMatch(source, /__NEXT_DATA__|react|next\//i);
  assert.equal(output, source);
  assert.match(script, /IntersectionObserver/);
  assert.match(stylesheet, /overflow-x: clip/);
  assert.match(stylesheet, /font-family: "Inkerin Sans"/);
  assert.match(stylesheet, /RobotoCondensed-Variable\.ttf/);
  assert.doesNotMatch(stylesheet, /font-family:\s*(?:Impact|"Courier New"|Arial)/);
  assert.match(stylesheet, /\.age strong\s*\{[\s\S]*?white-space: nowrap;/);
  assert.match(stylesheet, /\.kitContent h2\s*\{[\s\S]*?overflow-wrap: normal;/);
  assert.match(stylesheet, /@media \(max-width: 900px\)/);
  await access(new URL("../public/fonts/RobotoCondensed-Variable.ttf", import.meta.url));
  await access(new URL("../dist/server/index.js", import.meta.url));
});
