"use client";
import { useEffect, useState } from 'react'

const API = 'http://localhost:8000'

function Kpi({ title, value, delta, positive, loading }: { title: string; value: string; delta: string; positive?: boolean; loading?: boolean }) {
  return (
    <div className="card p-4">
      <div className="text-sm text-gray-600">{title}</div>
      {loading ? (
        <div className="mt-1 h-8 w-24 bg-gray-100 animate-pulse rounded"></div>
      ) : (
        <div className="mt-1 text-2xl font-bold">{value}</div>
      )}
      <div className={positive ? 'text-green-600 text-xs' : 'text-red-600 text-xs'}>{delta}</div>
    </div>
  )
}

export default function Dashboard() {
  const [overview, setOverview] = useState<any>(null)
  const [competitors, setCompetitors] = useState<any[]>([])
  const [aiInsight, setAiInsight] = useState<string>('')
  const [loadingInsight, setLoadingInsight] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchAll = async () => {
      try {
        const [ovRes, compRes] = await Promise.all([
          fetch(`${API}/analytics/overview`),
          fetch(`${API}/analytics/competitor-compare?companies=Zendesk,Freshdesk,HubSpot,Salesforce,Intercom`),
        ])
        if (ovRes.ok) setOverview(await ovRes.json())
        if (compRes.ok) {
          const d = await compRes.json()
          setCompetitors(d.results || [])
        }
      } catch (e) {
        console.error('Analytics load failed', e)
      } finally {
        setLoading(false)
      }
    }
    fetchAll()
  }, [])

  const generateInsight = async () => {
    setLoadingInsight(true)
    try {
      const res = await fetch(`${API}/ai/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: 'Based on all competitor reviews and market intelligence data, what are the top 3 strategic product improvements we should prioritize? Be specific and cite evidence.',
          mode: 'recommendations',
          output_format: 'text',
        }),
      })
      const d = await res.json()
      setAiInsight(d.answer || '')
    } catch (e) {
      setAiInsight('Failed to load AI insights. Check backend connection.')
    } finally {
      setLoadingInsight(false)
    }
  }

  const totalDocs =
    (overview?.company_knowledge?.doc_count || 0) +
    (overview?.market_intelligence?.doc_count || 0) +
    (overview?.customer_history?.doc_count || 0)

  const reviewCount = overview?.market_intelligence?.doc_count || 0
  const knowledgeCount = overview?.company_knowledge?.doc_count || 0

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-2xl font-bold">Recommendations Dashboard</div>
          <div className="text-sm text-gray-600">
            Live data from Elasticsearch — {totalDocs.toLocaleString()} documents indexed across 3 indices.
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="pill bg-green-50 text-green-600 border border-green-100">
            <span className="h-1.5 w-1.5 rounded-full bg-green-500 inline-block mr-1 animate-pulse"></span>
            LIVE DATA
          </span>
          <button onClick={generateInsight} disabled={loadingInsight} className="btn btn-primary px-3 py-1.5 disabled:opacity-60">
            {loadingInsight ? 'Generating...' : 'Generate AI Insights'}
          </button>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <Kpi
          title="Knowledge Base Documents"
          value={knowledgeCount.toLocaleString()}
          delta="Company docs + help articles"
          positive
          loading={loading}
        />
        <Kpi
          title="Competitor Reviews Indexed"
          value={reviewCount.toLocaleString()}
          delta="Trustpilot + G2 reviews"
          positive
          loading={loading}
        />
        <Kpi
          title="Total Indexed Documents"
          value={totalDocs.toLocaleString()}
          delta="Across all 3 ES indices"
          positive
          loading={loading}
        />
      </div>

      {aiInsight && (
        <div className="card p-5 border-blue-100 bg-blue-50/30">
          <div className="flex items-center gap-2 mb-3">
            <div className="h-6 w-6 grid place-items-center rounded bg-brand-blue text-white text-xs font-bold">AI</div>
            <div className="font-semibold text-gray-900">AI Strategic Insights</div>
            <span className="pill bg-blue-100 text-brand-blue">GPT-4o-mini + RRF Search</span>
          </div>
          <div className="text-sm text-gray-700 whitespace-pre-wrap leading-relaxed">{aiInsight}</div>
        </div>
      )}

      <div className="grid grid-cols-12 gap-6">
        <div className="col-span-12 lg:col-span-7 space-y-4">
          <div className="card p-4">
            <div className="flex items-center justify-between">
              <div className="font-semibold">Competitor Average Ratings</div>
              <span className="pill bg-blue-50 text-brand-blue">Live from Market Intelligence Index</span>
            </div>
            {loading ? (
              <div className="mt-3 space-y-2">
                {[1, 2, 3].map(i => <div key={i} className="h-12 bg-gray-100 animate-pulse rounded-lg"></div>)}
              </div>
            ) : competitors.length > 0 ? (
              <div className="mt-3 space-y-3">
                {competitors.map((c: any) => (
                  <div key={c.company} className="rounded-lg border p-3">
                    <div className="flex items-center justify-between">
                      <div className="font-medium">{c.company}</div>
                      <div className="flex items-center gap-2">
                        <span className="text-yellow-500">{'★'.repeat(Math.round(c.avg_rating || 0))}{'☆'.repeat(5 - Math.round(c.avg_rating || 0))}</span>
                        <span className="font-bold text-gray-900">{(c.avg_rating || 0).toFixed(2)}</span>
                      </div>
                    </div>
                    <div className="mt-1 flex items-center gap-2">
                      <div className="flex-1 h-2 rounded bg-gray-100">
                        <div
                          className="h-2 rounded bg-brand-blue"
                          style={{ width: `${((c.avg_rating || 0) / 5) * 100}%` }}
                        ></div>
                      </div>
                      <span className="text-xs text-gray-500">{c.review_count} reviews</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="mt-3 text-sm text-gray-400">No competitor data yet — run the review scraper first.</div>
            )}
          </div>
        </div>

        <div className="col-span-12 lg:col-span-5 space-y-4">
          <div className="card p-4">
            <div className="flex items-center justify-between">
              <div className="font-semibold">Data Index Breakdown</div>
              <span className="pill bg-blue-50 text-brand-blue">Elasticsearch</span>
            </div>
            {loading ? (
              <div className="mt-3 h-32 bg-gray-100 animate-pulse rounded-lg"></div>
            ) : (
              <div className="mt-3 space-y-3 text-sm">
                {[
                  { label: 'Company Knowledge', count: overview?.company_knowledge?.doc_count || 0, color: 'bg-brand-blue' },
                  { label: 'Market Intelligence', count: overview?.market_intelligence?.doc_count || 0, color: 'bg-purple-500' },
                  { label: 'Customer History', count: overview?.customer_history?.doc_count || 0, color: 'bg-green-500' },
                ].map(row => (
                  <div key={row.label}>
                    <div className="flex items-center justify-between">
                      <div>{row.label}</div>
                      <div className="text-gray-600">{row.count.toLocaleString()}</div>
                    </div>
                    <div className="mt-1 h-2 w-full rounded bg-gray-100">
                      <div
                        className={`h-2 rounded ${row.color}`}
                        style={{ width: totalDocs > 0 ? `${(row.count / totalDocs) * 100}%` : '0%' }}
                      ></div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="card p-4">
            <div className="font-semibold mb-3">Quick Actions</div>
            <div className="space-y-2 text-sm">
              <a href="/chatbot" className="flex items-center gap-2 rounded-lg border p-3 hover:bg-blue-50 transition cursor-pointer">
                <span>💬</span><span>Open Support Bot</span>
              </a>
              <a href="/sales" className="flex items-center gap-2 rounded-lg border p-3 hover:bg-blue-50 transition cursor-pointer">
                <span>📈</span><span>Sales Co-Pilot</span>
              </a>
              <a href="/support" className="flex items-center gap-2 rounded-lg border p-3 hover:bg-blue-50 transition cursor-pointer">
                <span>🎧</span><span>Live Support Agent</span>
              </a>
            </div>
          </div>
        </div>
      </div>

      <div className="flex items-center justify-between border-t border-gray-100 pt-3 text-[10px] font-bold text-gray-400 tracking-widest uppercase">
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-1.5"><span className="h-1.5 w-1.5 rounded-full bg-green-500 animate-pulse"></span> ES CLUSTER: LIVE</span>
          <span>RRF HYBRID SEARCH ACTIVE</span>
          <span>EMBEDDING: text-embedding-3-small</span>
        </div>
      </div>
    </div>
  )
}
