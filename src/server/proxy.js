/**
 * Clean Gemini Proxy Server
 * ---------------------------------------
 * - Minimal
 * - Only API key auth (recommended)
 * - Uses generateContent endpoint
 * - Easy to customize
 */

const express = require("express");
const axios = require("axios");
const cors = require("cors");

// ----------------------
// Environment Variables
// ----------------------
const API_KEY = process.env.GEMINI_API_KEY;
const MODEL = process.env.GEMINI_MODEL || "gemini-1.5-flash";
const API_BASE = process.env.GENERATIVE_API_BASE || "https://generativelanguage.googleapis.com";
const API_VERSION = process.env.GENERATIVE_API_VERSION || "v1beta";

// Construct final endpoint
const GEMINI_ENDPOINT = `${API_BASE}/${API_VERSION}/models/${MODEL}:generateContent`;

if (!API_KEY) {
  console.warn("⚠️  Warning: GEMINI_API_KEY is not set. Requests will fail with 401.");
}

// ----------------------
// App Setup
// ----------------------
const app = express();
app.use(cors());
app.use(express.json());

// Health check (optional)
app.get("/", (req, res) => {
  res.json({ status: "ok", model: MODEL });
});

// ----------------------
// Main Proxy Route
// ----------------------
app.post("/api/generate", async (req, res) => {
  try {
    const { prompt, system, maxTokens } = req.body || {};
    if (!prompt) {
      return res.status(400).json({ error: "Missing 'prompt' in request body." });
    }

    if (!API_KEY) {
      return res.status(401).json({ error: "Server missing GEMINI_API_KEY environment variable." });
    }

    // Gemini request body format
    const payload = {
      contents: [
        {
          role: "user",
          parts: [{ text: prompt }],
        },
      ],
    };

    if (system) {
      payload.systemInstruction = { parts: [{ text: system }] };
    }

    if (maxTokens) {
      payload.generationConfig = { maxOutputTokens: maxTokens };
    }

    // Send request to Gemini
    const response = await axios.post(
      `${GEMINI_ENDPOINT}?key=${API_KEY}`,
      payload,
      { headers: { "Content-Type": "application/json" } }
    );

    const data = response.data;

    // Extract model text
    const text =
      data?.candidates?.[0]?.content?.parts?.[0]?.text ??
      data?.text ??
      null;

    return res.json({ ok: true, text, raw: data });
  } catch (err) {
    const status = err.response?.status || 500;
    const details = err.response?.data || { message: err.message };

    console.error("❌ Gemini Proxy Error:", JSON.stringify(details, null, 2));

    return res.status(status).json({
      ok: false,
      error: details,
    });
  }
});

// ----------------------
// Start Server
// ----------------------
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`----------------------------------------------`);
  console.log(` Gemini Proxy Running`);
  console.log(` URL:        http://localhost:${PORT}`);
  console.log(` Model:      ${MODEL}`);
  console.log(` Endpoint:   ${GEMINI_ENDPOINT}`);
  console.log(`----------------------------------------------`);
});
