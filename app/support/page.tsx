"use client";
import { useState, useEffect, useRef } from 'react'

const API = 'http://localhost:8000'
const WS_URL = 'ws://localhost:3001'

interface TranscriptEntry {
  role: 'customer' | 'agent'
  time: string
  text: string
  isPartial?: boolean
}

interface Suggestion {
  solution: string
  steps: string[]
  confidence: number
  issue?: string
  searchResults?: any[]
}

export default function SupportAgent() {
  const [tab, setTab] = useState<'active' | 'queue' | 'history' | 'kb'>('active')
  const [input, setInput] = useState('')
  const [wsStatus, setWsStatus] = useState<'connecting' | 'connected' | 'disconnected'>('disconnected')
  const [suggestion, setSuggestion] = useState<Suggestion | null>(null)
  const [loadingSuggestion, setLoadingSuggestion] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)

  const [transcript, setTranscript] = useState<TranscriptEntry[]>([
    { role: 'customer', time: '04:15', text: "I'm seeing a double charge on my October statement. It looks like the subscription was billed twice on the 15th." },
    { role: 'agent', time: '04:18', text: "I'm so sorry to hear that, Marcus. Let me look into your billing history immediately." },
    { role: 'customer', time: '04:20', text: "Thank you. I also tried to update my payment method this morning but the website kept giving me an 'Error 502' message. Is the system down?" }
  ])

  // Connect to transcribe-live.mjs WebSocket server
  useEffect(() => {
    const connect = () => {
      setWsStatus('connecting')
      const ws = new WebSocket(WS_URL)
      wsRef.current = ws

      ws.onopen = () => setWsStatus('connected')

      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data)
          const now = new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })

          if (msg.type === 'partial') {
            setTranscript(prev => {
              const last = prev[prev.length - 1]
              if (last?.isPartial) {
                return [...prev.slice(0, -1), { role: 'customer', time: now, text: msg.text, isPartial: true }]
              }
              return [...prev, { role: 'customer', time: now, text: msg.text, isPartial: true }]
            })
          } else if (msg.type === 'final') {
            setTranscript(prev => {
              const filtered = prev.filter(e => !e.isPartial)
              return [...filtered, { role: 'customer', time: now, text: msg.text }]
            })
          } else if (msg.type === 'search_results') {
            setSuggestion(prev => ({
              solution: prev?.solution || `Customer issue detected: "${msg.issue}". Searching knowledge base...`,
              steps: prev?.steps || [],
              confidence: 90,
              issue: msg.issue,
              searchResults: msg.results,
            }))
          }
        } catch {}
      }

      ws.onclose = () => {
        setWsStatus('disconnected')
        // Try reconnect after 3s
        setTimeout(connect, 3000)
      }

      ws.onerror = () => ws.close()
    }

    connect()
    return () => { wsRef.current?.close() }
  }, [])

  const askAI = async () => {
    if (!input.trim()) return
    const q = input.trim()
    setInput('')
    setLoadingSuggestion(true)

    // Add to transcript as agent query
    setTranscript(prev => [...prev, {
      role: 'agent',
      time: new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }),
      text: `[AI Query] ${q}`
    }])

    try {
      const res = await fetch(`${API}/ai/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: q, mode: 'support_agent', output_format: 'json' }),
      })
      const data = await res.json()

      // Try to parse structured JSON from answer
      let parsed: any = {}
      try {
        parsed = typeof data.answer === 'string' ? JSON.parse(data.answer) : data.answer
      } catch {
        parsed = { suggested_response: data.answer, next_steps: [] }
      }

      setSuggestion({
        solution: parsed.suggested_response || parsed.answer || data.answer || 'See AI analysis above.',
        steps: Array.isArray(parsed.next_steps) ? parsed.next_steps : [],
        confidence: parsed.confidence_score ? Math.round(parsed.confidence_score * 100) : 92,
      })
    } catch {
      setSuggestion({ solution: 'Backend unavailable. Check localhost:8000.', steps: [], confidence: 0 })
    } finally {
      setLoadingSuggestion(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') askAI()
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-6">
          <div className="font-bold text-xl tracking-tight text-gray-900">Auralytics Agent</div>
          <div className="flex items-center gap-4 text-sm font-medium">
            {(['active', 'queue', 'history', 'kb'] as const).map(t => (
              <button key={t} onClick={() => setTab(t)}
                className={tab === t ? 'border-b-2 border-brand-blue text-brand-blue pb-1' : 'text-gray-500 hover:text-gray-700 transition'}>
                {t === 'active' ? 'Active Call' : t === 'queue' ? 'Queue (4)' : t === 'history' ? 'History' : 'Knowledge Base'}
              </button>
            ))}
          </div>
        </div>
        <div className="flex items-center gap-3">
          <div className="pill bg-green-50 text-green-600 font-bold border border-green-100 px-3">ONLINE</div>
          {wsStatus === 'connected' ? (
            <div className="pill bg-teal-50 text-teal-600 border border-teal-100">
              <span className="h-1.5 w-1.5 rounded-full bg-teal-500 inline-block mr-1 animate-pulse"></span>
              TRANSCRIPTION LIVE
            </div>
          ) : wsStatus === 'connecting' ? (
            <div className="pill bg-yellow-50 text-yellow-600">Connecting transcription...</div>
          ) : (
            <div className="pill bg-gray-100 text-gray-500">Transcription offline</div>
          )}
          <div className="h-9 w-9 rounded-full bg-blue-100 border-2 border-white shadow-sm overflow-hidden grid place-items-center font-bold text-brand-blue">AS</div>
        </div>
      </div>

      <div className="grid grid-cols-12 gap-6">
        <div className="col-span-12 lg:col-span-5 space-y-4">
          <div className="card p-4 shadow-sm border-blue-50">
            <div className="flex items-center justify-between">
              <div>
                <div className="font-bold text-lg text-gray-900">Marcus Sterling</div>
                <div className="text-xs font-medium text-gray-500">ID: #8829 • <span className="text-brand-blue">Premium Tier</span></div>
              </div>
              <div className="text-sm font-mono bg-gray-50 px-2 py-1 rounded">LIVE</div>
            </div>
            <div className="mt-4 flex items-center gap-2">
              <button className="btn btn-outline flex-1 py-1.5">Hold</button>
              <button className="btn btn-outline flex-1 py-1.5">Transfer</button>
              <button className="btn btn-danger flex-1 py-1.5">End Session</button>
            </div>
          </div>

          {/* Live Transcript */}
          <div className="card p-4 shadow-sm border-blue-50">
            <div className="flex items-center justify-between">
              <div className="font-semibold text-gray-800">Live Transcription</div>
              <span className={`pill ${wsStatus === 'connected' ? 'bg-teal-50 text-teal-600' : 'bg-gray-100 text-gray-500'} animate-pulse`}>
                ● {wsStatus === 'connected' ? 'REAL-TIME' : 'DEMO MODE'}
              </span>
            </div>
            <div className="mt-3 space-y-4 text-sm max-h-[350px] overflow-y-auto pr-2">
              {transcript.map((e, i) => (
                <div key={i} className={e.isPartial ? 'opacity-60' : ''}>
                  <div className={`text-[11px] font-bold ${e.role === 'customer' ? 'text-gray-500' : 'text-brand-blue'}`}>
                    {e.role.toUpperCase()} ({e.role === 'customer' ? 'MARCUS' : 'YOU'}) • {e.time}
                    {e.isPartial && ' (transcribing...)'}
                  </div>
                  <div className={`mt-1 rounded-xl p-3 shadow-sm border ${e.role === 'customer' ? 'bg-white border-gray-100' : 'bg-brand-blue text-white border-blue-600'}`}>
                    {e.text}
                  </div>
                </div>
              ))}
            </div>
            {wsStatus !== 'connected' && (
              <div className="mt-3 p-2 rounded-lg bg-yellow-50 text-yellow-700 text-xs text-center">
                Start <code className="font-mono">node transcribe-live.mjs</code> to enable live transcription
              </div>
            )}
          </div>
        </div>

        <div className="col-span-12 lg:col-span-7">
          <div className="card p-4 shadow-sm border-blue-50">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="h-6 w-6 grid place-items-center rounded bg-blue-100 text-brand-blue text-xs">AI</div>
                <div className="font-semibold">Smart Suggestions</div>
              </div>
              <div className={`pill font-bold ${loadingSuggestion ? 'bg-yellow-50 text-yellow-600' : 'bg-green-50 text-green-600'}`}>
                {loadingSuggestion ? 'ANALYZING...' : suggestion ? `${suggestion.confidence}% CONFIDENCE` : 'READY'}
              </div>
            </div>

            <div className="mt-3 rounded-xl border-2 border-blue-50 bg-blue-50/20 p-4 min-h-[120px]">
              {loadingSuggestion ? (
                <div className="flex items-center gap-2 text-gray-400 text-sm">
                  <div className="flex gap-1">
                    <span className="h-2 w-2 rounded-full bg-brand-blue animate-bounce" style={{ animationDelay: '0ms' }}></span>
                    <span className="h-2 w-2 rounded-full bg-brand-blue animate-bounce" style={{ animationDelay: '150ms' }}></span>
                    <span className="h-2 w-2 rounded-full bg-brand-blue animate-bounce" style={{ animationDelay: '300ms' }}></span>
                  </div>
                  Querying ElasticSearch + GPT-4o-mini...
                </div>
              ) : suggestion ? (
                <>
                  <div className="flex items-center justify-between border-b border-blue-50 pb-2 mb-2">
                    <div className="font-bold text-brand-blue text-sm uppercase tracking-wider">Recommended Solution</div>
                    <button className="text-xs font-bold text-brand-blue hover:underline">COPY</button>
                  </div>
                  {suggestion.issue && (
                    <div className="text-xs font-semibold text-gray-500 mb-2">
                      Issue detected: <span className="text-brand-blue">{suggestion.issue}</span>
                    </div>
                  )}
                  <div className="text-sm leading-relaxed text-gray-700 whitespace-pre-wrap">{suggestion.solution}</div>
                  {suggestion.steps.length > 0 && (
                    <div className="mt-3">
                      <div className="font-bold text-xs text-gray-400 uppercase tracking-widest mb-2">Next Steps</div>
                      <ol className="list-decimal pl-5 text-sm space-y-1 text-gray-600">
                        {suggestion.steps.map((step, i) => <li key={i}>{step}</li>)}
                      </ol>
                    </div>
                  )}
                  {suggestion.searchResults && suggestion.searchResults.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-blue-50">
                      <div className="text-xs font-semibold text-gray-400 uppercase mb-1">Related Cases from ES</div>
                      <div className="flex flex-wrap gap-1">
                        {suggestion.searchResults.map((r: any, i: number) => (
                          <span key={i} className="pill bg-gray-100 text-gray-600">
                            {r.title || r.customer_id || r.subject || 'Case'}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </>
              ) : (
                <div className="text-sm text-gray-400">
                  Type a question below to get AI-powered suggestions from ElasticSearch.
                  {wsStatus === 'connected' && ' Live transcription will auto-populate issues.'}
                </div>
              )}
            </div>

            <div className="mt-4 flex gap-2">
              <input
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask AI: 'How to handle duplicate billing charge?'"
                className="flex-1 rounded-xl border border-gray-200 px-4 py-2.5 text-sm focus:ring-2 focus:ring-blue-100 outline-none transition"
              />
              <button onClick={askAI} disabled={loadingSuggestion} className="btn btn-primary px-6 rounded-xl font-bold transition transform active:scale-95 disabled:opacity-60">
                {loadingSuggestion ? '...' : 'ASK AI'}
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="flex items-center justify-between border-t border-gray-100 pt-4 text-[10px] font-bold text-gray-400 tracking-widest uppercase">
        <div className="flex items-center gap-6">
          <span className="flex items-center gap-1.5"><span className="h-1.5 w-1.5 rounded-full bg-green-500"></span> SYSTEM: OPERATIONAL</span>
          <span>ES: SERVERLESS CLOUD</span>
          <span>AI: GPT-4O-MINI</span>
          <span>TRANSCRIPTION: AWS TRANSCRIBE + NOVA LITE</span>
        </div>
      </div>
    </div>
  )
}
