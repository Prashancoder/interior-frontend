import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../auth'
import { apiRequest, assetUrl, formatINR } from '../api'

const CATEGORY_OPTIONS = [
  { id: 'sofa', label: 'Sofa & Lounges' },
  { id: 'curtain', label: 'Curtains & Drapes' },
  { id: 'lighting', label: 'Lighting' },
  { id: 'decor', label: 'Decor & Accents' },
  { id: 'bed', label: 'Beds' },
  { id: 'wallpaper', label: 'Wallpaper & Art' },
  { id: 'table', label: 'Tables' },
  { id: 'chair', label: 'Accent Chairs' },
]

const STYLE_OPTIONS = [
  'Modern Contemporary',
  'Minimalist',
  'Scandinavian',
  'Luxury Modern',
  'Industrial',
  'Classic',
]

function statusClass(status) {
  if (status === 'within_budget') return 'status-within'
  if (status === 'slightly_over_budget') return 'status-over'
  return 'status-exceeds'
}

function statusLabel(status) {
  if (status === 'within_budget') return 'Within Budget'
  if (status === 'slightly_over_budget') return 'Slightly Over Budget'
  return 'Exceeds Budget'
}

function formatAttr(val, fallback = 'Not clearly identifiable') {
  if (!val) return fallback
  const str = String(val).trim()
  if (['unknown', 'undetermined', 'null', 'none', '—', ''].includes(str.toLowerCase())) {
    return 'Not clearly identifiable'
  }
  return str
}

function formatFurniture(arr) {
  if (!arr || !Array.isArray(arr) || arr.length === 0) {
    return 'No major furniture detected'
  }
  const filtered = arr.filter(
    (item) => item && !['none', 'unknown', 'undetermined', '—', ''].includes(String(item).toLowerCase().trim())
  )
  return filtered.length > 0 ? filtered.join(', ') : 'No major furniture detected'
}

function formatList(arr, fallback = 'Not clearly identifiable') {
  if (!arr || !Array.isArray(arr) || arr.length === 0) {
    return fallback
  }
  const filtered = arr.filter(
    (item) => item && !['none', 'unknown', 'undetermined', '—', ''].includes(String(item).toLowerCase().trim())
  )
  return filtered.length > 0 ? filtered.join(', ') : fallback
}

