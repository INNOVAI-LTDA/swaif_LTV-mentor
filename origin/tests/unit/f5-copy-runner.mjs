import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const files = [
  "../../jpe-command-center.jsx",
  "../../radar-longevidade.jsx",
  "../../matriz-renovacao.jsx",
  "../../jpe-hub.jsx",
];

const bannedPatterns = [
  { name: "paciente", regex: /\bpacientes?\b/i },
  { name: "clinica/clinico", regex: /\bcl[ií]nic[ao]s?\b/i },
  { name: "medico", regex: /\bm[eé]dic[oa]s?\b/i },
  { name: "biomarcador", regex: /\bbiomarcadores?\b/i },
  { name: "idade bio", regex: /\bidade\s+bio\b/i },
  { name: "jornada biologica", regex: /\bjornada\s+biol[oó]gic[ao]\b/i },
  { name: "causa provavel", regex: /\bcausa\s+prov[aá]vel\b/i },
];

function extractStringLiterals(source) {
  const literalRegex = /(["'`])(?:\\[\s\S]|(?!\1)[^\\])*\1/gm;
  return source.match(literalRegex) ?? [];
}

function run(name, fn) {
  try {
    fn();
    console.log(`PASS - ${name}`);
  } catch (error) {
    console.error(`FAIL - ${name}`);
    console.error(error?.stack || String(error));
    process.exitCode = 1;
  }
}

run("copy uses mentoria terms in UI string literals", () => {
  const issues = [];

  for (const relFile of files) {
    const absFile = path.resolve(__dirname, relFile);
    const source = fs.readFileSync(absFile, "utf8");
    const literals = extractStringLiterals(source);

    for (const rawLiteral of literals) {
      const literal = rawLiteral.slice(1, -1);
      for (const banned of bannedPatterns) {
        if (banned.regex.test(literal)) {
          issues.push({
            file: relFile.replace("../../", "origin/"),
            term: banned.name,
            literal: literal.slice(0, 120),
          });
        }
      }
    }
  }

  if (issues.length > 0) {
    const details = issues
      .map((issue) => `- ${issue.file} | ${issue.term} | "${issue.literal}"`)
      .join("\n");
    assert.fail(`Foram encontrados termos proibidos em strings de UI:\n${details}`);
  }
});

if (process.exitCode && process.exitCode !== 0) {
  console.error("F5 copy runner finished with failures.");
  process.exit(process.exitCode);
}

console.log("F5 copy runner: PASS");
