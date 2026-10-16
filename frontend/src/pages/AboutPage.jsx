import { Link } from 'react-router-dom'
import { assetUrl } from '../api'

const FEATURE_CARDS = [
  {
    title: 'Computer Vision Space Parsing',
    description: 'Groq Vision models detect structural constraints, natural lighting vectors, floor finishes, and wall palettes from a single smartphone photograph.',
    icon: '📐',
  },
  {
    title: 'Multi-Modal Vector Search',
    description: 'OpenCLIP ViT-B-32 neural embeddings paired with Qdrant vector indexing retrieve furniture matching both stylistic aesthetics and geometry.',
    icon: '🔮',
  },
  {
    title: 'Constraint-Aware Budget Engine',
    description: 'Intelligent cost distribution ensures complete room transformations fit squarely within user-defined financial constraints without quality loss.',
    icon: '⚖️',
  },
  {
    title: 'Multi-Vendor Catalog Grounding',
    description: 'Guarantees that every rendered concept is composed of physical items with active inventory, SKUs, and transparent seller listings.',
    icon: '🏷️',
  },
]

export default function AboutPage() {
  return (
    <div className="about-page">
      {/* 1. HERO */}
      <section className="about-hero">
        <div className="section-container">
          <div className="about-hero-content">
            <span className="section-sub">About Decore AI</span>
            <h1 className="about-title">
              Reimagining Interior Design Through <span className="highlight-text">Intelligent AI & Real Products</span>
            </h1>
            <p className="about-lead">
              Decore AI is a next-generation multi-vendor interior design platform designed to eliminate the friction between conceptual room styling and actual furniture purchasing.
            </p>
          </div>
        </div>
      </section>

      {/* 2. STUDIO IMAGE & MISSION */}
      <section className="section-container about-mission-section">
        <div className="mission-grid">
          <div className="mission-image-wrapper">
            <img
              src={assetUrl('/about-studio.jpg')}
              alt="Decore AI Architectural Studio Workspace"
              className="mission-img"
            />
          </div>
          <div className="mission-text-block">
            <span className="section-sub">Our Mission</span>
            <h2>Bridging the Gap Between Concept and Reality</h2>
            <p>
              Traditional interior design often requires expensive consultations, weeks of back-and-forth drafting, and tedious manual sourcing across dozens of disparate furniture stores.
            </p>
            <p>
              On the other hand, generic generative AI tools produce beautiful but impossible fantasy images featuring fictional chairs and phantom lights that do not exist in the physical world.
            </p>
            <p>
              <strong>Decore AI changes this paradigm.</strong> We anchor state-of-the-art vision models directly to a verified multi-vendor marketplace. When our AI envisions a Scandinavian living room, every sofa, rug, lamp, and wallpaper in the rendering is a real item you can purchase.
            </p>
          </div>
        </div>
      </section>

      {/* 3. HOW AI HELPS INTERIOR DESIGN */}
      <section className="section-container how-ai-helps-section">
        <div className="section-header">
          <span className="section-sub">Technological Architecture</span>
          <h2 className="section-title">How AI Powers Every Design Decision</h2>
          <p className="section-desc">
            We blend computer vision, multi-modal neural embeddings, and vector databases into a unified, lightning-fast design pipeline.
          </p>
        </div>

        <div className="feature-cards-grid">
          {FEATURE_CARDS.map((card) => (
            <div key={card.title} className="feature-card">
              <div className="feature-icon">{card.icon}</div>
              <h3>{card.title}</h3>
              <p>{card.description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* 4. WHY WE BUILT DECORE AI */}
      <section className="section-container why-built-section">
        <div className="why-built-box">
          <div className="why-built-content">
            <span className="section-sub">Our Philosophy</span>
            <h2>Why We Built Decore AI</h2>
            <p>
              We believe beautiful living spaces should be accessible to everyone — not just those who can afford high-end interior designer retainers.
            </p>
            <div className="principles-grid">
              <div className="principle-item">
                <strong>1. Grounded in Reality</strong>
                <p>No hallucinated furniture. Only authentic products from verified sellers.</p>
              </div>
              <div className="principle-item">
                <strong>2. Complete Financial Clarity</strong>
                <p>Real-time calculation against user budget prevents unexpected surprise bills.</p>
              </div>
              <div className="principle-item">
                <strong>3. Speed and Empowerment</strong>
                <p>Redesign in minutes from any device, iterating across multiple styles with zero pressure.</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 5. CTA */}
      <section className="section-container cta-section" style={{ marginBottom: 40 }}>
        <div className="cta-banner">
          <div className="cta-content">
            <h2>Experience Decore AI in Action</h2>
            <p>Ready to see what your room looks like with AI-curated furniture?</p>
            <div className="cta-actions">
              <Link to="/decor" className="btn-cta-primary">
                Launch Decor AI Designer
              </Link>
              <Link to="/contact" className="btn-cta-secondary">
                Get in Touch
              </Link>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}
