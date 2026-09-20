// ponytail: Minimal seeder. No complex factory patterns.
async function seedDatabase() {
  console.log("🌱 Seeding database with test repository...");
  try {
    // Using query param instead of header for better reliability in tests
    const response = await fetch('http://localhost:8008/repositories/octocat/Hello-World/refresh?user_id=test_user', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        access_token: 'mock_token'
      })
    });

    if (!response.ok) {
      const errText = await response.text();
      throw new Error(`Server responded with ${response.status}: ${errText}`);
    }

    const data = await response.json();
    console.log("✅ Seeded successfully:", data.full_name || "Repository synced");
  } catch (e) {
    console.error("❌ Seeding failed:", (e as Error).message);
    process.exit(1);
  }
}

seedDatabase();
