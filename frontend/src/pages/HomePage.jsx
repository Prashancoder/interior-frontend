import { Link } from 'react-router-dom'
import { assetUrl } from '../api'

const HOW_IT_WORKS_STEPS = [
  {
    step: '01',
    title: 'Upload Your Room',
    desc: 'Take a clear photo of your living room, bedroom, dining space or office and upload it instantly.',
    icon: (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
        <polyline points="17 8 12 3 7 8" />
        <line x1="12" y1="3" x2="12" y2="15" />
      </svg>
    ),
  },
  {
    step: '02',
    title: 'Tell Us Your Style & Budget',
    desc: 'Specify your maximum budget and select your preferred aesthetic from Minimalist to Luxury Modern.',
    icon: (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="10" />
        <path d="M16 8h-6a2 2 0 1 0 0 4h4a2 2 0 1 1 0 4H8" />
        <path d="M12 18V6" />
      </svg>
    ),
  },
  {
    step: '03',
    title: 'AI Analyzes Your Space',
    desc: 'Vision AI automatically extracts wall colors, floor materials, lighting conditions, and room dimensions.',
    icon: (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z" />
        <circle cx="12" cy="12" r="3" />
      </svg>
    ),
  },
  {
    step: '04',
    title: 'Get Product Recommendations',
    desc: 'Our OpenCLIP vector engine retrieves real matching catalog items from verified furniture vendors.',
    icon: (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="m7.5 4.27 9 5.15" />
        <path d="M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z" />
        <path d="m3.3 7 8.7 5 8.7-5" />
        <path d="M12 22V12" />
      </svg>
    ),
  },
  {
    step: '05',
    title: 'Generate Your Designed Room',
    desc: 'AI synthesizes a cohesive design vision bringing together the selected products with your room structure.',
    icon: (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="m12 3-1.9 5.8a2 2 0 0 1-1.3 1.3L3 12l5.8 1.9a2 2 0 0 1 1.3 1.3L12 21l1.9-5.8a2 2 0 0 1 1.3-1.3L21 12l-5.8-1.9a2 2 0 0 1-1.3-1.3Z" />
      </svg>
    ),
  },
  {
    step: '06',
    title: 'Buy the Look',
    desc: 'Transparent pricing with verified seller details makes it easy to purchase each element directly.',
    icon: (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="8" cy="21" r="1" />
        <circle cx="19" cy="21" r="1" />
        <path d="M2.05 2.05h2l2.66 12.42a2 2 0 0 0 2 1.58h9.78a2 2 0 0 0 1.95-1.57l1.65-7.43H5.12" />
      </svg>
    ),
  },
]

const STYLES = [
  {
    name: 'Modern Contemporary',
    tag: 'Popular',
    desc: 'Clean lines, neutral base with bold accents, functional elegance and airy spaces.',
    colorHex: '#3d5248',
  },
  {
    name: 'Minimalist',
    tag: 'Essential',
    desc: 'Decluttered simplicity, purposeful furniture, natural light, and soothing palettes.',
    colorHex: '#6b6358',
  },
  {
    name: 'Scandinavian',
    tag: 'Trending',
    desc: 'Warm woods, soft textiles, cozy hygge atmosphere, and organic silhouettes.',
    colorHex: '#9b7e5a',
  },
  {
    name: 'Luxury Modern',
    tag: 'Premium',
    desc: 'Rich velvet textures, brass and marble accents, dramatic lighting, and deep tones.',
    colorHex: '#734d31',
  },
  {
    name: 'Industrial',
    tag: 'Urban',
    desc: 'Exposed structural elements, rustic wood, metallic fixtures, and loft-inspired tones.',
    colorHex: '#484d51',
  },
  {
    name: 'Classic',
    tag: 'Timeless',
    desc: 'Symmetrical arrangements, intricate mouldings, timeless upholstery, and graceful warmth.',
    colorHex: '#52433d',
  },
]

const CATALOG_CATEGORIES = [
  { name: 'Sofas & Lounges', count: '18+ Items', category: 'sofa', icon: '🛋️' },
  { name: 'Designer Beds', count: '12+ Items', category: 'bed', icon: '🛏️' },
  { name: 'Curtains & Drapes', count: '14+ Items', category: 'curtain', icon: '🪟' },
  { name: 'Ambient Lighting', count: '16+ Items', category: 'lighting', icon: '💡' },
  { name: 'Wallpapers & Art', count: '20+ Items', category: 'wallpaper', icon: '🖼️' },
  { name: 'Decor & Accents', count: '25+ Items', category: 'decor', icon: '🏺' },
  { name: 'Tables & Consoles', count: '10+ Items', category: 'table', icon: '🪵' },
  { name: 'Accent Chairs', count: '15+ Items', category: 'chair', icon: '🪑' },
]

