"use client";
import { useState } from 'react'

function AssistCard() {
  return (
    <div className="space-y-4">
      <div className="rounded-xl border border-red-200 bg-red-50 p-0 shadow">
        <div className="flex items-center justify-between rounded-t-xl bg-brand-red px-4 py-2 text-white text-sm">
          <div>COMPETITOR ALERT: COMPETITOR X</div>
          <div className="pill bg-white/20 text-white">MATCH DETECTED</div>
        </div>
        <div className="space-y-3 p-4">
          <div className="font-semibold">Known Weakness: Analytics Stability</div>
          <div className="text-yellow-500 text-xs">★★★★★</div>
          <div className="italic text-sm text-gray-700">Recent Trustpilot reviews cite 40% increase in buggy analytics and dashboard timeouts since v4.2 release.</div>
          <div className="border-t pt-3 text-[11px] font-semibold tracking-wide text-gray-500">KILLER QUESTION TO DROP:</div>
          <div className="rounded-lg bg-blue-50 p-3 text-sm">When the board asks for verified attribution next week, how confident are you that the current system&apos;s buggy reports won&apos;t cause another delay?</div>
        </div>
      </div>
      <div className="card p-4">
        <div className="flex items-center gap-2">
          <div className="h-6 w-6 grid place-items-center rounded bg-blue-100 text-brand-blue">★</div>
          <div className="font-semibold">ACTIVE OBJECTION: STABILITY CONCERNS</div>
        </div>
        <div className="mt-3 flex flex-wrap gap-2">
          <span className="pill bg-blue-50 text-brand-blue">OUR COUNTER-POINT</span>
          <span className="text-sm">99.99% Uptime SLA with real-time data validation engines.</span>
        </div>
        <div className="mt-2 flex flex-wrap gap-2">
          <span className="pill bg-green-50 text-green-600">VALUE PROP</span>
          <span className="text-sm">Set it and forget it reporting for executive boards.</span>
        </div>
        <div className="mt-3 text-[11px] font-semibold tracking-wide text-gray-500">TALKING POINTS</div>
        <ul className="mt-1 list-disc pl-5 text-sm">
          <li>ElasticCX uses Eventual Consistency Protection to ensure reports never show buggy partial data.</li>
          <li>We offer a White-Glove Migration that ports over 2 years of Competitor X data in 48 hours.</li>
        </ul>
      </div>
      <div className="card flex items-center justify-between p-4">
        <div>
          <div className="font-medium">Reporting Pro Feature</div>
          <div className="text-sm text-gray-600">Auto-syncs with HubSpot/Salesforce daily.</div>
        </div>
        <button className="btn btn-outline px-3 py-1.5">View Specs</button>
      </div>
    </div>
  )
}

export default function SalesAssistant() {
  const [input, setInput] = useState('')
  return (
    <div className="grid grid-cols-12 gap-6">
      <section className="col-span-7">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="font-semibold">ElasticCX Co-Pilot</div>
            <span className="pill bg-green-50 text-green-600">Live Call: Sarah Jenkins</span>
            <div className="text-xs text-gray-500">DIRECTOR OF OPS • TECHFLOW</div>
          </div>
          <div className="flex items-center gap-2">
            <div className="font-mono">12:44</div>
            <button className="btn btn-outline px-3 py-1.5">Pause</button>
            <button className="btn btn-danger px-3 py-1.5">End Call</button>
            <div className="h-8 w-8 rounded-full bg-gray-200"></div>
          </div>
        </div>
        <div className="mt-4">
          <div className="text-[11px] font-semibold tracking-widest text-gray-500">WHISPER LIVE TRANSCRIPTION <span className="pill bg-green-50 text-green-600 ml-2">LOW LATENCY</span></div>
          <div className="mt-3 space-y-3">
            <div className="flex items-start gap-3">
              <div className="h-8 w-8 rounded-full bg-gray-200"></div>
              <div>
                <div className="text-sm font-semibold">Sarah Jenkins <span className="text-xs text-gray-400">10:42 AM</span></div>
                <div className="mt-1 rounded-2xl bg-white p-3 text-sm text-gray-700 shadow border">We&apos;ve been using Competitor X for the last two years, but honestly, their analytics dashboard has been extremely buggy since the last update. It&apos;s making our quarterly reporting a nightmare.</div>
              </div>
            </div>
            <div className="ml-14">
              <div className="inline-block rounded-2xl bg-brand-blue p-3 text-sm text-white shadow">I hear that a lot. Reliability in reporting is the foundation of making good business decisions. When the data is buggy, it&apos;s not just a technical issue, it&apos;s a trust issue. How has that specifically impacted your team&apos;s workflow this month?</div>
            </div>
            <div className="flex items-start gap-3 opacity-70">
              <div className="h-8 w-8 rounded-full bg-gray-200"></div>
              <div>
                <div className="text-sm">Sarah Jenkins <span className="text-xs text-gray-400">Transcribing…</span></div>
                <div className="mt-1 rounded-2xl border border-dashed p-3 text-sm text-gray-500">Well, we actually had to delay the board meeting because we couldn&apos;t verify the conversion numbers...</div>
              </div>
            </div>
          </div>
          <div className="mt-4 flex items-center justify-between">
            <div className="flex items-center gap-2 text-sm">
              <span className="text-gray-500">AI Suggested Next Question:</span>
              <div className="flex gap-2">
                <button className="rounded-full border px-3 py-1 text-gray-700">What&apos;s the cost of that delay?</button>
                <button className="rounded-full border px-3 py-1 text-gray-700">Who else is affected by this?</button>
              </div>
            </div>
            <div className="flex items-center gap-6 text-xs">
              <div className="flex items-center gap-2">
                <div className="h-2 w-28 rounded bg-green-100">
                  <div className="h-2 w-3/4 rounded bg-green-500"></div>
                </div>
                <div>75% Positive</div>
              </div>
              <div>Agent 40% / Sarah 60%</div>
              <div className="text-gray-500">Sales Manager Marcus is monitoring</div>
            </div>
          </div>
          <div className="mt-4 flex items-center gap-2">
            <input value={input} onChange={e => setInput(e.target.value)} placeholder="Type to coach..." className="flex-1 rounded-lg border px-3 py-2" />
            <button className="btn btn-primary px-3 py-2">Send</button>
          </div>
        </div>
      </section>
      <section className="col-span-5">
        <AssistCard />
      </section>
    </div>
  )
}
