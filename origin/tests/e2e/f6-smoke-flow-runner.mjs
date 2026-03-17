import assert from "node:assert/strict";

import { AppError } from "../../lib/errors.js";
import { login, getMe } from "../../services/authService.js";
import { getUnifiedStudentDetail, getUnifiedStudents } from "../../services/studentsService.js";
import { getStudentRadar } from "../../services/radarService.js";
import { getRenewalMatrix } from "../../services/matrixService.js";
import { clearAccessToken, getAccessToken } from "../../lib/authStorage.js";

function toHttpResponse(status, payload) {
  return {
    ok: status >= 200 && status < 300,
    status,
    text: async () => JSON.stringify(payload),
  };
}

function installFetchRouter(routes) {
  const previousFetch = globalThis.fetch;
  globalThis.fetch = async (url, options = {}) => {
    const u = new URL(url);
    const key = `${(options.method || "GET").toUpperCase()} ${u.pathname}${u.search}`;
    const route = routes[key];
    if (!route) {
      return toHttpResponse(404, {
        error: {
          status: 404,
          code: "NOT_FOUND",
          message: `Rota mock nao encontrada: ${key}`,
          details: null,
        },
      });
    }
    return route();
  };
  return () => {
    globalThis.fetch = previousFetch;
  };
}

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

await run("smoke flow login + centro + radar + matriz", async () => {
  clearAccessToken();

  const restore = installFetchRouter({
    "POST /auth/login": () =>
      toHttpResponse(200, {
        access_token: "token_smoke_f6",
      }),
    "GET /me": () =>
      toHttpResponse(200, {
        username: "usr_admin",
        role: "admin",
      }),
    "GET /admin/centro-comando/alunos": () =>
      toHttpResponse(200, [
        {
          id: "std_1",
          name: "Aluno Smoke",
          plan: "Mentoria LTV",
          progress: 0.66,
          engagement: 0.72,
          daysLeft: 38,
          urgency: "watch",
          ltv: 18000,
        },
      ]),
    "GET /admin/centro-comando/alunos/std_1": () =>
      toHttpResponse(200, {
        id: "std_1",
        name: "Aluno Smoke",
        programName: "Mentoria LTV",
        metricValues: [],
        checkpoints: [],
      }),
    "GET /admin/radar/alunos/std_1": () =>
      toHttpResponse(200, {
        studentId: "std_1",
        axisScores: [
          {
            axisKey: "clareza",
            axisLabel: "Clareza",
            axisSub: "Direcionamento",
            baseline: 40,
            current: 62,
            projected: 76,
          },
        ],
      }),
    "GET /admin/matriz-renovacao?filter=all": () =>
      toHttpResponse(200, {
        filter: "all",
        items: [
          {
            id: "std_1",
            full_name: "Aluno Smoke",
            plan: "Mentoria LTV",
            renewalReason: "Evolucao consistente.",
            suggestion: "Renovacao ciclo 2",
            markers: [],
          },
        ],
        kpis: {
          totalLTV: 18000,
          criticalRenewals: 1,
          rescueCount: 0,
          avgEngagement: 0.72,
        },
      }),
    "GET /admin/matriz-renovacao?filter=critical": () =>
      toHttpResponse(200, {
        filter: "critical",
        items: [
          {
            id: "std_1",
            full_name: "Aluno Smoke",
            plan: "Mentoria LTV",
            renewalReason: "Evolucao consistente.",
            suggestion: "Renovacao ciclo 2",
            markers: [],
          },
        ],
        kpis: {
          totalLTV: 18000,
          criticalRenewals: 1,
          rescueCount: 0,
          avgEngagement: 0.72,
        },
      }),
  });

  try {
    const auth = await login({ email: "admin@swaif.dev", password: "123456" });
    assert.equal(auth.access_token, "token_smoke_f6");
    assert.equal(getAccessToken(), "token_smoke_f6");

    const me = await getMe();
    assert.equal(me.username, "usr_admin");

    const students = await getUnifiedStudents();
    assert.equal(students.length, 1);
    assert.equal(students[0].name, "Aluno Smoke");

    const detail = await getUnifiedStudentDetail("std_1");
    assert.equal(detail.id, "std_1");

    const radar = await getStudentRadar("std_1");
    assert.equal(radar.axisScores.length, 1);
    assert.equal(radar.axisScores[0].axisKey, "clareza");

    const matrix = await getRenewalMatrix("critical");
    assert.equal(matrix.filter, "critical");
    assert.equal(matrix.items.length, 1);
  } finally {
    restore();
    clearAccessToken();
  }
});

await run("critical flow: unauthorized clears token", async () => {
  clearAccessToken();
  const restore = installFetchRouter({
    "POST /auth/login": () =>
      toHttpResponse(200, {
        access_token: "token_bad_f6",
      }),
    "GET /me": () =>
      toHttpResponse(401, {
        error: {
          status: 401,
          code: "AUTH_EXPIRED_TOKEN",
          message: "Token expirado.",
          details: null,
        },
      }),
  });

  try {
    await login({ email: "admin@swaif.dev", password: "123456" });
    assert.equal(getAccessToken(), "token_bad_f6");

    await assert.rejects(
      () => getMe(),
      (error) => {
        assert.ok(error instanceof AppError);
        assert.equal(error.httpStatus, 401);
        return true;
      }
    );

    assert.equal(getAccessToken(), null);
  } finally {
    restore();
    clearAccessToken();
  }
});

if (process.exitCode && process.exitCode !== 0) {
  console.error("F6 e2e smoke runner finished with failures.");
  process.exit(process.exitCode);
}

console.log("F6 e2e smoke runner: PASS");
