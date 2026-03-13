import Link from 'next/link'

const tiles = [
  {
    href: '/chatbot',
    title: 'Sales-Optimized Support Bot',
    desc: 'Customer-facing chat with citations and upsell prompts.'
  },
  {
    href: '/sales',
    title: 'Customer Pitching Assistant',
    desc: 'Live call co-pilot with competitor cards and coaching.'
  },
  {
    href: '/support',
    title: 'Support Prompting Agent',
    desc: 'Agent console with live transcription and smart suggestions.'
  },
  {
    href: '/dashboard',
    title: 'Recommendations Dashboard',
    desc: 'Executive insights with cited sources and actions.'
  }
]

export default function Page() {
  return (
    <div className="py-8">
      <div className="mb-6 flex items-baseline justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">ElasticCX Suite</h1>
          <p className="text-sm text-gray-600">UI-only prototype mapped to the PRD</p>
        </div>
        <Link href="/chatbot" className="btn btn-primary px-4 py-2">Open Support Bot</Link>
      </div>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {tiles.map(t => (
          <Link key={t.href} href={t.href} className="card p-4 hover:shadow-md transition">
            <div className="flex items-center justify-between">
              <div className="font-semibold">{t.title}</div>
              <span className="pill bg-blue-50 text-brand-blue">UI</span>
            </div>
            <p className="mt-2 text-sm text-gray-600">{t.desc}</p>
          </Link>
        ))}
      </div>
    </div>
  )
}
