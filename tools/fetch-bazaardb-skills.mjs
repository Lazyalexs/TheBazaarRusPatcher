#!/usr/bin/env node
/**
 * Fetch all Skills from bazaardb.gg and dump their raw cards
 * (with all fields) to a JSON file. Skills are server-side text not
 * present in local cards.json, so we need them separately for the
 * translation pipeline.
 *
 * Usage:
 *   node tools/fetch-bazaardb-skills.mjs
 */

import { writeFile } from "node:fs/promises";
import { resolve } from "node:path";
import { setTimeout as delay } from "node:timers/promises";
import https from "node:https";

const HOST = "https://sin.bazaardb.gg";
const CATEGORY = "skills";
const OUT = "tools/.bazaardb-skills.json";
const DELAY_MS = 80;

function fetchText(url, attempts = 3) {
  return new Promise((res, rej) => {
    const req = https.get(
      url,
      {
        family: 4,
        headers: {
          "User-Agent": "TheBazaarRusPatcherSkillSync/0.1",
          Accept: "text/html,application/xhtml+xml",
        },
        timeout: 30_000,
      },
      (response) => {
        let body = "";
        response.setEncoding("utf8");
        response.on("data", (c) => (body += c));
        response.on("end", async () => {
          if (response.statusCode >= 500 && attempts > 1) {
            await delay(500);
            return fetchText(url, attempts - 1).then(res, rej);
          }
          if (response.statusCode < 200 || response.statusCode >= 300) {
            return rej(new Error(`HTTP ${response.statusCode} for ${url}`));
          }
          res(body);
        });
      },
    );
    req.on("timeout", () => req.destroy(new Error(`timeout ${url}`)));
    req.on("error", async (e) => {
      if (attempts > 1) {
        await delay(500);
        return fetchText(url, attempts - 1).then(res, rej);
      }
      rej(e);
    });
  });
}

function decodeNextFlight(html) {
  const chunks = [];
  const pattern = /self\.__next_f\.push\(\[1,"((?:\\.|[^"\\])*)"\]\)<\/script>/g;
  for (const m of html.matchAll(pattern)) {
    chunks.push(JSON.parse(`"${m[1]}"`));
  }
  return chunks.join("");
}

function extractJsonObject(source, start) {
  let depth = 0;
  let inString = false;
  let escaped = false;
  for (let i = start; i < source.length; i += 1) {
    const ch = source[i];
    if (inString) {
      if (escaped) escaped = false;
      else if (ch === "\\") escaped = true;
      else if (ch === '"') inString = false;
      continue;
    }
    if (ch === '"') {
      inString = true;
      continue;
    }
    if (ch === "{") depth += 1;
    else if (ch === "}") {
      depth -= 1;
      if (depth === 0) return source.slice(start, i + 1);
    }
  }
  throw new Error("could not find end of initialData object");
}

function extractInitialData(html) {
  const unescaped = decodeNextFlight(html) || html;
  const idx = unescaped.indexOf('"initialData":');
  if (idx === -1) throw new Error("no initialData marker");
  return JSON.parse(extractJsonObject(unescaped, idx + '"initialData":'.length));
}

function pageUrl(page) {
  const u = new URL("/search", HOST);
  u.searchParams.set("c", CATEGORY);
  u.searchParams.set("page", String(page));
  return u.toString();
}

async function main() {
  const first = await extractInitialData(await fetchText(pageUrl(1)));
  const total = first.total ?? first.pageCards?.length ?? 0;
  const pageSize = first.pageCards?.length ?? 10;
  const pageCount = Math.ceil(total / pageSize);
  const cards = new Map();

  const add = (list) => {
    for (const c of list ?? []) {
      // Accept ALL types here — typically Type==="Skill"
      cards.set(c.Id, c);
    }
  };

  add(first.pageCards);
  console.log(`page 1/${pageCount} (${cards.size}/${total})`);

  for (let p = 2; p <= pageCount; p += 1) {
    await delay(DELAY_MS);
    const data = await extractInitialData(await fetchText(pageUrl(p)));
    add(data.pageCards);
    console.log(`page ${p}/${pageCount} (${cards.size}/${total})`);
  }

  const arr = [...cards.values()];
  await writeFile(resolve(OUT), JSON.stringify(arr, null, 2), "utf8");
  console.log(`Wrote ${arr.length} skills to ${OUT}`);

  // Print field summary for one card so we can plan extraction
  if (arr.length) {
    console.log("\nFirst skill (sample structure):");
    const k = Object.keys(arr[0]).sort();
    console.log("Keys:", k.join(", "));
    const sample = arr[0];
    const titleText = sample.Title?.Text;
    const descText = sample.Description?.Text;
    const tooltipsCount = (sample.Tooltips ?? []).length;
    console.log(`Title: ${titleText}`);
    console.log(`Description: ${descText}`);
    console.log(`Tooltips: ${tooltipsCount}`);
  }
}

main().catch((e) => {
  console.error(e.stack || e);
  process.exit(1);
});
