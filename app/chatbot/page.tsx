"use client";
import Link from 'next/link'
import { useState } from 'react'

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
          <div className="rounded-lg px-3 py-2 hover:bg-gray-100">Chat History</div>
          <div className="rounded-lg px-3 py-2 hover:bg-gray-100">Help Center</div>
          <div className="rounded-lg px-3 py-2 hover:bg-gray-100">Settings</div>
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
          <div className="flex items-center justify-between rounded border px-3 py-2">Pricing_Tier_2024.pdf<span>📄</span></div>
          <div className="flex items-center justify-between rounded border px-3 py-2">Enterprise_Security.pdf<span>📄</span></div>
        </div>
      </div>
    </aside>
  )
}

interface Message {
  role: 'user' | 'ai';
  content: string;
  citations?: string[];
  upsell?: string;
}

export default function ChatbotPage() {
  const [value, setValue] = useState('')
  const [messages, setMessages] = useState<Message[]>([
    { 
      role: 'user', 
      content: 'What features are included in the Enterprise plan for high-volume API access?' 
    },
    { 
      role: 'ai', 
      content: 'Based on our documentation, the Enterprise plan is specifically designed for high-scale operations. It includes:\n\n• Priority API access with guaranteed 99.99% uptime SLA\n• Unlimited seats and custom workspace permissions\n• Dedicated success manager and 24/7 technical support',
      citations: ['Pricing Doc', 'Enterprise SLA'],
      upsell: 'I noticed your current volume is averaging 450k requests/mo. Our Enterprise plan saves you 20% compared to your current Pay-As-You-Go pricing. Would you like to talk to a human specialist about transitioning?'
    }
  ])

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault()
    if (!value.trim()) return

    const userMessage: Message = { role: 'user', content: value }
    setMessages(prev => [...prev, userMessage])
    setValue('')

    // Mock AI response
    setTimeout(() => {
      const aiResponse: Message = {
        role: 'ai',
        content: "I've analyzed your request. Auralytics offers advanced scalability features that perfectly match your query. Is there anything specific about the implementation you'd like to dive into?",
        citations: ['Technical Specs v2']
      }
      setMessages(prev => [...prev, aiResponse])
    }, 1000)
  }

  return (
    <div className="flex gap-6 h-[calc(100vh-120px)]">
      <Sidebar />
      <section className="flex-1 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="text-lg font-semibold">Auralytics Support Bot</div>
            <span className="pill bg-green-50 text-green-600">AI Active</span>
            <span className="pill bg-blue-50 text-brand-blue">Fast Response</span>
          </div>
          <div className="flex items-center gap-3">
            <button className="btn btn-outline px-3 py-1.5">End Session</button>
            <div className="h-8 w-8 rounded-full bg-gray-200"></div>
          </div>
        </div>
        <div className="flex-1 overflow-y-auto space-y-4 pr-2">
          {messages.map((m, i) => (
            <div key={i} className={`mx-auto max-w-2xl ${m.role === 'user' ? 'flex justify-end' : ''}`}>
              {m.role === 'user' ? (
                <div className="max-w-xl rounded-2xl bg-brand-blue px-4 py-3 text-white shadow-sm">
                  {m.content}
                </div>
              ) : (
                <div className="space-y-2">
                  <div className="text-[11px] font-semibold tracking-wide text-gray-500">AURALYTICS INTELLIGENT RAG</div>
                  <div className="card mt-2 space-y-2 p-4 text-sm shadow-sm border-blue-100">
                    <div className="whitespace-pre-wrap">{m.content}</div>
                    {m.citations && (
                      <div className="mt-2 border-t pt-2">
                        <div className="text-[11px] font-semibold tracking-wide text-gray-500 uppercase">Citations</div>
                        <div className="mt-2 flex flex-wrap gap-2">
                          {m.citations.map((c, ci) => (
                            <Link key={ci} href="#" className="pill bg-blue-50 text-brand-blue hover:bg-blue-100 transition">Source: {c}</Link>
                          ))}
                        </div>
                      </div>
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
        </div>
        <form onSubmit={handleSend} className="sticky bottom-0 mt-6 border-t bg-gray-50 pt-3">
          <div className="mx-auto flex max-w-2xl items-center gap-2 rounded-full border bg-white px-3 py-2 shadow-sm focus-within:ring-2 focus-within:ring-blue-100 transition-all">
            <button type="button" className="text-xl hover:bg-gray-100 h-8 w-8 rounded-full transition">＋</button>
            <input 
              value={value} 
              onChange={e => setValue(e.target.value)} 
              placeholder="Type your message here..." 
              className="flex-1 outline-none bg-transparent py-1" 
            />
            <button type="button" className="text-xl hover:bg-gray-100 h-8 w-8 rounded-full transition">🎤</button>
            <button 
              type="submit"
              disabled={!value.trim()}
              className="grid h-9 w-9 place-items-center rounded-full bg-brand-blue text-white disabled:opacity-50 hover:opacity-90 transition active:scale-95"
            >
              ➤
            </button>
          </div>
          <div className="mt-1 text-center text-[10px] text-gray-500">Auralytics AI can make mistakes. Check important info.</div>
        </form>
      </section>
      <AccountContext />
    </div>
  )
}
