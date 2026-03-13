"use client";
import { useState } from 'react'

function Transcript({ entries }: { entries: any[] }) {
  return (
    <div className="card p-4 shadow-sm border-blue-50">
      <div className="flex items-center justify-between">
        <div className="font-semibold text-gray-800">Live Transcription</div>
        <span className="pill bg-teal-50 text-teal-600 animate-pulse">● REAL-TIME</span>
      </div>
      <div className="mt-3 space-y-4 text-sm max-h-[400px] overflow-y-auto pr-2">
        {entries.map((e, i) => (
          <div key={i} className="animate-in fade-in slide-in-from-bottom-2 duration-300">
            <div className={`text-[11px] font-bold ${e.role === 'customer' ? 'text-gray-500' : 'text-brand-blue'}`}>
              {e.role.toUpperCase()} ({e.role === 'customer' ? 'MARCUS' : 'YOU'}) • {e.time}
            </div>
            <div className={`mt-1 rounded-xl p-3 shadow-sm border ${e.role === 'customer' ? 'bg-white border-gray-100' : 'bg-brand-blue text-white border-blue-600'}`}>
              {e.text}
            </div>
          </div>
        ))}
      </div>
      <div className="mt-4 p-3 rounded-lg bg-teal-50/50 border border-teal-100 text-teal-700 text-xs flex items-center gap-2">
        <span className="h-2 w-2 rounded-full bg-teal-500 animate-pulse"></span>
        AI is identifying customer intent: <span className="font-bold">Billing Error + Technical Issue</span>
      </div>
    </div>
  )
}

function Suggestions() {
  return (
    <div className="space-y-4">
      <div className="card p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="h-6 w-6 grid place-items-center rounded bg-blue-100 text-brand-blue">⚙️</div>
            <div className="font-semibold">Smart Suggestions</div>
          </div>
          <div className="pill bg-green-50 text-green-600">CONFIDENCE: 98%</div>
        </div>
        <div className="mt-3 rounded-lg border p-3">
          <div className="flex items-center justify-between">
            <div className="font-medium">Recommended Solution</div>
            <button className="text-sm text-brand-blue">Copy to Clipboard</button>
          </div>
          <div className="mt-2 text-sm">
            <div className="font-medium">Issue: Duplicate Subscription Charge + Gateway Error 502</div>
            <p className="mt-1">I&apos;ve identified the duplicate charge on October 15th. It seems a temporary gateway timeout caused the system to retry. I&apos;ve already initiated a refund for the second transaction which should appear in 3–5 business days. Regarding the 502 error, we&apos;re currently performing a brief maintenance update on our payment portal which should be completed in 15 minutes.</p>
          </div>
        </div>
        <div className="mt-3 rounded-lg border p-3">
          <div className="font-medium">Step-by-Step Action Plan</div>
          <ol className="mt-2 list-decimal pl-5 text-sm space-y-1">
            <li>Confirm transaction IDs: <span className="font-mono">TXN-4992</span> and <span className="font-mono">TXN-4993</span>.</li>
            <li>Click &apos;Void/Refund&apos; on the second transaction in the Billing Tab.</li>
            <li>Send Standard Refund Confirmation email template.</li>
          </ol>
        </div>
        <div className="mt-3 rounded-lg border p-3">
          <div className="font-medium">Referenced Internal Documents</div>
          <div className="mt-2 flex flex-wrap gap-2">
            <button className="pill bg-gray-100 text-gray-700">Refund Policy (SOP-B04)</button>
            <button className="pill bg-gray-100 text-gray-700">Gateway Status Dashboard</button>
          </div>
        </div>
        <div className="mt-3 flex gap-2">
          <input placeholder="Ask AI for further clarification..." className="flex-1 rounded-lg border px-3 py-2" />
          <button className="btn btn-primary px-4 py-2">Resolve Case</button>
        </div>
      </div>
    </div>
  )
}

