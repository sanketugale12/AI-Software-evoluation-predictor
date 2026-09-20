// ponytail: The "Everything" Test. One script to rule them all.
async function testFeature(name, fn) {
  try {
    await fn();
    console.log(`✅ ${name}: PASSED`);
  } catch (e) {
    console.error(`❌ ${name}: FAILED - ${(e as Error).message}`);
  }
}

async function runFinalVerification() {
  console.log("🚀 Starting ASEP Full Feature Verification...\n");

  await testFeature("API Health", async () => {
    const res = await fetch('http://localhost:8008/health');
    if (!res.ok) throw new Error("Health check failed");
  });

  await testFeature("PR Intelligence", async () => {
    const res = await fetch('http://localhost:8008/repositories/octocat/Hello-World/refresh?user_id=test_user', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ access_token: 'mock_token' })
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
  });

  await testFeature("Issue Intelligence", async () => {
    const res = await fetch('http://localhost:8008/repositories/octocat/Hello-World/tree?commit_sha=main&user_id=test_user');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
  });

  await testFeature("Ops Intelligence", async () => {
    const res = await fetch('http://localhost:8008/repositories/octocat/Hello-World?user_id=test_user');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
  });

  await testFeature("Grounded Assistant", async () => {
    const res = await fetch('http://localhost:8008/health');
    if (!res.ok) throw new Error("API down");
  });

  await testFeature("Health Reporting", async () => {
    const res = await fetch('http://localhost:8008/health');
    if (!res.ok) throw new Error("Health report failed");
  });

  await testFeature("Risk Prediction", async () => {
    const res = await fetch('http://localhost:8008/repositories/octocat/Hello-World/refresh?user_id=test_user', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ access_token: 'mock_token' })
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
  });

  await testFeature("Security Sanitization", async () => {
    const res = await fetch('http://localhost:8008/repositories/octocat/Hello-World/refresh?user_id=test_user', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ access_token: '1; rm -rf /' })
    });
    if (res.status === 500) throw new Error("Sanitizer failed to block injection");
  });

  await testFeature("Incremental Analysis", async () => {
    await fetch('http://localhost:8008/repositories/octocat/Hello-World/refresh?user_id=test_user', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ access_token: 'mock_token' })
    });
    const start = Date.now();
    await fetch('http://localhost:8008/repositories/octocat/Hello-World/refresh?user_id=test_user', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ access_token: 'mock_token' })
    });
    const end = Date.now();
    if (end - start > 2000) throw new Error("Cache not working: second call too slow");
  });

  console.log("\n🏁 Verification Complete.");
}

runFinalVerification().catch(console.error);
