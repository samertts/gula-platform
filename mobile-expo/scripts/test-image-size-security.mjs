import assert from "node:assert/strict";
import { createRequire } from "node:module";
import imageSizeEsm from "../vendor/image-size/dist/index.mjs";

const require = createRequire(import.meta.url);
const { imageSize: imageSizeCjs } = require("../vendor/image-size/dist/index.cjs");

const ascii = (value) => Uint8Array.from(value, (character) => character.charCodeAt(0));

function makeIcnsWithZeroEntry() {
  const input = new Uint8Array(16);
  input.set(ascii("icns"), 0);
  new DataView(input.buffer).setUint32(4, input.length, false);
  input.set(ascii("ic08"), 8);
  new DataView(input.buffer).setUint32(12, 0, false);
  return input;
}

function makeZeroBoxContainer(signature) {
  const input = new Uint8Array(16);
  input.set(new Uint8Array([0, 0, 0, 0]), 0);
  input.set(ascii(signature), 4);
  return input;
}

function assertRejectsQuickly(reader, input, label) {
  const started = performance.now();
  assert.throws(() => reader(input), /Invalid ICNS entry length|unsupported file type/);
  assert.ok(performance.now() - started < 100, `${label} took too long to reject`);
}

for (const reader of [imageSizeEsm, imageSizeCjs]) {
  assertRejectsQuickly(reader, makeIcnsWithZeroEntry(), "ICNS zero entry");
  assertRejectsQuickly(reader, makeZeroBoxContainer("ftyp"), "HEIF zero box");
  assertRejectsQuickly(reader, makeZeroBoxContainer("JXL "), "JXL zero box");
}

console.log("image-size security parser checks passed");
