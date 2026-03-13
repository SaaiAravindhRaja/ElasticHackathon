function Kpi({ title, value, delta, positive }: { title: string; value: string; delta: string; positive?: boolean }) {
  return (
    <div className="card p-4">
      <div className="text-sm text-gray-600">{title}</div>
      <div className="mt-1 text-2xl font-bold">{value}</div>
      <div className={positive ? 'text-green-600 text-xs' : 'text-red-600 text-xs'}>{delta}</div>
    </div>
  )
}

export default function Dashboard() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-2xl font-bold">Recommendations Dashboard</div>
          <div className="text-sm text-gray-600">Strategic insights synthesized from 12,400+ customer touchpoints and real-time market signals.</div>
        </div>
        <div className="flex items-center gap-2">
          <button className="btn btn-outline px-3 py-1.5">Last 30 Days</button>
          <button className="btn btn-primary px-3 py-1.5">Export Strategy</button>
        </div>
      </div>
      <div className="grid gap-4 sm:grid-cols-3">
        <Kpi title="Churn Vulnerability Gap" value="14 Critical Issues" delta="5% vs last month" positive />
        <Kpi title="Feature Mention Volume" value="1.2k Requests" delta="22% increase" />
        <Kpi title="At-Risk Revenue" value="$2.4M ARR" delta="$400k SOC2 related" />
      </div>
      <div className="grid grid-cols-12 gap-6">
        <div className="col-span-7 space-y-4">
          <div className="card p-4">
            <div className="flex items-center justify-between">
              <div className="font-semibold">Lost Revenue Insights</div>
              <span className="pill bg-red-50 text-brand-red">Critical Priority</span>
            </div>
            <div className="mt-3 space-y-3">
              <div className="rounded-lg border p-3">
                <div className="flex items-center justify-between">
                  <div className="font-medium">COMPLIANCE GAP: SOC2</div>
                  <div className="text-brand-red font-semibold">$1.8M Lost</div>
                </div>
                <p className="mt-1 text-sm text-gray-700">Unable to clear enterprise procurement due to missing Type II SOC2 report. Major deal block for Fintech segment.</p>
                <div className="mt-2">
                  <span className="pill bg-blue-50 text-brand-blue">Cited in 42 Sales calls</span>
                </div>
              </div>
              <div className="rounded-lg border p-3">
                <div className="flex items-center justify-between">
                  <div className="font-medium">INTEGRATION: SAP S/4HANA</div>
                  <div className="text-brand-red font-semibold">$600k Lost</div>
                </div>
                <p className="mt-1 text-sm text-gray-700">Competitor X won on native SAP integration. Client mentioned manual CSV upload was a dealbreaker.</p>
                <div className="mt-2">
                  <span className="pill bg-gray-100 text-gray-700">Source: Account Executive Email</span>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div className="col-span-5 space-y-4">
          <div className="card p-4">
            <div className="flex items-center justify-between">
              <div className="font-semibold">Top Requested Features</div>
              <span className="pill bg-blue-50 text-brand-blue">Product Focus</span>
            </div>
            <div className="mt-3 space-y-3 text-sm">
              <div>
                <div className="flex items-center justify-between">
                  <div>Elastic Search kNN Clustering</div>
                  <div className="text-gray-600">482 Mentions</div>
                </div>
                <div className="mt-1 h-2 w-full rounded bg-blue-100">
                  <div className="h-2 w-4/5 rounded bg-brand-blue"></div>
                </div>
                <div className="text-xs text-gray-500">Recent: Customer Support Call #18291 (High Sentiment)</div>
              </div>
              <div>
                <div className="flex items-center justify-between">
                  <div>Advanced RBAC (Role-based Access)</div>
                  <div className="text-gray-600">315 Mentions</div>
                </div>
                <div className="mt-1 h-2 w-full rounded bg-blue-100">
                  <div className="h-2 w-3/5 rounded bg-brand-blue"></div>
                </div>
                <div className="text-xs text-gray-500">Recent: Slack Community Feature Request (22 Upvotes)</div>
              </div>
              <div>
                <div className="flex items-center justify-between">
                  <div>Mobile App (iOS/Android)</div>
                  <div className="text-gray-600">228 Mentions</div>
                </div>
                <div className="mt-1 h-2 w-full rounded bg-blue-100">
                  <div className="h-2 w-2/5 rounded bg-brand-blue"></div>
                </div>
                <div className="text-xs text-gray-500">Recent: Survey Response – Need on-the-go access</div>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div className="card p-4">
        <div className="font-semibold">Market Intelligence: Competitor Vulnerabilities</div>
        <div className="mt-3 overflow-auto">
          <table className="min-w-full text-sm">
            <thead className="text-left text-gray-500">
              <tr>
                <th className="py-2 pr-4">COMPETITOR</th>
                <th className="py-2 pr-4">VULNERABILITY IDENTIFIED</th>
                <th className="py-2 pr-4">EVIDENCE LEVEL</th>
                <th className="py-2 pr-4">STRATEGIC ACTION</th>
                <th className="py-2">SOURCE</th>
              </tr>
            </thead>
            <tbody>
              <tr className="border-t">
                <td className="py-2 pr-4">Competitor Y</td>
                <td className="py-2 pr-4">
                  <div>Mac OS Stability Issues</div>
                  <div className="text-xs text-gray-500">Frequent kernel crashes on M2 chips</div>
                </td>
                <td className="py-2 pr-4 text-yellow-500">★★★★☆</td>
                <td className="py-2 pr-4"><span className="pill bg-blue-50 text-brand-blue">Target Creative Campaign</span></td>
                <td className="py-2">🔗</td>
              </tr>
              <tr className="border-t">
                <td className="py-2 pr-4">Competitor Z</td>
                <td className="py-2 pr-4">
                  <div>Hidden Seat Licensing Fees</div>
                  <div className="text-xs text-gray-500">Recent price hike 20% (Q4)</div>
                </td>
                <td className="py-2 pr-4 text-yellow-500">★★★☆☆</td>
                <td className="py-2 pr-4"><span className="pill bg-green-50 text-green-600">Update Pricing One-Pager</span></td>
                <td className="py-2">📄</td>
              </tr>
              <tr className="border-t">
                <td className="py-2 pr-4">Alpha Cloud</td>
                <td className="py-2 pr-4">
                  <div>No On-Prem Support</div>
                  <div className="text-xs text-gray-500">Government clients frustrated</div>
                </td>
                <td className="py-2 pr-4 text-yellow-500">★★★★☆</td>
                <td className="py-2 pr-4"><span className="pill bg-blue-50 text-brand-blue">Sales Playbook: Public Sector</span></td>
                <td className="py-2">📄</td>
              </tr>
            </tbody>
          </table>
        </div>
        <div className="mt-3 flex items-center justify-between text-xs text-gray-600">
          <div className="flex items-center gap-2">
            <span>DATA STATUS: LIVE</span>
            <span>•</span>
            <span>LAST SYNCED: 4M AGO</span>
          </div>
          <div className="flex items-center gap-3">
            <a href="#" className="text-brand-blue">Documentation</a>
            <a href="#" className="text-brand-blue">Data Privacy</a>
            <a href="#" className="text-brand-blue">Support</a>
          </div>
        </div>
      </div>
    </div>
  )
}
