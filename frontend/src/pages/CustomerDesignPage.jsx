import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../auth'
import { apiRequest, assetUrl, formatINR } from '../api'

const CATEGORY_OPTIONS = ['sofa', 'curtain', 'lighting', 'decor', 'bed', 'wallpaper', 'table', 'chair']
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

export default function CustomerDesignPage() {
  const { user, token, logout } = useAuth()

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
  }

  function toggleCategory(cat) {
    setCategories((prev) =>
      prev.includes(cat) ? prev.filter((c) => c !== cat) : [...prev, cat]
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
    setLoading('Analyzing room with Vision AI...')
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
      if (!res.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'Room analysis failed')
      setRoomAnalysis(data.room_analysis)
      setRoomImagePath(data.room_image_path)
      setRoomId(data.room_id || '')
      setInfo(data.message || 'Room analysis completed.')
    } catch (err) {
      setError(err.message)
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

    setLoading('Finding matching products...')
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
      setInfo(`Found ${(data.recommended_products || []).length} recommended products.`)
    } catch (err) {
      setError(err.message)
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
    setLoading('Preparing AI design...')
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
      setInfo(data.status_message || 'Design preparation ready.')
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading('')
    }
  }

  return (
    <div className="app">
      <header className="brand customer-top">
        <div>
          <h1>DECORE AI</h1>
          <p>Customer AI Interior Design Flow</p>
        </div>
        <div className="customer-nav">
          <span className="muted">{user?.name}</span>
          <Link className="btn ghost" to="/customer/design">Design</Link>
          <button className="btn ghost" type="button" onClick={logout}>Logout</button>
        </div>
      </header>

      {error && <div className="error">{error}</div>}
      {info && <div className="success">{info}</div>}
      {loading && <div className="muted">{loading}</div>}

      <section className="panel">
        <h2>Upload Room Image</h2>
        <div className="field">
          <label>Choose Image (living room, bedroom, kitchen, bathroom, etc.)</label>
          <input type="file" accept="image/jpeg,image/png,image/webp" onChange={onImageChange} />
        </div>
        {previewUrl && (
          <div className="preview">
            <img src={previewUrl} alt="Room preview" />
          </div>
        )}

        <div className="row" style={{ marginTop: 14 }}>
          <div className="field">
            <label>Budget (INR)</label>
            <input
              type="number"
              min="1"
              value={budget}
              onChange={(e) => setBudget(e.target.value)}
              placeholder="95000"
            />
          </div>
          <div className="field">
            <label>Style</label>
            <select value={style} onChange={(e) => setStyle(e.target.value)}>
              {STYLE_OPTIONS.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="field">
          <label>Categories</label>
          <div className="categories">
            {CATEGORY_OPTIONS.map((cat) => (
              <label key={cat}>
                <input
                  type="checkbox"
                  checked={categories.includes(cat)}
                  onChange={() => toggleCategory(cat)}
                />
                {cat.charAt(0).toUpperCase() + cat.slice(1)}
              </label>
            ))}
          </div>
        </div>

        <div className="actions">
          <button className="btn" type="button" onClick={analyzeRoom} disabled={!!loading || !imageFile}>
            Analyze Room
          </button>
          <button
            className="btn secondary"
            type="button"
            onClick={findProducts}
            disabled={!!loading || !roomAnalysis}
          >
            Find Matching Products
          </button>
        </div>
      </section>

      {roomAnalysis && (
        <section className="panel">
          <h2>Room Analysis</h2>
          {roomId && <p className="muted">Room ID: {roomId}</p>}

          {roomAnalysis.is_fallback && (
            <div style={{
              background: 'rgba(234, 179, 8, 0.12)',
              border: '1px solid rgba(234, 179, 8, 0.35)',
              borderRadius: '8px',
              padding: '10px 14px',
              marginBottom: '14px',
              color: '#ca8a04',
              fontSize: '0.88rem'
            }}>
              <strong>⚠️ Notice:</strong> Real Vision API key is not configured in <code>.env</code> (GROQ_API_KEY). Running in offline fallback mode with zero assumed furniture.
            </div>
          )}

          <div className="analysis-grid">
            <div>
              <strong>Room Type</strong>
              {formatAttr(roomAnalysis.room_type, 'Living Space')}
            </div>
            <div>
              <strong>Wall</strong>
              {formatAttr(roomAnalysis.wall_color_finish || roomAnalysis.wall_color, 'Neutral')}
            </div>
            <div>
              <strong>Floor</strong>
              {formatAttr(roomAnalysis.flooring_material || roomAnalysis.floor, 'Hardwood / Tile')}
            </div>
            <div>
              <strong>Lighting</strong>
              {formatAttr(roomAnalysis.lighting, 'Daylight')}
            </div>
            <div>
              <strong>Style</strong>
              {formatAttr(roomAnalysis.target_style || roomAnalysis.design_style || style, 'Undetermined')}
            </div>
            <div>
              <strong>Existing Furniture</strong>
              {formatFurniture(roomAnalysis.existing_furniture)}
            </div>
            <div>
              <strong>Dominant Colors</strong>
              {formatList(roomAnalysis.dominant_colors, 'Neutral Palette')}
            </div>
            <div>
              <strong>Features</strong>
              {formatList(roomAnalysis.architectural_features || roomAnalysis.room_features, 'Standard room layout')}
            </div>
          </div>
          {roomAnalysis.description && (
            <p style={{ marginTop: 12 }}>{roomAnalysis.description}</p>
          )}
        </section>
      )}

      {recommended.length > 0 && (
        <section className="panel">
          <h2>Recommended Products</h2>
          {searchQuery && <p className="muted">Search query: {searchQuery}</p>}

          <div className="budget-box">
            <div>
              <span>Your Budget</span>
              <strong>{formatINR(budget)}</strong>
            </div>
            <div>
              <span>Estimated Total (selected)</span>
              <strong>{formatINR(selectedTotal)}</strong>
            </div>
            <div>
              <span>Remaining</span>
              <strong>{formatINR(selectedRemaining)}</strong>
            </div>
            <div>
              <span>Status</span>
              <strong className={statusClass(selectedStatus)}>
                {statusLabel(selectedStatus)}
              </strong>
            </div>
          </div>

          {budgetMeta && (
            <p className="muted">
              Backend recommendation total: {formatINR(budgetMeta.estimated_total)} (
              {statusLabel(budgetMeta.budget_status)})
            </p>
          )}

          <div className="product-list">
            {recommended.map((product) => (
              <label className="product" key={product.product_id}>
                <input
                  type="checkbox"
                  checked={selectedIds.has(product.product_id)}
                  onChange={() => toggleProduct(product.product_id)}
                />
                <img
                  src={assetUrl(product.image_path)}
                  alt={product.name}
                  onError={(e) => {
                    e.currentTarget.style.visibility = 'hidden'
                  }}
                />
                <div>
                  <h3>{product.name}</h3>
                  <p className="price">{formatINR(product.price)}</p>
                  <p>Seller: {product.seller_id || 'SYSTEM'}</p>
                  <p>
                    Color: {product.color || '—'} · Material: {product.material || '—'}
                  </p>
                  <p>
                    Category: {product.category}
                    {product.score != null ? ` · Score: ${Number(product.score).toFixed(3)}` : ''}
                  </p>
                </div>
              </label>
            ))}
          </div>

          <div className="actions">
            <button className="btn" type="button" onClick={prepareDesign} disabled={!!loading}>
              Prepare AI Design
            </button>
          </div>
        </section>
      )}

      {prepareResult && (
        <section className="panel">
          <h2>Final Design Preparation</h2>
          <div className="budget-box">
            <div>
              <span>Budget</span>
              <strong>{formatINR(prepareResult.budget)}</strong>
            </div>
            <div>
              <span>Estimated Total</span>
              <strong>{formatINR(prepareResult.estimated_total)}</strong>
            </div>
            <div>
              <span>Remaining</span>
              <strong>{formatINR(prepareResult.budget_remaining)}</strong>
            </div>
            <div>
              <span>Status</span>
              <strong className={statusClass(prepareResult.budget_status)}>
                {statusLabel(prepareResult.budget_status)}
              </strong>
            </div>
          </div>

          <h3>Final Prompt</h3>
          <div className="prompt-box">{prepareResult.final_prompt}</div>

          <h3 style={{ marginTop: 16 }}>Reference Images</h3>
          <ul>
            {(prepareResult.reference_images || []).map((path) => (
              <li key={path}>{path}</li>
            ))}
          </ul>

          <h3>Image Generation</h3>
          <p>
            Provider: {prepareResult.image_generation?.provider || 'mock'} · Status:{' '}
            {prepareResult.image_generation?.status || 'ready'}
          </p>
          <p className="muted">{prepareResult.image_generation?.message || prepareResult.status_message}</p>
        </section>
      )}
    </div>
  )
}
