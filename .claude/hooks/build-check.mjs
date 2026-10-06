// PostToolUse hook: after Edit/Write on a file under client/, run the frontend
// build (tsc -b && vite build). On failure, exit 2 so the errors are fed back
// to Claude.
import { spawnSync } from "node:child_process";
import { readFileSync } from "node:fs";
import path from "node:path";

const input = JSON.parse(readFileSync(0, "utf8"));
const file = input.tool_response?.filePath ?? input.tool_input?.file_path;
if (!file) process.exit(0);

const clientDir = path.resolve(input.cwd ?? process.cwd(), "client");
const rel = path.relative(clientDir, path.resolve(file));
const inClient = !rel.startsWith("..") && !path.isAbsolute(rel);
if (!inClient || !/\.(tsx?|css|html|json)$/.test(rel)) process.exit(0);

const result = spawnSync("npm run build", {
  cwd: clientDir,
  shell: true,
  encoding: "utf8",
});
if (result.status !== 0) {
  process.stderr.write(`Frontend build failed after editing ${rel}:\n${result.stdout}${result.stderr}`);
  process.exit(2);
}
