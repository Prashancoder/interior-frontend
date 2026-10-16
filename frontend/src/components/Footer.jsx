import { Link } from 'react-router-dom'

export default function Footer() {
  return (
    <footer className="global-footer">
      <div className="footer-container">
        <div className="footer-grid">
          <div className="footer-brand-col">
            <Link to="/" className="footer-logo">
              <div className="logo-icon small">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
                  <polyline points="9 22 9 12 15 12 15 22" />
                </svg>
              </div>
              <span>Decore<span className="logo-ai">AI</span></span>
            </Link>
            <p className="footer-desc">
              Transform your space with AI-driven interior styling powered by computer vision,
              multi-modal embeddings, and real furniture products from verified sellers.
            </p>
            <div className="footer-badges">
              <span className="tech-badge">Groq Vision AI</span>
              <span className="tech-badge">OpenCLIP Vectors</span>
              <span className="tech-badge">Qdrant Engine</span>
            </div>
          </div>

          <div className="footer-col">
            <h4 className="footer-heading">Navigation</h4>
            <ul className="footer-nav-list">
              <li><Link to="/">Home</Link></li>
              <li><Link to="/about">About Us</Link></li>
              <li><Link to="/decor">Decor AI Designer</Link></li>
              <li><Link to="/contact">Contact Support</Link></li>
            </ul>
          </div>

          <div className="footer-col">
            <h4 className="footer-heading">Catalog Categories</h4>
            <ul className="footer-nav-list">
              <li><Link to="/decor">Sofas & Lounges</Link></li>
              <li><Link to="/decor">Designer Beds</Link></li>
              <li><Link to="/decor">Curtains & Drapes</Link></li>
              <li><Link to="/decor">Ambient Lighting</Link></li>
              <li><Link to="/decor">Wallpapers & Art</Link></li>
              <li><Link to="/decor">Home Decor Items</Link></li>
            </ul>
          </div>

          <div className="footer-col">
            <h4 className="footer-heading">Portals & Contact</h4>
            <ul className="footer-nav-list">
              <li><Link to="/login">Sign In / Register</Link></li>
              <li><Link to="/seller/dashboard">Seller Portal</Link></li>
              <li><Link to="/admin/dashboard">Platform Admin</Link></li>
            </ul>
            <div className="footer-contact-info">
              <p><span>Email:</span> support@decoreai.com</p>
              <p><span>Phone:</span> +91 98765 43210</p>
              <p><span>Location:</span> Delhi NCR, India</p>
            </div>
          </div>
        </div>

        <div className="footer-bottom">
          <p>© {new Date().getFullYear()} Decore AI Technologies Inc. All rights reserved.</p>
          <div className="footer-bottom-links">
            <span>AI Interior Design System</span>
            <span>·</span>
            <span>Multi-Vendor Catalog</span>
          </div>
        </div>
      </div>
    </footer>
  )
}
