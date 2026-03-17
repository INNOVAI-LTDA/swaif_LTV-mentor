import assert from "node:assert/strict";

import {
  AppError,
  toUserErrorMessage,
  shouldForceLogout,
} from "../../lib/errors.js";
import { httpClient } from "../../lib/httpClient.js";
import { onUnauthorized } from "../../lib/httpEvents.js";
import {
  clearAccessToken,
  getAccessToken,
  setAccessToken,
} from "../../lib/authStorage.js";

async function run(name, fn) {
  try {
    await fn();
    console.log(`PASS - ${name}`);
  } catch (error) {
    console.error(`FAIL - ${name}`);
    console.error(error?.stack || String(error));
    process.exitCode = 1;
  }
}

await run("toUserErrorMessage maps expected HTTP statuses", async () => {
  assert.equal(
    toUserErrorMessage(new AppError({ httpStatus: 401, message: "x" })),
    "Sessao expirada ou token invalido. Faca login novamente."
  );
  assert.equal(
    toUserErrorMessage(new AppError({ httpStatus: 403, message: "x" })),
    "Voce nao tem permissao para acessar este recurso."
  );
  assert.equal(
    toUserErrorMessage(new AppError({ httpStatus: 404, message: "x" })),
    "Recurso nao encontrado."
  );
  assert.equal(
    toUserErrorMessage(new AppError({ httpStatus: 409, message: "x" })),
    "Conflito de dados. Atualize e tente novamente."
  );
  assert.equal(
    toUserErrorMessage(new AppError({ httpStatus: 422, message: "x" })),
    "Dados invalidos para esta operacao."
  );
});

await run("shouldForceLogout handles status and auth codes", async () => {
  assert.equal(shouldForceLogout(new AppError({ httpStatus: 401 })), true);
  assert.equal(shouldForceLogout(new AppError({ httpStatus: 403 })), false);
  assert.equal(
    shouldForceLogout(new AppError({ httpStatus: 0, code: "AUTH_EXPIRED_TOKEN" })),
    true
  );
});

await run("httpClient 401 clears token and emits unauthorized event", async () => {
  clearAccessToken();
  setAccessToken("token_f6");
  assert.equal(getAccessToken(), "token_f6");

  let eventCount = 0;
  const unsubscribe = onUnauthorized((event) => {
    eventCount += 1;
    assert.equal(event.status, 401);
    assert.equal(event.code, "AUTH_INVALID_TOKEN");
  });

  const previousFetch = globalThis.fetch;
  globalThis.fetch = async () => ({
    ok: false,
    status: 401,
    text: async () =>
      JSON.stringify({
        error: {
          status: 401,
          code: "AUTH_INVALID_TOKEN",
          message: "Token invalido.",
          details: null,
        },
      }),
  });

  try {
    await assert.rejects(
      () => httpClient.get("/me", { token: "token_f6" }),
      (error) => {
        assert.ok(error instanceof AppError);
        assert.equal(error.httpStatus, 401);
        return true;
      }
    );
    assert.equal(getAccessToken(), null);
    assert.equal(eventCount, 1);
  } finally {
    unsubscribe();
    globalThis.fetch = previousFetch;
    clearAccessToken();
  }
});

if (process.exitCode && process.exitCode !== 0) {
  console.error("F6 hardening runner finished with failures.");
  process.exit(process.exitCode);
}

console.log("F6 hardening runner: PASS");
