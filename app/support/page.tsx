"use client";
import { useState } from 'react'

function Transcript() {
  return (
    <div className="card p-4">
      <div className="flex items-center justify-between">
        <div className="font-semibold">Live Transcription</div>
        <span className="pill bg-teal-50 text-teal-600">REAL-TIME</span>
      </div>
      <div className="mt-3 space-y-3 text-sm">
        <div>
          <div className="text-[11px] text-gray-500">CUSTOMER • 04:15</div>
          <div className="rounded-lg border bg-white p-3">I&apos;m seeing a double charge on my October statement. It looks like the subscription was billed twice on the 15th.</div>
        </div>
        <div>
          <div className="text-[11px] text-gray-500">AGENT (YOU) • 04:18</div>
          <div className="rounded-lg bg-brand-blue p-3 text-white">I&apos;m so sorry to hear that, Marcus. Let me look into your billing history immediately.</div>
        </div>
        <div>
          <div className="text-[11px] text-gray-500">CUSTOMER • 04:20</div>
          <div className="rounded-lg border bg-white p-3">Thank you. I also tried to update my payment method this morning but the website kept giving me an &apos;Error 502&apos; message. Is the system down?</div>
        </div>
      </div>
      <div className="mt-3 text-teal-600">AI is identifying customer intent: Billing Error + Technical Issue</div>
      <div className="mt-2 h-8 rounded bg-blue-50"></div>
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
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-6">
          <div className="font-semibold">ElasticCX Agent</div>
          <div className="flex items-center gap-4 text-sm">
            <button onClick={() => setTab('active')} className={tab==='active'?'border-b-2 border-brand-blue text-brand-blue':'text-gray-600'}>Active Call</button>
            <button onClick={() => setTab('queue')} className={tab==='queue'?'border-b-2 border-brand-blue text-brand-blue':'text-gray-600'}>Queue (4)</button>
            <button onClick={() => setTab('history')} className={tab==='history'?'border-b-2 border-brand-blue text-brand-blue':'text-gray-600'}>History</button>
            <button onClick={() => setTab('kb')} className={tab==='kb'?'border-b-2 border-brand-blue text-brand-blue':'text-gray-600'}>Knowledge Base</button>
          </div>
        </div>
        <div className="pill bg-green-50 text-green-600">AVAILABLE</div>
      </div>
      <div className="grid grid-cols-12 gap-6">
        <div className="col-span-5 space-y-4">
          <div className="card p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="font-medium">Marcus Sterling</div>
                <div className="text-xs text-gray-500">ID: #8829 • Premium Tier</div>
              </div>
              <div className="text-sm">04:22 DURATION</div>
            </div>
            <div className="mt-3 flex items-center gap-2">
              <button className="btn btn-outline px-3 py-1.5">Hold</button>
              <button className="btn btn-outline px-3 py-1.5">Transfer</button>
              <button className="btn btn-danger px-3 py-1.5">End</button>
            </div>
          </div>
          <Transcript />
        </div>
        <div className="col-span-7">
          <Suggestions />
        </div>
      </div>
      <div className="flex items-center justify-between border-t pt-3 text-xs">
        <div className="flex items-center gap-4">
          <span className="text-green-600">SYSTEM: OPERATIONAL</span>
          <span>LATENCY: 42MS</span>
          <span>MODEL: ELASTIC-V4-PRO</span>
          <span>ID: AG-4421-B</span>
        </div>
      </div>
    </div>
  )
}
