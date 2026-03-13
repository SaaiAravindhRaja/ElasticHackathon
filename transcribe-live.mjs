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

// CHANGE THIS if your mic name is different
const MICROPHONE_NAME = "Microphone (Realtek(R) Audio)";

// Nova Lite model
const MODEL_ID = "amazon.nova-lite-v1:0";

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

Return ONLY JSON:

{"issues":["issue1","issue2"]}

Rules:
- Only explicit problems or complaints
- No explanation
- Empty list if none

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
    return parsed.issues || [];
  } catch {
    console.log("Model output:", output);
    return [];
  }
}

const seen = new Set();
let queue = Promise.resolve();

async function handleFinalTranscript(text) {
  console.log(`\nFinal: ${text}`);

  const issues = await extractIssues(text);

  if (!issues.length) return;

  for (const issue of issues) {
    const key = issue.toLowerCase();
    if (seen.has(key)) continue;

    seen.add(key);
    console.log(`🚨 ISSUE: ${issue}`);
  }
}

async function main() {
  console.log("Starting transcription...");
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
      const text = result.Alternatives?.[0]?.Transcript || "";
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

main();