const assert = require('node:assert/strict');

const imageSize = require('image-size');
const craftedIcns = Buffer.alloc(16);
craftedIcns.write('icns', 0, 'ascii');
craftedIcns.writeUInt32BE(16, 4);
craftedIcns.write('ic07', 8, 'ascii');
craftedIcns.writeUInt32BE(0, 12);

const startedAt = Date.now();
assert.throws(
  () => imageSize(craftedIcns),
  /Invalid ICNS image entry length/,
);
assert.ok(Date.now() - startedAt < 1000, 'malformed ICNS input must fail without hanging');

console.log('image-size ICNS zero-length entry rejected without a loop');
