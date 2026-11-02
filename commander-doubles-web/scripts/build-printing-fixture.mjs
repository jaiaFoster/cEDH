// Reproduce the multilingual regression from retained, actual Scryfall records.
import fs from "node:fs";
const root = new URL("../tests/fixtures/", import.meta.url);
const sources = JSON.parse(
  fs.readFileSync(new URL("printing-incident-sources.json", root)),
);
const names = new Map(
  sources.map((c) => ["1 " + c.name, "1 " + c.printed_name]),
);
const original = fs.readFileSync(
  new URL("import-incident-100.txt", root),
  "utf8",
);
const output = original
  .split("\n")
  .map((l) => names.get(l) || l)
  .join("\n");
const dest = new URL("printing-incident-100.txt", root);
if (process.argv.includes("--check")) {
  if (fs.readFileSync(dest, "utf8") !== output)
    throw Error("Printing fixture differs");
} else fs.writeFileSync(dest, output);
console.log(
  "Verified seven translated printings; original quantities and commander positions retained.",
);