export default function HomePage() {
  return (
    <div className="home-page">
      {/* 1. HERO SECTION */}
      <section className="hero-section">
        <div className="hero-container">
          <div className="hero-content">
            <div className="hero-pill">
              <span className="pill-dot" />
              <span>Next-Gen AI Interior Design Engine</span>
            </div>
            <h1 className="hero-title">
              Transform Your Space <span className="highlight-text">with AI</span>
            </h1>
            <p className="hero-subtitle">
              Upload your room, choose your style and budget, and let AI create a personalized interior design using real products from our catalog.
            </p>
            <div className="hero-actions">
              <Link to="/decor" className="btn-hero-primary">
                <span>Design My Room</span>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M5 12h14" />
                  <path d="m12 5 7 7-7 7" />
                </svg>
              </Link>
              <a href="#how-it-works" className="btn-hero-secondary">
                How It Works
              </a>
            </div>
            <div className="hero-stats">
              <div className="hero-stat-item">
                <strong>Real</strong>
                <span>Catalog Items</span>
              </div>
              <div className="stat-divider" />
              <div className="hero-stat-item">
                <strong>100%</strong>
                <span>Budget Aware</span>
              </div>
              <div className="stat-divider" />
              <div className="hero-stat-item">
                <strong>Vision AI</strong>
                <span>Room Analysis</span>
              </div>
            </div>
          </div>

          <div className="hero-visual">
            <div className="hero-image-wrapper">
              <img
                src={assetUrl('/hero-design.jpg')}
                alt="AI Designed Living Room Interior"
                className="hero-main-img"
              />
              <div className="hero-floating-badge badge-top">
                <div className="badge-icon-wrap">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="12" cy="12" r="10" />
                    <polyline points="12 6 12 12 14 14" />
                  </svg>
                </div>
                <div>
                  <div className="badge-label">Groq Vision AI</div>
                  <div className="badge-val">Room Layout Analyzed</div>
                </div>
              </div>

              <div className="hero-floating-badge badge-bottom">
                <div className="badge-icon-wrap gold">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
                  </svg>
                </div>
                <div>
                  <div className="badge-label">Budget Matching</div>
                  <div className="badge-val">Catalog Products Matched</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 2. HOW IT WORKS SECTION */}
      <section id="how-it-works" className="section-container how-it-works-section">
        <div className="section-header">
          <span className="section-sub">Simple 6-Step Experience</span>
          <h2 className="section-title">How Decore AI Works</h2>
          <p className="section-desc">
            From your room photograph to a fully realized, budget-accurate interior design with purchasable catalog items.
          </p>
        </div>

        <div className="steps-grid">
          {HOW_IT_WORKS_STEPS.map((s) => (
            <div key={s.step} className="step-card">
              <div className="step-top">
                <span className="step-number">{s.step}</span>
                <div className="step-icon">{s.icon}</div>
              </div>
              <h3 className="step-title">{s.title}</h3>
              <p className="step-desc">{s.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* 3. AI-POWERED INTERIOR DESIGN SPOTLIGHT */}
      <section className="section-container ai-spotlight-section">
        <div className="ai-spotlight-card">
          <div className="ai-spotlight-content">
            <span className="section-sub">Intelligent Technology</span>
            <h2 className="section-title">AI That Understands Architecture & Real Products</h2>
            <p className="section-desc">
              Unlike generic image generators that produce impossible furniture you cannot buy, Decore AI couples computer vision with a live multi-vendor catalog.
            </p>
            <ul className="ai-feature-list">
              <li>
                <div className="feature-check">✓</div>
                <div>
                  <strong>Vision AI Room Decomposition</strong>
                  <p>Accurately detects wall tones, flooring materials, existing furniture, and natural lighting.</p>
                </div>
              </li>
              <li>
                <div className="feature-check">✓</div>
                <div>
                  <strong>Multi-Modal OpenCLIP Semantic Search</strong>
                  <p>Finds real catalog products whose visual embeddings harmonize with your room structure.</p>
                </div>
              </li>
              <li>
                <div className="feature-check">✓</div>
                <div>
                  <strong>Strict Budget Optimization</strong>
                  <p>Balances your total expenditure so you never fall in love with a design you cannot afford.</p>
                </div>
              </li>
            </ul>
            <div style={{ marginTop: 24 }}>
              <Link to="/decor" className="btn-primary">
                Try Room Analysis Now →
              </Link>
            </div>
          </div>

          <div className="ai-spotlight-visual">
            <div className="tech-breakdown-card">
              <div className="tech-header">
                <span className="tech-indicator" />
                <span>Live AI Pipeline</span>
              </div>
              <div className="tech-row">
                <span className="tech-label">Vision Model</span>
                <span className="tech-value">Groq Llama-3.2 11B Vision</span>
              </div>
              <div className="tech-row">
                <span className="tech-label">Vector Database</span>
                <span className="tech-value">Qdrant Collection (512-dim)</span>
              </div>
              <div className="tech-row">
                <span className="tech-label">Embeddings</span>
                <span className="tech-value">OpenCLIP ViT-B-32</span>
              </div>
              <div className="tech-row">
                <span className="tech-label">Catalog Source</span>
                <span className="tech-value">Real Verified Sellers</span>
              </div>
              <div className="tech-row">
                <span className="tech-label">Budget Solver</span>
                <span className="tech-value">Dynamic Category Allocator</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 4. CHOOSE YOUR STYLE */}
      <section className="section-container styles-section">
        <div className="section-header">
          <span className="section-sub">Aesthetic Direction</span>
          <h2 className="section-title">Choose Your Style</h2>
          <p className="section-desc">
            Select an interior design aesthetic and our AI will curate colors, textures, and furniture pieces tailored to that mood.
          </p>
        </div>

        <div className="styles-grid">
          {STYLES.map((style) => (
            <div key={style.name} className="style-card">
              <div className="style-badge" style={{ borderColor: style.colorHex, color: style.colorHex }}>
                {style.tag}
              </div>
              <h3 className="style-name">{style.name}</h3>
              <p className="style-desc">{style.desc}</p>
              <Link to="/decor" className="style-link">
                Explore in Decor AI →
              </Link>
            </div>
          ))}
        </div>
      </section>

      {/* 5. DESIGN WITHIN YOUR BUDGET */}
      <section className="section-container budget-section">
        <div className="budget-box-spotlight">
          <div className="budget-text">
            <span className="section-sub">Budget Intelligence</span>
            <h2 className="section-title">Design Within Your Exact Budget</h2>
            <p className="section-desc">
              Whether you have ₹25,000 for a cozy corner refresh or ₹2,50,000 for a luxury master suite redesign, Decore AI allocates funds across essential categories to keep you on budget.
            </p>
            <div className="budget-chips">
              <div className="budget-chip">
                <span>Starter Refresh</span>
                <strong>₹25,000 – ₹50,000</strong>
              </div>
              <div className="budget-chip highlighted">
                <span>Standard Room</span>
                <strong>₹75,000 – ₹1,20,000</strong>
              </div>
              <div className="budget-chip">
                <span>Luxury Makeover</span>
                <strong>₹1,50,000 – ₹3,00,000+</strong>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 6. REAL PRODUCTS FROM OUR CATALOG */}
      <section className="section-container catalog-section">
        <div className="section-header">
          <span className="section-sub">Multi-Vendor Marketplace</span>
          <h2 className="section-title">Real Products From Our Catalog</h2>
          <p className="section-desc">
            Every item recommended by our AI is a real, high-quality furniture or decor item registered by sellers on our platform.
          </p>
        </div>

        <div className="catalog-grid">
          {CATALOG_CATEGORIES.map((cat) => (
            <Link key={cat.name} to="/decor" className="catalog-cat-card">
              <div className="cat-icon-large">{cat.icon}</div>
              <div className="cat-info">
                <h4>{cat.name}</h4>
                <span className="cat-count">{cat.count}</span>
              </div>
              <span className="cat-arrow">→</span>
            </Link>
          ))}
        </div>
      </section>

      {/* 7. WHY DECORE AI */}
      <section className="section-container why-section">
        <div className="section-header">
          <span className="section-sub">Platform Advantages</span>
          <h2 className="section-title">Why Choose Decore AI?</h2>
          <p className="section-desc">
            The bridge between generative design dreams and physical furniture reality.
          </p>
        </div>

        <div className="why-grid">
          <div className="why-card">
            <div className="why-icon">🏷️</div>
            <h3>Real Purchasable Products</h3>
            <p>No fantasy concepts that cannot be bought. Every recommendation maps directly to an active seller SKU.</p>
          </div>
          <div className="why-card">
            <div className="why-icon">⚡</div>
            <h3>Instant Vision AI Analysis</h3>
            <p>Upload a photo from your phone and get full architectural and stylistic breakdown in seconds.</p>
          </div>
          <div className="why-card">
            <div className="why-icon">💰</div>
            <h3>No Surprise Costs</h3>
            <p>Transparent pricing with real-time budget calculations ensures you always stay in control of expenses.</p>
          </div>
          <div className="why-card">
            <div className="why-icon">🛡️</div>
            <h3>Verified Sellers</h3>
            <p>Curated catalog from vetted interior vendors and artisan manufacturers across the nation.</p>
          </div>
        </div>
      </section>

      {/* 8. CALL TO ACTION BANNER */}
      <section className="section-container cta-section">
        <div className="cta-banner">
          <div className="cta-content">
            <h2>Ready to Redesign Your Room?</h2>
            <p>Upload a room photo, pick your budget and style, and let Decore AI generate your customized design right now.</p>
            <div className="cta-actions">
              <Link to="/decor" className="btn-cta-primary">
                Start Designing for Free
              </Link>
              <Link to="/about" className="btn-cta-secondary">
                Learn About Our Technology
              </Link>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}
