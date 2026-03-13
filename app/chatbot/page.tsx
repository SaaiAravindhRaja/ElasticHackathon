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
            <div className="font-semibold">ElasticCX</div>
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

export default function ChatbotPage() {
  const [value, setValue] = useState('')
  return (
    <div className="flex gap-6">
      <Sidebar />
      <section className="flex-1 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="text-lg font-semibold">ElasticCX Support Bot</div>
            <span className="pill bg-green-50 text-green-600">AI Active</span>
            <span className="pill bg-blue-50 text-brand-blue">Fast Response</span>
          </div>
          <div className="flex items-center gap-3">
            <button className="btn btn-outline px-3 py-1.5">End Session</button>
            <div className="h-8 w-8 rounded-full bg-gray-200"></div>
          </div>
        </div>
        <div className="space-y-3">
          <div className="mx-auto max-w-2xl">
            <div className="mx-auto max-w-xl rounded-2xl bg-brand-blue px-4 py-3 text-white">
              What features are included in the Enterprise plan for high-volume API access?
            </div>
          </div>
          <div className="mx-auto max-w-2xl">
            <div className="text-[11px] font-semibold tracking-wide text-gray-500">ELASTICCX INTELLIGENT RAG</div>
            <div className="card mt-2 space-y-2 p-4 text-sm">
              <div>Based on our documentation, the Enterprise plan is specifically designed for high-scale operations. It includes:</div>
              <ul className="list-disc pl-5">
                <li>Priority API access with guaranteed 99.99% uptime SLA</li>
                <li>Unlimited seats and custom workspace permissions</li>
                <li>Dedicated success manager and 24/7 technical support</li>
              </ul>
              <div className="mt-2 border-t pt-2">
                <div className="text-[11px] font-semibold tracking-wide text-gray-500">CITATIONS</div>
                <div className="mt-2 flex flex-wrap gap-2">
                  <Link href="#" className="pill bg-blue-50 text-brand-blue">Source: Pricing Doc</Link>
                  <Link href="#" className="pill bg-blue-50 text-brand-blue">Source: Enterprise SLA</Link>
                </div>
              </div>
            </div>
            <div className="mt-3 rounded-xl bg-blue-50 p-4 text-sm">
              <div>I noticed your current volume is averaging 450k requests/mo. Our Enterprise plan saves you 20% compared to your current Pay-As-You-Go pricing. Would you like to talk to a human specialist about transitioning?</div>
              <div className="mt-3 flex gap-2">
                <button className="btn btn-primary px-4 py-2">Talk to an Agent</button>
                <button className="btn btn-outline px-4 py-2">Not now</button>
              </div>
            </div>
          </div>
        </div>
        <div className="sticky bottom-0 mt-6 border-t bg-gray-50 pt-3">
          <div className="mx-auto flex max-w-2xl items-center gap-2 rounded-full border bg-white px-3 py-2">
            <button className="text-xl">＋</button>
            <input value={value} onChange={e => setValue(e.target.value)} placeholder="Type your message here..." className="flex-1 outline-none" />
            <button className="text-xl">🎤</button>
            <button className="grid h-9 w-9 place-items-center rounded-full bg-brand-blue text-white">➤</button>
          </div>
          <div className="mt-1 text-center text-[10px] text-gray-500">ElasticCX AI can make mistakes. Check important info.</div>
        </div>
      </section>
      <AccountContext />
    </div>
  )
}
