#!/usr/bin/env node
// Sends a coding prompt to DeepSeek v4 Flash via OpenRouter and prints the response to stdout.
//
// Usage:
//   node scripts/ask-deepseek.js "prompt text"
//   echo "prompt text" | node scripts/ask-deepseek.js
//
// API key resolution order:
//   1. OPENROUTER_API_KEY env var
//   2. Bitwarden item "OpenRouter — API Key" (requires BW_SESSION or ~/bin/bw-unlock)

const { execSync } = require('child_process');

const MODEL = 'deepseek/deepseek-v4-flash';
const API_URL = 'https://openrouter.ai/api/v1/chat/completions';

function getApiKey() {
  if (process.env.OPENROUTER_API_KEY) return process.env.OPENROUTER_API_KEY;

  let session = process.env.BW_SESSION;
  if (!session) {
    session = execSync('~/bin/bw-unlock', { shell: '/bin/zsh' }).toString().trim();
  }
  const key = execSync(
    `bw get password "OpenRouter — API Key" --session "${session}"`,
    { shell: '/bin/zsh' }
  ).toString().trim();
  if (!key) throw new Error('Could not resolve OpenRouter API key from Bitwarden.');
  return key;
}

function readStdin() {
  return new Promise((resolve) => {
    if (process.stdin.isTTY) return resolve('');
    let data = '';
    process.stdin.setEncoding('utf8');
    process.stdin.on('data', (chunk) => (data += chunk));
    process.stdin.on('end', () => resolve(data));
  });
}

async function main() {
  const argPrompt = process.argv.slice(2).join(' ');
  const stdinPrompt = await readStdin();
  const prompt = argPrompt || stdinPrompt;

  if (!prompt.trim()) {
    console.error('Usage: node scripts/ask-deepseek.js "prompt" (or pipe prompt via stdin)');
    process.exit(1);
  }

  const apiKey = getApiKey();

  const res = await fetch(API_URL, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${apiKey}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      model: MODEL,
      messages: [{ role: 'user', content: prompt }],
    }),
  });

  if (!res.ok) {
    const body = await res.text();
    console.error(`OpenRouter request failed (${res.status}): ${body}`);
    process.exit(1);
  }

  const data = await res.json();
  const content = data.choices?.[0]?.message?.content;
  if (!content) {
    console.error('No content in response: ' + JSON.stringify(data));
    process.exit(1);
  }
  console.log(content);
}

main().catch((err) => {
  console.error(err.message || err);
  process.exit(1);
});
