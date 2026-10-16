import { useState } from 'react'

const FAQ_ITEMS = [
  {
    q: 'How does Decore AI analyze my room?',
    a: 'We use Groq Vision AI to analyze your uploaded room photograph. The model evaluates architectural lines, wall palettes, floor textures, ambient daylight, and existing furniture.',
  },
  {
    q: 'Are the recommended furniture items really available for purchase?',
    a: 'Yes! All recommended products come from registered seller catalogs stored in our Qdrant vector database. Each item includes authentic pricing, dimensions, and seller information.',
  },
  {
    q: 'How does the budget calculator work?',
    a: 'You set a total budget (e.g. ₹95,000). Decore AI allocates this across your chosen categories (sofas, tables, lighting, etc.) and retrieves candidate products that fit your financial boundary.',
  },
  {
    q: 'Can I register as a furniture seller or manufacturer?',
    a: 'Absolutely. Click on Register and select the "Seller" account type. You will get immediate access to the Seller Dashboard where you can upload product catalogs and images.',
  },
]

export default function ContactPage() {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    subject: 'General Inquiry',
    message: '',
  })
  const [submitted, setSubmitted] = useState(false)
  const [loading, setLoading] = useState(false)

  function handleChange(e) {
    const { name, value } = e.target
    setFormData((prev) => ({ ...prev, [name]: value }))
  }

  function handleSubmit(e) {
    e.preventDefault()
    setLoading(true)
    setTimeout(() => {
      setLoading(false)
      setSubmitted(true)
      setFormData({
        name: '',
        email: '',
        phone: '',
        subject: 'General Inquiry',
        message: '',
      })
    }, 600)
  }

  return (
    <div className="contact-page">
      {/* HERO */}
      <section className="contact-hero">
        <div className="section-container">
          <span className="section-sub">Get in Touch</span>
          <h1 className="contact-title">
            We’re Here to Help You <span className="highlight-text">Create Beautiful Spaces</span>
          </h1>
          <p className="contact-subtitle">
            Have questions about our AI design engine, product catalog integration, or seller onboarding? Reach out to our team.
          </p>
        </div>
      </section>

      <section className="section-container contact-main-section">
        <div className="contact-grid">
          {/* CONTACT INFO */}
          <div className="contact-info-panel">
            <h2>Contact Information</h2>
            <p className="muted">
              Connect directly with our customer support and vendor onboarding specialists.
            </p>

            <div className="contact-cards-list">
              <div className="contact-info-card">
                <div className="contact-icon">📧</div>
                <div>
                  <strong>Email Support</strong>
                  <p>support@decoreai.com</p>
                  <span className="muted">Fast response within 24 hours</span>
                </div>
              </div>

              <div className="contact-info-card">
                <div className="contact-icon">📞</div>
                <div>
                  <strong>Phone / WhatsApp</strong>
                  <p>+91 98765 43210</p>
                  <span className="muted">Mon – Sat, 9:00 AM – 7:00 PM IST</span>
                </div>
              </div>

              <div className="contact-info-card">
                <div className="contact-icon">📍</div>
                <div>
                  <strong>Headquarters</strong>
                  <p>Delhi NCR, India</p>
                  <span className="muted">Technology & Product Engineering Hub</span>
                </div>
              </div>
            </div>

            <div className="contact-seller-notice">
              <h4>Are you an Interior Furniture Seller?</h4>
              <p>
                List your products on our OpenCLIP vector catalog and reach thousands of homeowners designing with AI.
              </p>
              <a href="/register" className="btn-secondary small">
                Join as a Seller →
              </a>
            </div>
          </div>

          {/* CONTACT FORM */}
          <div className="contact-form-panel">
            <h2>Send Us a Message</h2>
            <p className="muted" style={{ marginBottom: 20 }}>
              Fill out the form below and our team will get back to you promptly.
            </p>

            {submitted && (
              <div className="alert-box success">
                <strong>Thank you! Your message has been sent successfully.</strong>
                <p>Our support team will review your inquiry and get in touch shortly.</p>
              </div>
            )}

            <form onSubmit={handleSubmit} className="contact-form">
              <div className="form-field">
                <label htmlFor="contact-name">Full Name *</label>
                <input
                  id="contact-name"
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleChange}
                  placeholder="e.g. Priya Sharma"
                  required
                />
              </div>

              <div className="form-row-2">
                <div className="form-field">
                  <label htmlFor="contact-email">Email Address *</label>
                  <input
                    id="contact-email"
                    type="email"
                    name="email"
                    value={formData.email}
                    onChange={handleChange}
                    placeholder="e.g. priya@example.com"
                    required
                  />
                </div>
                <div className="form-field">
                  <label htmlFor="contact-phone">Phone Number</label>
                  <input
                    id="contact-phone"
                    type="tel"
                    name="phone"
                    value={formData.phone}
                    onChange={handleChange}
                    placeholder="+91 9876543210"
                  />
                </div>
              </div>

              <div className="form-field">
                <label htmlFor="contact-subject">Inquiry Type</label>
                <select
                  id="contact-subject"
                  name="subject"
                  value={formData.subject}
                  onChange={handleChange}
                >
                  <option value="General Inquiry">General Inquiry</option>
                  <option value="AI Room Design Support">AI Room Design Support</option>
                  <option value="Seller / Catalog Partnership">Seller / Catalog Partnership</option>
                  <option value="Feedback & Feature Request">Feedback & Feature Request</option>
                </select>
              </div>

              <div className="form-field">
                <label htmlFor="contact-message">Your Message *</label>
                <textarea
                  id="contact-message"
                  name="message"
                  rows="5"
                  value={formData.message}
                  onChange={handleChange}
                  placeholder="Tell us how we can help you..."
                  required
                />
              </div>

              <button type="submit" className="btn-primary" disabled={loading}>
                {loading ? 'Sending Message...' : 'Submit Message'}
              </button>
            </form>
          </div>
        </div>
      </section>

      {/* FAQ SECTION */}
      <section className="section-container faq-section">
        <div className="section-header">
          <span className="section-sub">Frequently Asked Questions</span>
          <h2 className="section-title">Common Questions About Decore AI</h2>
        </div>

        <div className="faq-grid">
          {FAQ_ITEMS.map((item) => (
            <div key={item.q} className="faq-card">
              <h3>{item.q}</h3>
              <p>{item.a}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}
