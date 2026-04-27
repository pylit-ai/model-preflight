// Example bridge for JS/agent-hook projects: keep provider logic in ModelPreflight,
// shell out through the CLI, and parse JSON artifacts when needed.
import { spawnSync } from "node:child_process";

const prompt = process.argv.slice(2).join(" ") || "Return only: ok";
const result = spawnSync("mpf", ["pro", prompt, "--n", "4"], { encoding: "utf8" });
if (result.status !== 0) {
  console.error(result.stderr || result.stdout);
  process.exit(result.status ?? 1);
}
console.log(result.stdout);
