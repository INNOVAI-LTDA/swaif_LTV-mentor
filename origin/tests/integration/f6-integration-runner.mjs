import assert from "node:assert/strict";

import { AppError } from "../../lib/errors.js";
import { getUnifiedStudentDetail, getUnifiedStudents } from "../../services/studentsService.js";
import { getRenewalMatrix } from "../../services/matrixService.js";
import { listCommandCenterStudents } from "../../services/commandCenterService.js";

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

await run("services integrate center+matrix for unified students", async () => {
  const restore = installFetchRouter({
    "GET /admin/centro-comando/alunos": () =>
      toHttpResponse(200, [
        {
          id: "std_1",
          name: "Aluno 1",
          plan: "Mentoria Scale",
          progress: 0.6,
          engagement: 0.8,
          daysLeft: 40,
          urgency: "watch",
          ltv: 12000,
        },
      ]),
    "GET /admin/matriz-renovacao?filter=all": () =>
      toHttpResponse(200, {
        filter: "all",
        items: [
          {
            id: "std_1",
            full_name: "Aluno 1",
            plan: "Mentoria Scale",
            renewalReason: "Bom momento para renovar.",
            suggestion: "Ciclo 2 Mentoria Scale",
            markers: [],
          },
        ],
        kpis: {
          totalLTV: 12000,
          criticalRenewals: 1,
          rescueCount: 0,
          avgEngagement: 0.8,
        },
      }),
  });

  try {
    const students = await getUnifiedStudents();
    assert.equal(students.length, 1);
    assert.equal(students[0].programName, "Mentoria Scale");
    assert.equal(students[0].name, "Aluno 1");
    assert.equal(students[0].renewalReason, "Bom momento para renovar.");
    assert.equal(students[0].suggestion, "Ciclo 2 Mentoria Scale");
  } finally {
    restore();
  }
});

await run("detail flow merges command center detail with matrix info", async () => {
  const restore = installFetchRouter({
    "GET /admin/centro-comando/alunos/std_1": () =>
      toHttpResponse(200, {
        id: "std_1",
        name: "Aluno 1",
        programName: "Mentoria Scale",
        renewalReason: "Momento de consolidacao.",
        suggestion: "Proposta ciclo 2",
        metricValues: [],
        checkpoints: [],
      }),
    "GET /admin/matriz-renovacao?filter=all": () =>
      toHttpResponse(200, {
        filter: "all",
        items: [
          {
            id: "std_1",
            full_name: "Aluno 1",
            plan: "Mentoria Scale",
            renewalReason: "Momento de consolidacao.",
            suggestion: "Proposta ciclo 2",
            markers: [{ label: "Entrega", value: "80", target: "100", pct: 80 }],
          },
        ],
        kpis: {
          totalLTV: 0,
          criticalRenewals: 0,
          rescueCount: 0,
          avgEngagement: 0,
        },
      }),
  });

  try {
    const detail = await getUnifiedStudentDetail("std_1");
    assert.equal(detail.id, "std_1");
    assert.equal(detail.renewalReason, "Momento de consolidacao.");
    assert.equal(detail.suggestion, "Proposta ciclo 2");
    assert.equal(Array.isArray(detail.metricValues), true);
  } finally {
    restore();
  }
});

await run("matrix service preserves 422 as AppError", async () => {
  const restore = installFetchRouter({
    "GET /admin/matriz-renovacao?filter=critical": () =>
      toHttpResponse(422, {
        error: {
          status: 422,
          code: "VALIDATION_ERROR",
          message: "Filtro invalido.",
          details: { filter: "critical" },
        },
      }),
  });

  try {
    await assert.rejects(
      () => getRenewalMatrix("critical"),
      (error) => {
        assert.ok(error instanceof AppError);
        assert.equal(error.httpStatus, 422);
        assert.equal(error.code, "VALIDATION_ERROR");
        return true;
      }
    );
  } finally {
    restore();
  }
});

await run("command center list handles contract drift fallback", async () => {
  const restore = installFetchRouter({
    "GET /admin/centro-comando/alunos": () =>
      toHttpResponse(200, { unexpected: true }),
  });

  try {
    const list = await listCommandCenterStudents();
    assert.deepEqual(list, []);
  } finally {
    restore();
  }
});

if (process.exitCode && process.exitCode !== 0) {
  console.error("F6 integration runner finished with failures.");
  process.exit(process.exitCode);
}

console.log("F6 integration runner: PASS");
