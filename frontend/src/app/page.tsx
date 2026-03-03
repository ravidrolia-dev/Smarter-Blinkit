import Link from "next/link";

export default function HomePage() {
  return (
    <div className="min-h-screen" style={{ background: "var(--off-white)" }}>
      {/* Navbar */}
      <nav className="navbar">
        <div className="navbar-logo">
          <span>⚡</span>
          <span>Smarter<span>BlinkIt</span></span>
        </div>
        <div className="flex gap-3">
          <Link href="/login" className="btn-ghost">Sign In</Link>
          <Link href="/register" className="btn-primary">Get Started</Link>
        </div>
      </nav>

      {/* Hero */}
      <section className="hero pt-24 pb-20 px-6">
        <div className="max-w-5xl mx-auto text-center relative">
          <span className="badge badge-yellow mb-4 text-sm px-4 py-1.5 animate-fade-up">
            🚀 AI-Powered Smart Marketplace
          </span>
          <h1 className="text-6xl font-black text-gray-900 mb-6 leading-tight animate-fade-up" style={{ animationDelay: "60ms" }}>
            Shop by intent,<br />not by keyword.
          </h1>
          <p className="text-xl text-gray-700 mb-8 max-w-2xl mx-auto animate-fade-up" style={{ animationDelay: "120ms" }}>
            Tell us <strong>"Make Pizza for 4 people"</strong> — our AI finds every ingredient from local shops and fills your cart in one click.
          </p>
          <div className="flex gap-4 justify-center flex-wrap animate-fade-up" style={{ animationDelay: "180ms" }}>
            <Link href="/register?role=buyer" className="btn-primary text-base px-8 py-3.5">
              🛒 Start Shopping
            </Link>
            <Link href="/register?role=seller" className="btn-secondary text-base px-8 py-3.5">
              🏪 Become a Seller
            </Link>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-20 px-6 max-w-6xl mx-auto">
        <div className="text-center mb-12">
          <h2 className="text-4xl font-black text-gray-900 mb-2">Everything you need</h2>
          <p className="text-gray-500">5 powerful features. 1 seamless experience.</p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 stagger">
          {[
            {
              icon: "🤖", title: "AI Recipe Agent",
              desc: "Type \"Make Biryani for 6\" and the AI parses the recipe, finds all ingredients from nearby shops, and fills your cart."
            },
            {
              icon: "🔍", title: "Intent Search",
              desc: "Search naturally — \"I have a cold\" surfaces Honey, Ginger Tea, and Tulsi drops automatically using semantic AI."
            },
            {
              icon: "😊", title: "Face ID Login",
              desc: "Register your face once. Next time, just look at the camera to log in — no password needed."
            },
            {
              icon: "📷", title: "Barcode Inventory",
              desc: "Sellers scan boxes with their phone camera to update stock instantly. No manual typing, no mistakes."
            },
            {
              icon: "⚡", title: "Smart Cart Split",
              desc: "If items come from different shops, we intelligently split your order for the fastest, cheapest delivery."
            },
            {
              icon: "📊", title: "Live Storeboard",
              desc: "Real-time dashboard showing top-selling products, fastest shops, and live order feeds — refreshes every 15 seconds."
            },
          ].map((f) => (
            <div key={f.title} className="card animate-fade-up">
              <span className="text-4xl block mb-3">{f.icon}</span>
              <h3 className="text-lg font-bold text-gray-900 mb-2">{f.title}</h3>
              <p className="text-sm text-gray-500 leading-relaxed">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* How it works */}
      <section className="py-20 px-6" style={{ background: "var(--yellow-subtle)" }}>
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-4xl font-black text-gray-900 mb-12">How it works</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {[
              { step: "1", icon: "💬", title: "Tell the AI", desc: "Type what you want to cook or search for" },
              { step: "2", icon: "🔍", title: "AI finds it", desc: "Searches nearby shops for exact ingredients" },
              { step: "3", icon: "📦", title: "Delivered fast", desc: "Order split and delivered from nearest shops" },
            ].map((s) => (
              <div key={s.step} className="flex flex-col items-center">
                <div className="w-16 h-16 rounded-full flex items-center justify-center text-3xl mb-4 animate-pulse-yellow"
                  style={{ background: "var(--yellow-primary)" }}>
                  {s.icon}
                </div>
                <h3 className="text-lg font-bold text-gray-900 mb-1">{s.title}</h3>
                <p className="text-sm text-gray-500">{s.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 px-6 text-center">
        <h2 className="text-4xl font-black text-gray-900 mb-4">Ready to shop smarter?</h2>
        <p className="text-gray-500 mb-8">Join thousands of buyers and sellers on Smarter BlinkIt</p>
        <div className="flex gap-4 justify-center flex-wrap">
          <Link href="/register" className="btn-primary text-base px-10 py-4">
            Create Free Account →
          </Link>
          <Link href="/login" className="btn-ghost border border-gray-200 rounded-xl px-10 py-4">
            Sign In
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-gray-100 py-8 px-6 text-center">
        <div className="navbar-logo justify-center mb-2">
          <span>⚡</span>
          <span>Smarter<span>BlinkIt</span></span>
        </div>
        <p className="text-sm text-gray-400">
          Built with Next.js · FastAPI · MongoDB · Neo4j · Gemini AI
        </p>
      </footer>
    </div>
  );
}
