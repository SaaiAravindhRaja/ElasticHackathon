import { NextRequest, NextResponse } from 'next/server'

const KIBANA_URL =
  process.env.KIBANA_URL
const KIBANA_API_KEY =
  process.env.KIBANA_API_KEY
const AGENT_ID = process.env.ELASTIC_AGENT_ID ?? 'elasticx-support-agent'

export const runtime = 'nodejs'

export async function POST(req: NextRequest) {
  const body = await req.json()
  const { input, agent_id } = body

  let elasticRes: Response
  try {
    elasticRes = await fetch(`${KIBANA_URL}/api/agent_builder/converse`, {
      method: 'POST',
      headers: {
        Authorization: `ApiKey ${KIBANA_API_KEY}`,
        'kbn-xsrf': 'true',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        input,
        agent_id: agent_id ?? AGENT_ID,
      }),
    })
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err)
    return NextResponse.json({ error: 'Failed to reach Elastic', detail: message }, { status: 502 })
  }

  if (!elasticRes.ok) {
    const errText = await elasticRes.text()
    console.error('[converse] Elastic error:', elasticRes.status, errText)
    return NextResponse.json(
      { error: `Elastic agent returned ${elasticRes.status}`, detail: errText },
      { status: elasticRes.status }
    )
  }

  const contentType = elasticRes.headers.get('content-type') ?? ''

  // ── Streaming: Elastic returned SSE ─────────────────────────────────────────
  if (contentType.includes('text/event-stream') && elasticRes.body) {
    const upstream = elasticRes.body

    // Pass straight through to the browser
    return new Response(upstream, {
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache, no-transform',
        Connection: 'keep-alive',
        'X-Accel-Buffering': 'no',
      },
    })
  }

  // ── Non-streaming fallback: parse JSON and synthesise an SSE stream ─────────
  // This ensures the frontend always gets the same SSE protocol regardless of
  // whether Elastic supports streaming on this endpoint.
  const data = await elasticRes.json()
  const answer = extractAnswer(data)
  const citations = extractCitations(data)

  const encoder = new TextEncoder()
  const stream = new ReadableStream({
    start(controller) {
      // Emit the answer in small chunks to simulate streaming
      const words = answer.split(' ')
      let i = 0

      function push() {
        if (i < words.length) {
          const chunk = (i === 0 ? '' : ' ') + words[i]
          controller.enqueue(
            encoder.encode(`data: ${JSON.stringify({ token: chunk })}\n\n`)
          )
          i++
          setTimeout(push, 18) // ~55 tokens/s
        } else {
          // Send citations in a final event
          controller.enqueue(
            encoder.encode(
              `data: ${JSON.stringify({ done: true, citations })}\n\n`
            )
          )
          controller.close()
        }
      }
      push()
    },
  })

  return new Response(stream, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache, no-transform',
      Connection: 'keep-alive',
      'X-Accel-Buffering': 'no',
    },
  })
}

// ── Helpers ──────────────────────────────────────────────────────────────────

function extractAnswer(data: unknown): string {
  if (typeof data === 'string') return data
  if (Array.isArray(data)) return data.map(extractAnswer).join('\n')
  if (data && typeof data === 'object') {
    const d = data as Record<string, unknown>
    // Walk common field names, recursing on objects
    for (const key of ['output', 'answer', 'text', 'content', 'response', 'message', 'result']) {
      const val = d[key]
      if (typeof val === 'string' && val) return val
      if (val && typeof val === 'object') {
        const nested = extractAnswer(val)
        if (nested) return nested
      }
    }
    // Last resort: stringify
    return JSON.stringify(data)
  }
  return String(data ?? '')
}

function extractCitations(data: unknown): string[] {
  if (!data || typeof data !== 'object' || Array.isArray(data)) return []
  const d = data as Record<string, unknown>
  const raw =
    (d.citations as unknown[]) ||
    (d.references as unknown[]) ||
    (d.sources as unknown[]) ||
    (d.documents as unknown[]) ||
    []
  return raw.map((c) => {
    if (typeof c === 'string') return c
    if (c && typeof c === 'object') {
      const obj = c as Record<string, unknown>
      return (
        (obj.title as string) ||
        (obj.name as string) ||
        (obj.url as string) ||
        JSON.stringify(c)
      )
    }
    return String(c)
  })
}
