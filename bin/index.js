#!/usr/bin/env node

import { cpSync, existsSync, mkdirSync } from "node:fs";
import { join } from "node:path";
import { argv, cwd, exit } from "node:process";
import { fileURLToPath } from "node:url";

const RESET = "\x1b[0m";
const BOLD = "\x1b[1m";
const GREEN = "\x1b[32m";
const YELLOW = "\x1b[33m";
const RED = "\x1b[31m";
const CYAN = "\x1b[36m";

function log(color, symbol, message) {
  console.log(`${color}${symbol}${RESET} ${message}`);
}

const packageRoot = join(fileURLToPath(import.meta.url), "..", "..");
const destination = argv[2] ? argv[2] : cwd();

const targets = [
  { src: join(packageRoot, ".amtcz"), dest: join(destination, ".amtcz") },
  { src: join(packageRoot, ".claude"), dest: join(destination, ".claude") },
];

console.log();
console.log(
  `${BOLD}${CYAN}Amatsucozy AI Workflow Installer${RESET}`
);
console.log(`Installing into: ${BOLD}${destination}${RESET}`);
console.log();

const force = argv.includes("--force");
let anyInstalled = false;

for (const { src, dest } of targets) {
  const name = src.split("/").pop();

  if (!existsSync(src)) {
    continue;
  }

  if (existsSync(dest) && !force) {
    log(YELLOW, "⚠", `${name}/ already exists – skipping (use --force to overwrite)`);
    continue;
  }

  try {
    mkdirSync(dest, { recursive: true });
    cpSync(src, dest, { recursive: true, force: true });
    log(GREEN, "✔", `Installed ${name}/`);
    anyInstalled = true;
  } catch (err) {
    log(RED, "✘", `Failed to install ${name}/: ${err.message}`);
    exit(1);
  }
}

console.log();

if (anyInstalled) {
  log(GREEN, "✔", `${BOLD}Done!${RESET} Amatsucozy AI Workflow is ready.`);
  console.log();
  console.log("  Next steps:");
  console.log("  1. Open your AI assistant (Claude, Copilot, etc.).");
  console.log('  2. Say: "*activate" to start the workflow.');
  console.log(
    "  3. Use *start-workflow [--auto] to kick off a new task.\n"
  );
} else {
  log(
    YELLOW,
    "ℹ",
    "Nothing was installed (all directories already exist). Run with --force to overwrite."
  );
  console.log();
}
