// transcribe-live.mjs
// ======================================================
// HOW TO RUN THIS SCRIPT
// ======================================================
//
// 1. Install Node.js (version 18 or higher recommended)
//
//    Check installation:
//    node -v
//
// 2. Navigate to the folder containing this file
//
//    cd <project-folder>
//
// 3. Install project dependencies
//
//    npm install
//
// 4. Set required environment variables (if needed)
//
//    export AWS_ACCESS_KEY_ID=your_key
//    export AWS_SECRET_ACCESS_KEY=your_secret
//    export AWS_REGION=us-east-1
//
//    OR use a .env file if the project supports dotenv.
//
// 5. Run the live transcription script
//
//    node transcribe-live.mjs
//
// 6. Speak into the microphone to start transcription.
//    The transcript will appear in the terminal.
//
// ======================================================
// TROUBLESHOOTING
// ======================================================
//
// If you see "Module not found":
// → Run: npm install
//
// If you see "Cannot use import statement outside module":
// → Make sure you run: node transcribe-live.mjs
//
// If AWS credentials errors appear:
// → Verify environment variables are set correctly.
//
// ======================================================

import { spawn } from "child_process";
import {
  TranscribeStreamingClient,
  StartStreamTranscriptionCommand,
} from "@aws-sdk/client-transcribe-streaming";
import {
  BedrockRuntimeClient,
  ConverseCommand,
} from "@aws-sdk/client-bedrock-runtime";

const REGION = process.env.AWS_REGION || "us-east-1";

const LANGUAGE_CODE = "en-US";
const SAMPLE_RATE = 16000;
const BYTES_PER_SAMPLE = 2;
const CHANNELS = 1;
const CHUNK_MS = 100;

const CHUNK_SIZE = Math.floor(
  (CHUNK_MS / 1000) * SAMPLE_RATE * BYTES_PER_SAMPLE * CHANNELS
);

// Change if needed
const MICROPHONE_NAME = "Microphone (Realtek(R) Audio)";

// Bedrock model
const MODEL_ID = "amazon.nova-lite-v1:0";

// Backend from test.md
const BACKEND_BASE_URL = "http://localhost:8000";
const SEARCH_TOP_K = 5;

const transcribeClient = new TranscribeStreamingClient({
  region: REGION,
});

const bedrockClient = new BedrockRuntimeClient({
  region: REGION,
});

const ffmpeg = spawn(
  "ffmpeg",
  [
    "-hide_banner",
    "-loglevel",
    "error",
    "-f",
    "dshow",
    "-i",
    `audio=${MICROPHONE_NAME}`,
    "-ac",
    "1",
    "-ar",
    String(SAMPLE_RATE),
    "-f",
    "s16le",
    "-acodec",
    "pcm_s16le",
    "-",
  ],
  { stdio: ["ignore", "pipe", "inherit"] }
);

ffmpeg.on("error", (err) => {
  console.error("Failed to start ffmpeg:", err.message);
  process.exit(1);
});

async function* audioStream() {
  let buffer = Buffer.alloc(0);

  for await (const chunk of ffmpeg.stdout) {
    buffer = Buffer.concat([buffer, chunk]);

    while (buffer.length >= CHUNK_SIZE) {
      const audioChunk = buffer.subarray(0, CHUNK_SIZE);
      buffer = buffer.subarray(CHUNK_SIZE);

      yield {
        AudioEvent: {
          AudioChunk: audioChunk,
        },
      };
    }
  }
}

async function extractIssues(text) {
  const prompt = `
You analyze customer speech transcripts.

Return ONLY strict JSON in this exact format:
{"issues":["issue1","issue2"]}

Rules:
- Only explicit customer problems, complaints, or pain points.
- Keep each issue short and concrete.
- No explanation.
- Empty list if none.
- Do not infer aggressively.

Transcript:
${text}
`;

  const command = new ConverseCommand({
    modelId: MODEL_ID,
    messages: [
      {
        role: "user",
        content: [{ text: prompt }],
      },
    ],
    inferenceConfig: {
      maxTokens: 200,
      temperature: 0,
    },
  });

  const response = await bedrockClient.send(command);

  const output =
    response.output?.message?.content
      ?.map((x) => x.text || "")
      .join("")
      .trim() || "";

  try {
    const parsed = JSON.parse(output);
    return Array.isArray(parsed.issues)
      ? parsed.issues.map((x) => String(x).trim()).filter(Boolean)
      : [];
  } catch {
    console.log("Model output was not valid JSON:", output);
    return [];
  }
}

