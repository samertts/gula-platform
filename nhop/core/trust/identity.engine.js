"use strict";

/*
 NHOP DIGITAL TRUST ENGINE
 Cryptographic identity layer
*/

const crypto = require("crypto");

const activeIdentities = new Map();

/* create identity */
function createIdentity(userId, role) {

  const keyPair = crypto.generateKeyPairSync("rsa", {
    modulusLength: 2048
  });

  const identity = {
    userId,
    role,
    publicKey:
      keyPair.publicKey.export({
        type: "pkcs1",
        format: "pem"
      }),
    privateKey:
      keyPair.privateKey.export({
        type: "pkcs1",
        format: "pem"
      })
  };

  activeIdentities.set(userId, identity);

  return identity;
}

/* sign request */
function signPayload(privateKey, payload) {

  const sign = crypto.createSign("SHA256");

  sign.update(JSON.stringify(payload));

  return sign.sign(privateKey, "base64");
}

/* verify signature */
function verify(publicKey, payload, signature) {

  const verify = crypto.createVerify("SHA256");

  verify.update(JSON.stringify(payload));

  return verify.verify(publicKey, signature, "base64");
}

function getIdentity(userId) {
  return activeIdentities.get(userId);
}

module.exports = {
  createIdentity,
  signPayload,
  verify,
  getIdentity
};
