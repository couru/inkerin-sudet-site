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
  assert.match(source, /src="\.\/script\.js"/);
  assert.doesNotMatch(source, /(?:src|href|content)="\/(?:brand|og\.png|styles\.css|script\.js)/);
  assert.doesNotMatch(source, /__NEXT_DATA__|react|next\//i);
  assert.equal(output, source);
  assert.match(script, /IntersectionObserver/);
  assert.match(stylesheet, /@media \(max-width: 760px\)/);
  await access(new URL("../dist/server/index.js", import.meta.url));
});
