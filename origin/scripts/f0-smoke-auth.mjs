const API_BASE_URL = process.env.API_BASE_URL || "http://127.0.0.1:8000";
const email = process.env.SMOKE_EMAIL || "admin@swaif.local";
const password = process.env.SMOKE_PASSWORD || "admin123";

function fail(message, details = "") {
  console.error(`[F0 smoke] FAIL: ${message}`);
  if (details) console.error(details);
  process.exit(1);
}

async function parseJsonSafe(response) {
  const text = await response.text();
  if (!text) return null;
  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

async function run() {
  console.log(`[F0 smoke] API base: ${API_BASE_URL}`);
  console.log(`[F0 smoke] Step 1/2 login as ${email}`);

  const loginResponse = await fetch(`${API_BASE_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });

  const loginPayload = await parseJsonSafe(loginResponse);
  if (!loginResponse.ok) {
    fail("Login endpoint returned non-200.", JSON.stringify(loginPayload, null, 2));
  }

  const accessToken = loginPayload?.access_token;
  if (!accessToken) {
    fail("Login response does not contain access_token.", JSON.stringify(loginPayload, null, 2));
  }

  console.log("[F0 smoke] Step 2/2 call /me with bearer token");
  const meResponse = await fetch(`${API_BASE_URL}/me`, {
    method: "GET",
    headers: { Authorization: `Bearer ${accessToken}` },
  });
  const mePayload = await parseJsonSafe(meResponse);

  if (!meResponse.ok) {
    fail("/me endpoint returned non-200.", JSON.stringify(mePayload, null, 2));
  }

  console.log("[F0 smoke] PASS");
  console.log(JSON.stringify(mePayload, null, 2));
}

run().catch((error) => {
  fail("Unhandled exception while running smoke script.", error?.stack || String(error));
});

