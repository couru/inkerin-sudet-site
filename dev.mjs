import { createReadStream, existsSync, statSync } from "node:fs";
import { createServer } from "node:http";
import { extname, join, normalize } from "node:path";

const root = new URL(".", import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, "$1");
const types = {
  ".css": "text/css; charset=utf-8",
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".png": "image/png",
  ".svg": "image/svg+xml",
};

const server = createServer((request, response) => {
  const path = decodeURIComponent(new URL(request.url, "http://localhost").pathname);
  const relative = path === "/" ? "index.html" : path.replace(/^\/+/, "");
  let file = normalize(join(root, relative));
  if (relative.startsWith("brand/") || relative.startsWith("fonts/") || relative === "og.png") {
    file = normalize(join(root, "public", relative));
  }
  if (!file.startsWith(normalize(root)) || !existsSync(file) || statSync(file).isDirectory()) {
    response.writeHead(404).end("Not found");
    return;
  }
  response.writeHead(200, { "Content-Type": types[extname(file)] || "application/octet-stream" });
  createReadStream(file).pipe(response);
});

server.listen(3000, "127.0.0.1", () => {
  console.log("Local URL: http://127.0.0.1:3000");
});
