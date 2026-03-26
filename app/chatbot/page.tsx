"use client";
import Link from 'next/link'
import { useState, useRef, useEffect } from 'react'
import ReactMarkdown, { Components } from 'react-markdown'

const API = 'http://localhost:8000'

const MD: Components = {
  h1: ({ children }) => <h1 className="text-lg font-bold text-gray-900 mt-4 mb-1">{children}</h1>,
  h2: ({ children }) => <h2 className="text-base font-semibold text-gray-800 mt-4 mb-1">{children}</h2>,
  h3: ({ children }) => <h3 className="text-sm font-semibold text-gray-800 mt-3 mb-0.5">{children}</h3>,
  ul: ({ children }) => <ul className="list-disc list-outside pl-5 my-2 space-y-0.5">{children}</ul>,
  ol: ({ children }) => <ol className="list-decimal list-outside pl-5 my-2 space-y-0.5">{children}</ol>,
  li: ({ children }) => <li className="text-gray-700 leading-relaxed">{children}</li>,
  p: ({ children }) => <p className="text-gray-700 leading-relaxed my-1.5">{children}</p>,
  strong: ({ children }) => <strong className="font-semibold text-gray-900">{children}</strong>,
  em: ({ children }) => <em className="italic text-gray-700">{children}</em>,
  a: ({ href, children }) => <a href={href} className="text-brand-blue underline hover:opacity-80" target="_blank" rel="noopener noreferrer">{children}</a>,
  code: ({ children, className }) => {
    const isBlock = className?.includes('language-')
    return isBlock
      ? <code className="block bg-gray-100 text-gray-800 text-xs font-mono p-3 rounded-lg my-2 overflow-x-auto">{children}</code>
      : <code className="bg-gray-100 text-gray-800 text-xs font-mono px-1.5 py-0.5 rounded">{children}</code>
  },
  pre: ({ children }) => <pre className="my-2">{children}</pre>,
  blockquote: ({ children }) => <blockquote className="border-l-4 border-blue-200 pl-3 my-2 text-gray-600 italic">{children}</blockquote>,
  hr: () => <hr className="my-3 border-gray-200" />,
}

function Sidebar() {
  return (
    <aside className="w-60 shrink-0">
      <div className="sticky top-16">
        <div className="mb-4 flex items-center gap-2">
          <div className="h-8 w-8 rounded bg-brand-blue text-white grid place-items-center">⚡</div>
          <div>
            <div className="font-semibold">Auralytics</div>
            <div className="text-[11px] text-gray-500">AI Support Engine</div>
          </div>
        </div>
        <nav className="space-y-2">
          <div className="bg-blue-50 text-brand-blue rounded-lg px-3 py-2">Home</div>
          <div className="rounded-lg px-3 py-2 hover:bg-gray-100 cursor-pointer">Chat History</div>
          <div className="rounded-lg px-3 py-2 hover:bg-gray-100 cursor-pointer">Help Center</div>
          <div className="rounded-lg px-3 py-2 hover:bg-gray-100 cursor-pointer">Settings</div>
        </nav>
        <div className="mt-6">
          <button className="btn btn-primary w-full py-2">Speak to an Agent</button>
        </div>
      </div>
    </aside>
  )
}

function AccountContext() {
  return (
    <aside className="w-72 shrink-0 space-y-4">
      <div className="text-xs font-semibold text-gray-500">ACCOUNT CONTEXT</div>
      <div className="card p-4">
        <div className="text-sm text-gray-600">MONTHLY API VOLUME</div>
        <div className="mt-1 text-3xl font-bold">452k</div>
        <div className="text-xs text-green-600">+12% vs last mo</div>
        <div className="mt-2 h-2 w-full rounded bg-blue-100">
          <div className="h-2 w-3/4 rounded bg-brand-blue"></div>
        </div>
      </div>
      <div className="card p-4">
        <div className="text-sm text-gray-600">CURRENT PLAN</div>
        <div className="mt-1 font-medium">Pro Monthly</div>
        <button className="mt-3 btn btn-primary w-full py-2">Upgrade to Enterprise</button>
      </div>
      <div className="card p-4">
        <div className="text-sm text-gray-600">RELEVANT DOCS</div>
        <div className="mt-2 space-y-2 text-sm">
          <div className="flex items-center justify-between rounded border px-3 py-2">
            Pricing_Tier_2024.pdf<span>📄</span>
          </div>
          <div className="flex items-center justify-between rounded border px-3 py-2">
            Enterprise_Security.pdf<span>📄</span>
          </div>
        </div>
      </div>
    </aside>
  )
}

interface Source {
  title: string
  score?: number
}

interface Message {
  role: 'user' | 'ai'
  content: string
  citations?: Source[]
  upsell?: string
  loading?: boolean
  error?: boolean
}

