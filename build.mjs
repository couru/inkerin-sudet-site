import { cp, mkdir, readFile, rm, writeFile } from "node:fs/promises";

const output = new URL("./dist/", import.meta.url);
const client = new URL("./dist/client/", import.meta.url);
const server = new URL("./dist/server/", import.meta.url);

await rm(output, { recursive: true, force: true });
await mkdir(client, { recursive: true });
await mkdir(server, { recursive: true });

for (const file of ["index.html", "styles.css", "script.js"]) {
  await cp(new URL(`./${file}`, import.meta.url), new URL(`./dist/client/${file}`, import.meta.url));
}
await cp(new URL("./public/", import.meta.url), client, { recursive: true });

const worker = `export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const assetRequest = url.pathname === "/" ? new Request(new URL("/index.html", url), request) : request;
    const response = await env.ASSETS.fetch(assetRequest);
    if (response.status !== 404 || url.pathname.includes(".")) return response;
    return env.ASSETS.fetch(new Request(new URL("/index.html", url), request));
  },
};\n`;

await writeFile(new URL("./dist/server/index.js", import.meta.url), worker, "utf8");

const html = await readFile(new URL("./dist/client/index.html", import.meta.url), "utf8");
if (!html.includes('<html lang="ru">') || !html.includes("script.js")) {
  throw new Error("Static site validation failed");
}
console.log("Static site built successfully.");