function normalizeSearchResults(data) {
  if (Array.isArray(data)) return data;
  if (Array.isArray(data.results)) return data.results;
  if (Array.isArray(data.hits)) return data.hits;
  if (Array.isArray(data.items)) return data.items;
  return [];
}

function printBackendResults(issue, results) {
  console.log(`\n[ELASTIC SEARCH] Issue query: ${issue}`);

  if (!results.length) {
    console.log("No backend matches found.\n");
    return;
  }

  results.forEach((item, idx) => {
    const title =
      item.title ||
      item.subject ||
      item.customer_id ||
      item.company_name ||
      "Untitled";

    const score =
      item.score ??
      item._score ??
      item.relevance_score ??
      "n/a";

    const snippet =
      item.highlight ||
      item.snippet ||
      item.raw_text ||
      item.text ||
      item.review_text ||
      "";

    console.log(`Result ${idx + 1}: ${title}`);
    console.log(`Score: ${score}`);
    if (snippet) {
      console.log(`Snippet: ${String(snippet).slice(0, 300)}`);
    }
    console.log("");
  });
}

async function searchCustomers(issue) {
  const url = new URL("/search/customers", BACKEND_BASE_URL);
  url.searchParams.set("q", issue);
  url.searchParams.set("top_k", String(SEARCH_TOP_K));

  const response = await fetch(url.toString(), {
    method: "GET",
    headers: {
      Accept: "application/json",
    },
  });

  if (!response.ok) {
    throw new Error(`Backend /search/customers failed: ${response.status}`);
  }

  const data = await response.json();
  return normalizeSearchResults(data);
}

// Optional richer query if you want AI backend output instead of plain search
async function querySupportAgent(question) {
  const response = await fetch(`${BACKEND_BASE_URL}/ai/query`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    body: JSON.stringify({
      question,
      mode: "support_agent",
      output_format: "text",
    }),
  });

  if (!response.ok) {
    throw new Error(`Backend /ai/query failed: ${response.status}`);
  }

  return response.json();
}

const seen = new Set();
let queue = Promise.resolve();

async function handleFinalTranscript(text) {
  console.log(`\nFinal: ${text}`);

  const issues = await extractIssues(text);

  if (!issues.length) {
    console.log("Issues: none\n");
    return;
  }

  for (const issue of issues) {
    const key = issue.toLowerCase();
    if (seen.has(key)) continue;

    seen.add(key);
    console.log(`🚨 ISSUE: ${issue}`);

    try {
      const results = await searchCustomers(issue);
      printBackendResults(issue, results);
    } catch (err) {
      console.error("Customer search failed:", err.message);
    }

    // Uncomment this block if you also want the backend AI summary
    /*
    try {
      const ai = await querySupportAgent(
        `Customer issue: ${issue}. Original transcript: ${text}`
      );
      console.log("[SUPPORT_AGENT OUTPUT]");
      console.log(JSON.stringify(ai, null, 2));
      console.log("");
    } catch (err) {
      console.error("AI query failed:", err.message);
    }
    */
  }
}

async function main() {
  console.log("Starting transcription...");
  console.log(`Backend: ${BACKEND_BASE_URL}`);
  console.log("Speak into microphone.\n");

  const command = new StartStreamTranscriptionCommand({
    LanguageCode: LANGUAGE_CODE,
    MediaEncoding: "pcm",
    MediaSampleRateHertz: SAMPLE_RATE,
    AudioStream: audioStream(),
    EnablePartialResultsStabilization: true,
    PartialResultsStability: "medium",
  });

  const response = await transcribeClient.send(command);

  for await (const event of response.TranscriptResultStream) {
    const results = event.TranscriptEvent?.Transcript?.Results || [];

    for (const result of results) {
      const text = result.Alternatives?.[0]?.Transcript?.trim() || "";
      if (!text) continue;

      if (result.IsPartial) {
        process.stdout.write(`\rPartial: ${text}      `);
      } else {
        process.stdout.write("\n");
        queue = queue.then(() => handleFinalTranscript(text));
      }
    }
  }
}

main().catch((err) => {
  console.error("\nFatal error:");
  console.error(err);
  process.exit(1);
});