export default function SupportAgent() {
  const [tab, setTab] = useState<'active' | 'queue' | 'history' | 'kb'>('active')
  const [input, setInput] = useState('')
  const [transcript, setTranscript] = useState([
    { role: 'customer', time: '04:15', text: "I'm seeing a double charge on my October statement. It looks like the subscription was billed twice on the 15th." },
    { role: 'agent', time: '04:18', text: "I'm so sorry to hear that, Marcus. Let me look into your billing history immediately." },
    { role: 'customer', time: '04:20', text: "Thank you. I also tried to update my payment method this morning but the website kept giving me an 'Error 502' message. Is the system down?" }
  ])

  const handleAction = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && input.trim()) {
      setTranscript(prev => [...prev, { role: 'agent', time: '04:22', text: input }])
      setInput('')
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-6">
          <div className="font-bold text-xl tracking-tight text-gray-900">Auralytics Agent</div>
          <div className="flex items-center gap-4 text-sm font-medium">
            <button onClick={() => setTab('active')} className={tab==='active'?'border-b-2 border-brand-blue text-brand-blue pb-1':'text-gray-500 hover:text-gray-700 transition'}>Active Call</button>
            <button onClick={() => setTab('queue')} className={tab==='queue'?'border-b-2 border-brand-blue text-brand-blue pb-1':'text-gray-500 hover:text-gray-700 transition'}>Queue (4)</button>
            <button onClick={() => setTab('history')} className={tab==='history'?'border-b-2 border-brand-blue text-brand-blue pb-1':'text-gray-500 hover:text-gray-700 transition'}>History</button>
            <button onClick={() => setTab('kb')} className={tab==='kb'?'border-b-2 border-brand-blue text-brand-blue pb-1':'text-gray-500 hover:text-gray-700 transition'}>Knowledge Base</button>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <div className="pill bg-green-50 text-green-600 font-bold border border-green-100 px-3">ONLINE</div>
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
              <div className="text-sm font-mono bg-gray-50 px-2 py-1 rounded">04:22</div>
            </div>
            <div className="mt-4 flex items-center gap-2">
              <button className="btn btn-outline flex-1 py-1.5 hover:bg-gray-50 transition">Hold</button>
              <button className="btn btn-outline flex-1 py-1.5 hover:bg-gray-50 transition">Transfer</button>
              <button className="btn btn-danger flex-1 py-1.5 hover:bg-red-600 transition">End Session</button>
            </div>
          </div>
          <Transcript entries={transcript} />
        </div>
        <div className="col-span-12 lg:col-span-7">
          <div className="card p-4 shadow-sm border-blue-50">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="h-6 w-6 grid place-items-center rounded bg-blue-100 text-brand-blue text-xs">AI</div>
                <div className="font-semibold">Smart Suggestions</div>
              </div>
              <div className="pill bg-green-50 text-green-600 font-bold">98% CONFIDENCE</div>
            </div>
            <div className="mt-3 rounded-xl border-2 border-blue-50 bg-blue-50/20 p-4">
              <div className="flex items-center justify-between border-b border-blue-50 pb-2 mb-2">
                <div className="font-bold text-brand-blue text-sm uppercase tracking-wider">Recommended Solution</div>
                <button className="text-xs font-bold text-brand-blue hover:underline">COPY RESPONSE</button>
              </div>
              <div className="text-sm leading-relaxed text-gray-700">
                <div className="font-bold text-gray-900 mb-1">Issue: Duplicate Subscription Charge + Gateway Error 502</div>
                <p>I&apos;ve identified the duplicate charge on October 15th. It seems a temporary gateway timeout caused the system to retry. I&apos;ve already initiated a refund for the second transaction which should appear in 3–5 business days. Regarding the 502 error, we&apos;re currently performing a brief maintenance update on our payment portal which should be completed in 15 minutes.</p>
              </div>
            </div>
            <div className="mt-4 space-y-3">
              <div className="font-bold text-xs text-gray-400 uppercase tracking-widest">Next Actions</div>
              <ol className="list-decimal pl-5 text-sm space-y-2 text-gray-600">
                <li>Confirm transaction IDs: <span className="font-mono bg-gray-100 px-1 rounded">TXN-4992</span> and <span className="font-mono bg-gray-100 px-1 rounded">TXN-4993</span>.</li>
                <li>In Billing Tab, click <span className="font-bold text-gray-900">&apos;Void/Refund&apos;</span> on the second transaction.</li>
                <li>Send <span className="text-brand-blue underline">Standard Refund Confirmation</span> email template.</li>
              </ol>
            </div>
            <div className="mt-5 flex gap-2">
              <input 
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={handleAction}
                placeholder="Type your response or ask AI..." 
                className="flex-1 rounded-xl border border-gray-200 px-4 py-2.5 text-sm focus:ring-2 focus:ring-blue-100 outline-none transition" 
              />
              <button onClick={() => { if(input.trim()) setTranscript(prev => [...prev, {role:'agent', time:'now', text:input}]); setInput('') }} className="btn btn-primary px-6 rounded-xl font-bold transition transform active:scale-95">SEND</button>
            </div>
          </div>
        </div>
      </div>
      <div className="flex items-center justify-between border-t border-gray-100 pt-4 text-[10px] font-bold text-gray-400 tracking-widest uppercase">
        <div className="flex items-center gap-6">
          <span className="flex items-center gap-1.5"><span className="h-1.5 w-1.5 rounded-full bg-green-500"></span> SYSTEM: OPERATIONAL</span>
          <span>LATENCY: 42MS</span>
          <span>MODEL: AURALYTICS-V1-ULTRA</span>
          <span>ID: AG-4421-B</span>
        </div>
      </div>
    </div>
  )
}
