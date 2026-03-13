"use client";
import { useState } from 'react'

const API = 'http://localhost:8000'

interface AgentBuilderResult {
  executive_summary?: string
  trigger_analysis?: { category?: string; urgency?: string; primary_emotion?: string; confidence_score?: number }
  context_intelligence?: { competitor_context?: string; knowledge_base_insights?: string }
  risk_assessment?: { churn_risk?: string; escalation_likelihood?: string }
  resolution_playbook?: { step: number; action: string; script: string }[]
  response_templates?: { template: string; tone: string; channel: string }[]
  agent_coaching_notes?: string
}

function AssistCard({ result, loading }: { result: AgentBuilderResult | null; loading: boolean }) {
  if (loading) {
    return (
      <div className="space-y-4">
        <div className="rounded-xl border border-blue-100 bg-blue-50 p-4 animate-pulse">
          <div className="h-4 bg-blue-200 rounded w-3/4 mb-2"></div>
          <div className="h-3 bg-blue-100 rounded w-full mb-1"></div>
          <div className="h-3 bg-blue-100 rounded w-5/6"></div>
        </div>
        <div className="card p-4 animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/2 mb-3"></div>
          <div className="h-3 bg-gray-100 rounded w-full mb-1"></div>
          <div className="h-3 bg-gray-100 rounded w-4/5"></div>
        </div>
      </div>
    )
  }

  if (!result) {
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
            <div className="italic text-sm text-gray-700">Click "Analyze with AI" to get real intelligence from your Elasticsearch database.</div>
            <div className="border-t pt-3 text-[11px] font-semibold tracking-wide text-gray-500">KILLER QUESTION TO DROP:</div>
            <div className="rounded-lg bg-blue-50 p-3 text-sm">Click Analyze to generate a real talking point based on actual review data.</div>
          </div>
        </div>
        <div className="card p-4">
          <div className="text-sm text-gray-500 text-center py-4">Real competitor intelligence will appear here after analysis.</div>
        </div>
      </div>
    )
  }

  const urgencyColor = result.trigger_analysis?.urgency === 'high' ? 'bg-brand-red' : result.trigger_analysis?.urgency === 'medium' ? 'bg-yellow-500' : 'bg-blue-500'
  const churnRisk = result.risk_assessment?.churn_risk || 'medium'

  return (
    <div className="space-y-4">
      {/* Competitor Alert */}
      <div className="rounded-xl border border-red-200 bg-red-50 p-0 shadow">
        <div className={`flex items-center justify-between rounded-t-xl ${urgencyColor} px-4 py-2 text-white text-sm`}>
          <div>LIVE INTELLIGENCE: {result.trigger_analysis?.category?.toUpperCase() || 'CUSTOMER SIGNAL'}</div>
          <div className="pill bg-white/20 text-white">{result.trigger_analysis?.urgency?.toUpperCase() || 'DETECTED'}</div>
        </div>
        <div className="space-y-3 p-4">
          <div className="font-semibold">Emotion: {result.trigger_analysis?.primary_emotion || 'Frustration'}</div>
          <div className={`text-xs font-bold ${churnRisk === 'high' ? 'text-red-600' : churnRisk === 'medium' ? 'text-yellow-600' : 'text-green-600'}`}>
            Churn Risk: {churnRisk.toUpperCase()} · Escalation: {result.risk_assessment?.escalation_likelihood || 'medium'}
          </div>
          <div className="italic text-sm text-gray-700">{result.context_intelligence?.competitor_context || 'See knowledge base insights below.'}</div>
          {result.response_templates?.[0] && (
            <>
              <div className="border-t pt-3 text-[11px] font-semibold tracking-wide text-gray-500">KILLER TALKING POINT:</div>
              <div className="rounded-lg bg-blue-50 p-3 text-sm">{result.response_templates[0].template}</div>
            </>
          )}
        </div>
      </div>

      {/* Playbook */}
      {result.resolution_playbook && result.resolution_playbook.length > 0 && (
        <div className="card p-4">
          <div className="flex items-center gap-2 mb-3">
            <div className="h-6 w-6 grid place-items-center rounded bg-blue-100 text-brand-blue">★</div>
            <div className="font-semibold">RESOLUTION PLAYBOOK</div>
          </div>
          <div className="space-y-2">
            {result.resolution_playbook.map((step) => (
              <div key={step.step} className="rounded-lg border p-3">
                <div className="flex items-center gap-2 mb-1">
                  <span className="pill bg-brand-blue text-white">Step {step.step}</span>
                  <span className="font-medium text-sm">{step.action}</span>
                </div>
                <p className="text-xs text-gray-600">{step.script}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Coaching notes */}
      {result.agent_coaching_notes && (
        <div className="card p-4 border-yellow-100 bg-yellow-50/30">
          <div className="text-[11px] font-semibold tracking-wide text-gray-500 mb-2">COACH NOTES</div>
          <p className="text-sm text-gray-700">{result.agent_coaching_notes}</p>
        </div>
      )}

      {/* Summary */}
      {result.executive_summary && (
        <div className="card flex items-center justify-between p-4">
          <div>
            <div className="font-medium text-sm">AI Executive Summary</div>
            <div className="text-sm text-gray-600 mt-1">{result.executive_summary.slice(0, 120)}...</div>
          </div>
        </div>
      )}
    </div>
  )
}

export default function SalesAssistant() {
  const [input, setInput] = useState('')
  const [agentResult, setAgentResult] = useState<AgentBuilderResult | null>(null)
  const [loadingAgent, setLoadingAgent] = useState(false)
  const [transcript, setTranscript] = useState([
    { role: 'customer', name: 'Sarah Jenkins', time: '10:42 AM', text: "We've been using Competitor X for the last two years, but honestly, their analytics dashboard has been extremely buggy since the last update. It's making our quarterly reporting a nightmare." },
    { role: 'agent', name: 'You', time: '10:43 AM', text: "I hear that a lot. Reliability in reporting is the foundation of making good business decisions. When the data is buggy, it's not just a technical issue, it's a trust issue. How has that specifically impacted your team's workflow this month?" }
  ])

  const handleSend = () => {
    if (!input.trim()) return
    setTranscript(prev => [...prev, { role: 'agent', name: 'You', time: 'now', text: input }])
    setInput('')
  }

  const analyzeWithAI = async () => {
    const customerText = transcript.filter(m => m.role === 'customer').map(m => m.text).join(' ')
    setLoadingAgent(true)
    try {
      const res = await fetch(`${API}/agent-builder`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ customer_input: customerText }),
      })
      const data = await res.json()
      setAgentResult(data)
    } catch (e) {
      console.error('Agent builder failed', e)
    } finally {
      setLoadingAgent(false)
    }
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
            <button
              onClick={analyzeWithAI}
              disabled={loadingAgent}
              className="btn btn-primary px-4 py-2 rounded-lg text-sm font-bold shadow-lg shadow-blue-100 active:scale-95 disabled:opacity-60"
            >
              {loadingAgent ? '⏳ Analyzing...' : '⚡ Analyze with AI'}
            </button>
            <button className="btn btn-danger px-4 py-1.5 rounded-lg text-sm font-bold">END CALL</button>
          </div>
        </div>

        <div className="mt-6 bg-white p-6 rounded-2xl shadow-sm border border-gray-100 min-h-[500px] flex flex-col">
          <div className="flex items-center justify-between mb-6 border-b pb-4">
            <div className="text-[11px] font-bold tracking-widest text-gray-400 uppercase">Live Call Intelligence</div>
            <div className="flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-green-500 animate-pulse"></span>
              <span className="text-[10px] font-bold text-green-600">AWS TRANSCRIBE ACTIVE</span>
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
          </div>

          <div className="mt-8 pt-6 border-t border-gray-100">
            <div className="flex items-center gap-3">
              <input
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleSend()}
                placeholder="Type your response..."
                className="flex-1 bg-white rounded-lg border border-gray-200 px-4 py-3 text-sm focus:ring-2 focus:ring-blue-100 focus:border-brand-blue outline-none transition"
              />
              <button onClick={handleSend} className="btn btn-primary px-6 py-3 rounded-lg font-bold shadow-lg shadow-blue-100 active:scale-95 transition">SEND</button>
            </div>
          </div>
        </div>
      </section>

      <section className="col-span-12 lg:col-span-5">
        <AssistCard result={agentResult} loading={loadingAgent} />
      </section>
    </div>
  )
}