export default function ChatbotPage() {
  const [value, setValue] = useState('')
  const [loading, setLoading] = useState(false)
  const [conversationId, setConversationId] = useState<string | null>(null)
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'ai',
      content: "Hi! I'm your Auralytics AI support assistant. I have access to Zendesk help documentation, company knowledge, and historical support data. How can I help you today?",
    }
  ])
  const bottomRef = useRef<HTMLDivElement>(null)
  const abortRef = useRef<AbortController | null>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault()
    const userMsg = value.trim()
    if (!userMsg || loading) return

    abortRef.current?.abort()
    const controller = new AbortController()
    abortRef.current = controller

    setValue('')
    setLoading(true)

    setMessages(prev => [
      ...prev,
      { role: 'user', content: userMsg },
      { role: 'ai', content: '', loading: true },
    ])

    try {
      const res = await fetch(`${API}/ai/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: userMsg,
          mode: 'support_bot',
          ...(conversationId ? { conversation_id: conversationId } : {}),
        }),
        signal: controller.signal,
      })

      if (!res.ok) throw new Error(`API error ${res.status}`)
      const data = await res.json()

      if (data.conversation_id) setConversationId(data.conversation_id)

      const sources: Source[] = (data.sources || []).map((s: any) => ({
        title: s.title || s.doc_type || 'Source',
        score: s.score,
      }))

      setMessages(prev => [
        ...prev.slice(0, -1),
        {
          role: 'ai',
          content: data.answer || 'No answer returned.',
          citations: sources,
        },
      ])
    } catch (err) {
      if ((err as { name?: string }).name === 'AbortError') return
      setMessages(prev => [
        ...prev.slice(0, -1),
        {
          role: 'ai',
          content: "Sorry, I couldn't reach the backend. Please check that the server is running on localhost:8000.",
          error: true,
        },
      ])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex gap-6 h-[calc(100vh-120px)]">
      <Sidebar />

      <section className="flex-1 flex flex-col space-y-4 min-h-0">
        {/* Header */}
        <div className="flex items-center justify-between shrink-0">
          <div className="flex items-center gap-3">
            <div className="text-lg font-semibold">Auralytics Support Bot</div>
            <span className="pill bg-green-50 text-green-600">AI Active</span>
            <span className="pill bg-blue-50 text-brand-blue">ElasticSearch RAG</span>
            {conversationId && (
              <span className="pill bg-purple-50 text-purple-600">Multi-Turn</span>
            )}
          </div>
          <div className="flex items-center gap-3">
            <button
              className="btn btn-outline px-3 py-1.5"
              onClick={() => { setMessages([{ role: 'ai', content: 'Session reset. How can I help you?' }]); setConversationId(null) }}
            >
              New Session
            </button>
            <div className="h-8 w-8 rounded-full bg-gray-200"></div>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto space-y-4 pr-2">
          {messages.map((m, i) => (
            <div
              key={i}
              className={`mx-auto max-w-2xl ${m.role === 'user' ? 'flex justify-end' : ''}`}
            >
              {m.role === 'user' ? (
                <div className="max-w-xl rounded-2xl bg-brand-blue px-4 py-3 text-white shadow-sm">
                  {m.content}
                </div>
              ) : (
                <div className="space-y-2">
                  <div className="text-[11px] font-semibold tracking-wide text-gray-500">
                    AURALYTICS INTELLIGENT RAG
                  </div>
                  <div className={`card mt-2 space-y-2 p-4 text-sm shadow-sm ${m.error ? 'border-red-200 bg-red-50' : 'border-blue-100'}`}>
                    {m.loading ? (
                      <div className="flex items-center gap-2 text-gray-400">
                        <div className="flex gap-1">
                          <span className="h-2 w-2 rounded-full bg-brand-blue animate-bounce opacity-60" style={{ animationDelay: '0ms' }}></span>
                          <span className="h-2 w-2 rounded-full bg-brand-blue animate-bounce opacity-60" style={{ animationDelay: '150ms' }}></span>
                          <span className="h-2 w-2 rounded-full bg-brand-blue animate-bounce opacity-60" style={{ animationDelay: '300ms' }}></span>
                        </div>
                        <span className="text-xs">Searching knowledge base...</span>
                      </div>
                    ) : (
                      <>
                        <div className="text-sm text-gray-700">
                          <ReactMarkdown components={MD}>{m.content}</ReactMarkdown>
                        </div>
                        {m.citations && m.citations.length > 0 && (
                          <div className="mt-2 border-t pt-2">
                            <div className="text-[11px] font-semibold tracking-wide text-gray-500 uppercase">Sources</div>
                            <div className="mt-2 flex flex-wrap gap-2">
                              {m.citations.map((c, ci) => (
                                <span key={ci} className="pill bg-blue-50 text-brand-blue">
                                  📄 {c.title}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                      </>
                    )}
                  </div>
                  {m.upsell && (
                    <div className="mt-3 rounded-xl bg-blue-50 p-4 text-sm border border-blue-100">
                      <div>{m.upsell}</div>
                      <div className="mt-3 flex gap-2">
                        <button className="btn btn-primary px-4 py-2">Talk to an Agent</button>
                        <button className="btn btn-outline px-4 py-2 bg-white">Not now</button>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
          <div ref={bottomRef} />
        </div>

        {/* Input */}
        <form onSubmit={handleSend} className="sticky bottom-0 shrink-0 border-t bg-gray-50 pt-3">
          <div className="mx-auto flex max-w-2xl items-center gap-2 rounded-full border bg-white px-3 py-2 shadow-sm focus-within:ring-2 focus-within:ring-blue-100 transition-all">
            <button type="button" className="text-xl hover:bg-gray-100 h-8 w-8 rounded-full transition">
              ＋
            </button>
            <input
              value={value}
              onChange={e => setValue(e.target.value)}
              onKeyDown={e => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault()
                  handleSend(e)
                }
              }}
              placeholder="Ask anything — e.g. 'How do I reset my password?'"
              className="flex-1 outline-none bg-transparent py-1"
              disabled={loading}
            />
            <button
              type="submit"
              disabled={!value.trim() || loading}
              className="grid h-9 w-9 place-items-center rounded-full bg-brand-blue text-white disabled:opacity-50 hover:opacity-90 transition active:scale-95"
            >
              {loading ? (
                <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
                </svg>
              ) : (
                '➤'
              )}
            </button>
          </div>
          <div className="mt-1 text-center text-[10px] text-gray-500">
            Powered by ElasticSearch RRF hybrid search · {conversationId ? `Session: ${conversationId.slice(0, 8)}...` : 'New session'}
          </div>
        </form>
      </section>

      <AccountContext />
    </div>
  )
}
