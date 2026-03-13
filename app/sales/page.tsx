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
          <li>Auralytics uses Eventual Consistency Protection to ensure reports never show buggy partial data.</li>
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
  const [transcript, setTranscript] = useState([
    { role: 'customer', name: 'Sarah Jenkins', time: '10:42 AM', text: "We've been using Competitor X for the last two years, but honestly, their analytics dashboard has been extremely buggy since the last update. It's making our quarterly reporting a nightmare." },
    { role: 'agent', name: 'You', time: '10:43 AM', text: "I hear that a lot. Reliability in reporting is the foundation of making good business decisions. When the data is buggy, it's not just a technical issue, it's a trust issue. How has that specifically impacted your team's workflow this month?" }
  ])

  const handleSend = () => {
    if (!input.trim()) return
    setTranscript(prev => [...prev, { role: 'agent', name: 'You', time: '10:44 AM', text: input }])
    setInput('')
  }

  return (
    <div className="grid grid-cols-12 gap-6">
      <section className="col-span-12 lg:col-span-7">
        <div className="flex items-center justify-between bg-white p-4 rounded-xl shadow-sm border border-gray-100">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-full bg-blue-100 grid place-items-center text-brand-blue font-bold">SJ</div>
            <div>
              <div className="flex items-center gap-2">
                <div className="font-bold text-gray-900 text-lg">Auralytics Co-Pilot</div>
                <span className="pill bg-green-50 text-green-600 animate-pulse border border-green-100 text-[10px] font-bold">LIVE CALL</span>
              </div>
              <div className="text-xs font-medium text-gray-500 uppercase tracking-wider">Sarah Jenkins • Director of Ops • TechFlow</div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <div className="font-mono bg-gray-900 text-white px-3 py-1 rounded text-sm font-bold tracking-tighter">12:44</div>
            <button className="btn btn-outline h-9 w-9 grid place-items-center rounded-lg">⏸</button>
            <button className="btn btn-danger px-4 py-1.5 rounded-lg text-sm font-bold">END CALL</button>
          </div>
        </div>
        <div className="mt-6 bg-white p-6 rounded-2xl shadow-sm border border-gray-100 min-h-[500px] flex flex-col">
          <div className="flex items-center justify-between mb-6 border-b pb-4">
            <div className="text-[11px] font-bold tracking-widest text-gray-400 uppercase">Live Call Intelligence</div>
            <div className="flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-green-500 animate-pulse"></span>
              <span className="text-[10px] font-bold text-green-600">WHISPER-V3 ACTIVE</span>
            </div>
          </div>
          
          <div className="flex-1 space-y-6 overflow-y-auto max-h-[400px] pr-2">
            {transcript.map((m, i) => (
              <div key={i} className={`flex items-start gap-4 ${m.role === 'agent' ? 'flex-row-reverse' : ''}`}>
                <div className={`h-10 w-10 shrink-0 rounded-full grid place-items-center font-bold border-2 border-white shadow-sm ${m.role === 'agent' ? 'bg-brand-blue text-white' : 'bg-gray-100 text-gray-600'}`}>
                  {m.role === 'agent' ? 'YO' : 'SJ'}
                </div>
                <div className={`max-w-[80%] ${m.role === 'agent' ? 'text-right' : ''}`}>
                  <div className="text-xs font-bold text-gray-400 mb-1">{m.name} • {m.time}</div>
                  <div className={`rounded-2xl p-4 text-sm leading-relaxed shadow-sm border ${m.role === 'agent' ? 'bg-brand-blue text-white border-blue-600 rounded-tr-none' : 'bg-white text-gray-700 border-gray-100 rounded-tl-none'}`}>
                    {m.text}
                  </div>
                </div>
              </div>
            ))}
            <div className="flex items-start gap-4 opacity-50 animate-pulse">
              <div className="h-10 w-10 rounded-full bg-gray-100 grid place-items-center text-gray-400 font-bold">SJ</div>
              <div>
                <div className="text-xs font-bold text-gray-400 mb-1">Sarah Jenkins • Transcribing...</div>
                <div className="rounded-2xl border-2 border-dashed p-4 text-sm text-gray-400 bg-gray-50/50">
                  Well, we actually had to delay the board meeting because we couldn&apos;t verify the conversion numbers...
                </div>
              </div>
            </div>
          </div>

          <div className="mt-8 pt-6 border-t border-gray-100">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2 text-xs font-bold text-gray-400 uppercase tracking-widest">
                <span>AI Suggested Hook</span>
              </div>
              <div className="flex gap-2">
                <button onClick={() => setInput("What's the cost of that delay to your bottom line?")} className="text-[11px] font-bold bg-blue-50 text-brand-blue px-3 py-1 rounded-full border border-blue-100 hover:bg-blue-100 transition">Cost of delay?</button>
                <button onClick={() => setInput("Who else in your leadership team is feeling this pain?")} className="text-[11px] font-bold bg-blue-50 text-brand-blue px-3 py-1 rounded-full border border-blue-100 hover:bg-blue-100 transition">Influencers affected?</button>
              </div>
            </div>
            <div className="bg-gray-50 p-4 rounded-xl border border-gray-200">
              <div className="flex items-center gap-4 mb-3">
                <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
                  <div className="h-full bg-green-500 w-3/4"></div>
                </div>
                <div className="text-[10px] font-bold text-green-600">SENTIMENT: 75% POSITIVE</div>
              </div>
              <div className="flex items-center gap-3">
                <input 
                  value={input} 
                  onChange={e => setInput(e.target.value)} 
                  onKeyDown={e => e.key === 'Enter' && handleSend()}
                  placeholder="Type to coach or send response..." 
                  className="flex-1 bg-white rounded-lg border border-gray-200 px-4 py-3 text-sm focus:ring-2 focus:ring-blue-100 focus:border-brand-blue outline-none transition" 
                />
                <button onClick={handleSend} className="btn btn-primary px-6 py-3 rounded-lg font-bold shadow-lg shadow-blue-100 active:scale-95 transition">SEND</button>
              </div>
            </div>
          </div>
        </div>
      </section>
      <section className="col-span-12 lg:col-span-5">
        <AssistCard />
      </section>
    </div>
  )
}