export default function DecorPage() {
  const { user, token } = useAuth()

  const [imageFile, setImageFile] = useState(null)
  const [previewUrl, setPreviewUrl] = useState('')
  const [budget, setBudget] = useState('95000')
  const [style, setStyle] = useState('Modern Contemporary')
  const [categories, setCategories] = useState(['sofa', 'curtain', 'lighting', 'decor'])

  const [roomAnalysis, setRoomAnalysis] = useState(null)
  const [roomImagePath, setRoomImagePath] = useState('')
  const [roomId, setRoomId] = useState('')

  const [recommended, setRecommended] = useState([])
  const [selectedIds, setSelectedIds] = useState(new Set())
  const [searchQuery, setSearchQuery] = useState('')
  const [budgetMeta, setBudgetMeta] = useState(null)

  const [prepareResult, setPrepareResult] = useState(null)
  const [loading, setLoading] = useState('')
  const [error, setError] = useState('')
  const [info, setInfo] = useState('')

  const selectedProducts = useMemo(
    () => recommended.filter((p) => selectedIds.has(p.product_id)),
    [recommended, selectedIds]
  )

  const selectedTotal = useMemo(
    () => selectedProducts.reduce((sum, p) => sum + Number(p.price || 0), 0),
    [selectedProducts]
  )

  const selectedRemaining = Number(budget || 0) - selectedTotal
  const selectedStatus =
    selectedRemaining >= 0
      ? 'within_budget'
      : Math.abs(selectedRemaining) <= Number(budget || 0) * 0.2
        ? 'slightly_over_budget'
        : 'exceeds_budget'

  function authHeaders() {
    return token ? { Authorization: `Bearer ${token}` } : {}
  }

  function onImageChange(e) {
    const file = e.target.files?.[0]
    if (!file) return
    setImageFile(file)
    setPreviewUrl(URL.createObjectURL(file))
    setRoomAnalysis(null)
    setRecommended([])
    setSelectedIds(new Set())
    setPrepareResult(null)
    setBudgetMeta(null)
    setError('')
    setInfo('')
  }

  function toggleCategory(catId) {
    setCategories((prev) =>
      prev.includes(catId) ? prev.filter((c) => c !== catId) : [...prev, catId]
    )
  }

  async function analyzeRoom() {
    setError('')
    setInfo('')
    setPrepareResult(null)
    if (!imageFile) {
      setError('Please upload a room image first.')
      return
    }
    setLoading('Analyzing room with Groq Vision AI...')
    try {
      const form = new FormData()
      form.append('file', imageFile)
      form.append('style', style)
      const res = await fetch('/api/design/analyze-room', {
        method: 'POST',
        headers: { ...authHeaders() },
        body: form,
      })
      const data = await res.json()
      if (!res.ok) {
        throw new Error(typeof data.detail === 'string' ? data.detail : 'Room analysis failed')
      }
      setRoomAnalysis(data.room_analysis)
      setRoomImagePath(data.room_image_path)
      setRoomId(data.room_id || '')
      setInfo(data.message || 'Room analysis completed successfully via Vision AI.')
    } catch (err) {
      setError(err.message || 'Room analysis failed')
    } finally {
      setLoading('')
    }
  }

  async function findProducts() {
    setError('')
    setInfo('')
    setPrepareResult(null)
    if (!roomAnalysis) {
      setError('Analyze the room first.')
      return
    }
    if (!categories.length) {
      setError('Select at least one category.')
      return
    }
    const budgetNum = Number(budget)
    if (!budgetNum || budgetNum <= 0) {
      setError('Enter a valid budget.')
      return
    }

    setLoading('Retrieving catalog products with OpenCLIP & Qdrant...')
    try {
      const data = await apiRequest('/api/design/recommend-products', {
        method: 'POST',
        body: JSON.stringify({
          room_analysis: roomAnalysis,
          style,
          budget: budgetNum,
          categories,
          room_image_path: roomImagePath || null,
        }),
      })
      setRecommended(data.recommended_products || [])
      setSelectedIds(new Set((data.recommended_products || []).map((p) => p.product_id)))
      setSearchQuery(data.search_query || '')
      setBudgetMeta({
        budget: data.budget,
        estimated_total: data.estimated_total,
        budget_remaining: data.budget_remaining,
        budget_status: data.budget_status,
        categories_covered: data.categories_covered || [],
      })
      setInfo(`Found ${(data.recommended_products || []).length} matching catalog products.`)
    } catch (err) {
      setError(err.message || 'Product recommendation failed')
    } finally {
      setLoading('')
    }
  }

  function toggleProduct(productId) {
    setSelectedIds((prev) => {
      const next = new Set(prev)
      if (next.has(productId)) next.delete(productId)
      else next.add(productId)
      return next
    })
  }

  async function prepareDesign() {
    setError('')
    setInfo('')
    if (!roomAnalysis) {
      setError('Analyze the room first.')
      return
    }
    if (!selectedProducts.length) {
      setError('Select at least one product.')
      return
    }
    setLoading('Synthesizing dynamic AI interior prompt & reference assets...')
    try {
      const data = await apiRequest('/design/prepare', {
        method: 'POST',
        body: JSON.stringify({
          room_analysis: roomAnalysis,
          style,
          budget: Number(budget),
          categories,
          selected_products: selectedProducts,
          room_image_path: roomImagePath || null,
        }),
      })
      setPrepareResult(data)
      setInfo(data.status_message || 'Design prompt synthesized and ready for rendering.')
    } catch (err) {
      setError(err.message || 'Design prompt preparation failed')
    } finally {
      setLoading('')
    }
  }

  return (
    <div className="decor-page-wrapper">
      {/* DECOR HERO BANNER */}
      <section className="decor-header-hero">
        <div className="decor-header-container">
          <div className="decor-hero-badge">
            <span className="pill-dot" />
            <span>AI Interior Design Studio</span>
          </div>
          <h1>Design Your Room with AI</h1>
          <p>
            Upload a photo of your room and let AI create a personalized interior design using real products from our multi-vendor catalog.
          </p>
          {!user && (
            <div className="decor-guest-banner">
              <span>You are designing in Guest mode.</span>
              <Link to="/login" className="guest-login-link">
                Sign In to save designs to your profile →
              </Link>
            </div>
          )}
        </div>
      </section>

      <div className="decor-main-container">
        {/* Status Alerts */}
        {error && <div className="alert-box error">{error}</div>}
        {info && <div className="alert-box success">{info}</div>}
        {loading && (
          <div className="alert-box loading">
            <div className="spinner-small" />
            <span>{loading}</span>
          </div>
        )}

        {/* STEP 1: UPLOAD & CONFIGURATION */}
        <section className="decor-panel">
          <div className="panel-header">
            <div className="step-tag">Step 1</div>
            <h2>Upload Room Image & Preferences</h2>
          </div>

          <div className="decor-form-grid">
            <div className="decor-upload-col">
              <label className="input-label">Room Photo (Living room, bedroom, office, etc.)</label>
              <div className="upload-dropzone">
                <input
                  type="file"
                  id="room-image-input"
                  accept="image/jpeg,image/png,image/webp"
                  onChange={onImageChange}
                  className="file-input-hidden"
                />
                <label htmlFor="room-image-input" className="dropzone-label">
                  <div className="upload-icon">
                    <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                      <polyline points="17 8 12 3 7 8" />
                      <line x1="12" y1="3" x2="12" y2="15" />
                    </svg>
                  </div>
                  <strong>Click to upload room image</strong>
                  <span className="muted">Supports JPG, PNG, WEBP up to 10MB</span>
                </label>
              </div>

              {previewUrl && (
                <div className="room-preview-card">
                  <div className="preview-tag">Selected Room Preview</div>
                  <img src={previewUrl} alt="Uploaded Room Preview" className="room-preview-img" />
                </div>
              )}
            </div>

            <div className="decor-controls-col">
              <div className="field-group">
                <label className="input-label" htmlFor="budget-input">
                  Total Budget (INR)
                </label>
                <div className="input-with-prefix">
                  <span className="currency-prefix">₹</span>
                  <input
                    id="budget-input"
                    type="number"
                    min="1000"
                    step="1000"
                    value={budget}
                    onChange={(e) => setBudget(e.target.value)}
                    placeholder="95000"
                    className="styled-input"
                  />
                </div>
              </div>

              <div className="field-group">
                <label className="input-label" htmlFor="style-select">
                  Design Style & Mood
                </label>
                <select
                  id="style-select"
                  value={style}
                  onChange={(e) => setStyle(e.target.value)}
                  className="styled-select"
                >
                  {STYLE_OPTIONS.map((s) => (
                    <option key={s} value={s}>
                      {s}
                    </option>
                  ))}
                </select>
              </div>

              <div className="field-group">
                <label className="input-label">Product Categories to Include</label>
                <div className="category-checkbox-grid">
                  {CATEGORY_OPTIONS.map((cat) => (
                    <label
                      key={cat.id}
                      className={`cat-checkbox-card ${categories.includes(cat.id) ? 'checked' : ''}`}
                    >
                      <input
                        type="checkbox"
                        checked={categories.includes(cat.id)}
                        onChange={() => toggleCategory(cat.id)}
                      />
                      <span>{cat.label}</span>
                    </label>
                  ))}
                </div>
              </div>

              <div className="decor-action-row">
                <button
                  className="btn-primary"
                  type="button"
                  onClick={analyzeRoom}
                  disabled={Boolean(loading) || !imageFile}
                >
                  <span>1. Analyze Room with AI</span>
                </button>
                <button
                  className="btn-secondary"
                  type="button"
                  onClick={findProducts}
                  disabled={Boolean(loading) || !roomAnalysis}
                >
                  <span>2. Find Matching Products</span>
                </button>
              </div>
            </div>
          </div>
        </section>

        {/* STEP 2: ROOM ANALYSIS RESULTS */}
        {roomAnalysis && (
          <section className="decor-panel">
            <div className="panel-header">
              <div className="step-tag">Step 2</div>
              <h2>Vision AI Room Analysis</h2>
              {roomId && <span className="room-id-pill">ID: {roomId}</span>}
            </div>

            {roomAnalysis.is_fallback && (
              <div style={{
                background: 'rgba(234, 179, 8, 0.12)',
                border: '1px solid rgba(234, 179, 8, 0.35)',
                borderRadius: '8px',
                padding: '12px 16px',
                marginBottom: '16px',
                color: '#ca8a04',
                fontSize: '0.9rem',
                lineHeight: '1.4'
              }}>
                <strong>⚠️ Notice:</strong> Real AI Vision API key is not configured in <code>.env</code> (GROQ_API_KEY). Running in offline development fallback mode with zero assumed furniture.
              </div>
            )}

            <div className="analysis-summary-grid">
              <div className="analysis-card">
                <span className="analysis-label">Room Type</span>
                <strong>{formatAttr(roomAnalysis.room_type, 'Living Space')}</strong>
              </div>
              <div className="analysis-card">
                <span className="analysis-label">Wall Color / Finish</span>
                <strong>{formatAttr(roomAnalysis.wall_color_finish || roomAnalysis.wall_color, 'Neutral')}</strong>
              </div>
              <div className="analysis-card">
                <span className="analysis-label">Flooring Material</span>
                <strong>{formatAttr(roomAnalysis.flooring_material || roomAnalysis.floor, 'Hardwood / Tile')}</strong>
              </div>
              <div className="analysis-card">
                <span className="analysis-label">Natural & Ambient Lighting</span>
                <strong>{formatAttr(roomAnalysis.lighting, 'Daylight')}</strong>
              </div>
              <div className="analysis-card">
                <span className="analysis-label">Target Style</span>
                <strong>{formatAttr(roomAnalysis.target_style || roomAnalysis.design_style || style, 'Undetermined')}</strong>
              </div>
              <div className="analysis-card">
                <span className="analysis-label">Existing Elements</span>
                <strong>{formatFurniture(roomAnalysis.existing_furniture)}</strong>
              </div>
              <div className="analysis-card">
                <span className="analysis-label">Dominant Color Palette</span>
                <strong>{formatList(roomAnalysis.dominant_colors, 'Neutral Palette')}</strong>
              </div>
              <div className="analysis-card">
                <span className="analysis-label">Architectural Features</span>
                <strong>{formatList(roomAnalysis.architectural_features || roomAnalysis.room_features, 'Standard room layout')}</strong>
              </div>
            </div>

            {roomAnalysis.room_condition && (
              <div style={{ marginTop: 12, fontSize: '0.88rem', color: '#64748b' }}>
                <strong>Room Condition:</strong> <span style={{ textTransform: 'capitalize' }}>{roomAnalysis.room_condition}</span>
              </div>
            )}

            {roomAnalysis.description && (
              <div className="analysis-description-box">
                <strong>AI Architectural Assessment:</strong>
                <p>{roomAnalysis.description}</p>
              </div>
            )}
          </section>
        )}

        {/* STEP 3: RECOMMENDED PRODUCTS */}
        {recommended.length > 0 && (
          <section className="decor-panel">
            <div className="panel-header">
              <div className="step-tag">Step 3</div>
              <h2>Recommended Catalog Products</h2>
              <span className="results-count">{recommended.length} products found</span>
            </div>

            {searchQuery && (
              <div className="query-meta-box">
                <span className="meta-tag">OpenCLIP Semantic Query:</span>
                <code>{searchQuery}</code>
              </div>
            )}

            {/* Budget Calculation Summary Bar */}
            <div className="budget-status-bar">
              <div className="budget-stat">
                <span className="stat-label">Total Budget</span>
                <span className="stat-amount">{formatINR(budget)}</span>
              </div>
              <div className="budget-stat">
                <span className="stat-label">Selected Total</span>
                <span className="stat-amount">{formatINR(selectedTotal)}</span>
              </div>
              <div className="budget-stat">
                <span className="stat-label">Remaining Balance</span>
                <span className="stat-amount">{formatINR(selectedRemaining)}</span>
              </div>
              <div className="budget-stat">
                <span className="stat-label">Budget Status</span>
                <span className={`status-badge ${statusClass(selectedStatus)}`}>
                  {statusLabel(selectedStatus)}
                </span>
              </div>
            </div>

            {budgetMeta && (
              <p className="muted budget-footnote">
                Catalog optimizer covered {budgetMeta.categories_covered?.length || 0} categories with initial estimate of {formatINR(budgetMeta.estimated_total)}.
              </p>
            )}

            {/* Products Grid */}
            <div className="recommended-products-grid">
              {recommended.map((product) => (
                <label
                  key={product.product_id}
                  className={`product-selection-card ${selectedIds.has(product.product_id) ? 'selected' : ''}`}
                >
                  <div className="card-checkbox-header">
                    <input
                      type="checkbox"
                      checked={selectedIds.has(product.product_id)}
                      onChange={() => toggleProduct(product.product_id)}
                      className="product-check"
                    />
                    <span className="category-pill">{product.category}</span>
                  </div>

                  <div className="product-image-container">
                    <img
                      src={assetUrl(product.image_path)}
                      alt={product.name}
                      onError={(e) => {
                        e.currentTarget.style.display = 'none'
                      }}
                    />
                  </div>

                  <div className="product-card-body">
                    <h3 className="product-name">{product.name}</h3>
                    <div className="product-price">{formatINR(product.price)}</div>
                    <div className="product-specs">
                      <span>Color: {product.color || 'Standard'}</span>
                      <span>Material: {product.material || 'Standard'}</span>
                    </div>
                    <div className="product-seller-info">
                      <span>Seller: {product.seller_id || 'Decore Verified'}</span>
                      {product.score != null && (
                        <span className="similarity-score">
                          Score: {Number(product.score).toFixed(2)}
                        </span>
                      )}
                    </div>
                  </div>
                </label>
              ))}
            </div>

            <div className="decor-action-row" style={{ marginTop: 24 }}>
              <button
                className="btn-primary large"
                type="button"
                onClick={prepareDesign}
                disabled={Boolean(loading) || selectedProducts.length === 0}
              >
                <span>3. Generate Cohesive AI Design with Selected Items</span>
              </button>
            </div>
          </section>
        )}

        {/* STEP 4: FINAL DESIGN PREPARATION & GENERATION */}
        {prepareResult && (
          <section className="decor-panel design-ready-panel">
            <div className="panel-header">
              <div className="step-tag">Step 4</div>
              <h2>AI Interior Design Synthesis & Generation</h2>
            </div>

            <div className="budget-status-bar">
              <div className="budget-stat">
                <span className="stat-label">Budget</span>
                <span className="stat-amount">{formatINR(prepareResult.budget)}</span>
              </div>
              <div className="budget-stat">
                <span className="stat-label">Estimated Total</span>
                <span className="stat-amount">{formatINR(prepareResult.estimated_total)}</span>
              </div>
              <div className="budget-stat">
                <span className="stat-label">Remaining</span>
                <span className="stat-amount">{formatINR(prepareResult.budget_remaining)}</span>
              </div>
              <div className="budget-stat">
                <span className="stat-label">Status</span>
                <span className={`status-badge ${statusClass(prepareResult.budget_status)}`}>
                  {statusLabel(prepareResult.budget_status)}
                </span>
              </div>
            </div>

            <div className="design-synthesis-block">
              <h3 className="synthesis-title">Synthesized Generative Interior Prompt</h3>
              <div className="prompt-container">
                <pre>{prepareResult.final_prompt}</pre>
              </div>

              <h3 className="synthesis-title" style={{ marginTop: 20 }}>
                Referenced Catalog Products & Visual Assets
              </h3>
              <ul className="reference-asset-list">
                {(prepareResult.reference_images || []).map((path) => (
                  <li key={path}>
                    <code>{path}</code>
                  </li>
                ))}
              </ul>

              <div className="generation-status-box">
                <div className="gen-provider">
                  <strong>Provider:</strong> {prepareResult.image_generation?.provider || 'Decore AI Generation Engine'}
                </div>
                <div className="gen-state">
                  <strong>Status:</strong> {prepareResult.image_generation?.status || 'Ready'}
                </div>
                <p className="gen-msg">
                  {prepareResult.image_generation?.message || prepareResult.status_message}
                </p>
              </div>
            </div>
          </section>
        )}
      </div>
    </div>
  )
}
