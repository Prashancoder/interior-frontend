import { useEffect, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { sellerApi, assetUrl, formatINR } from '../../api'
import ConfirmModal from '../../components/ConfirmModal'
import EmptyState from '../../components/EmptyState'
import { LoadingState } from '../../components/LoadingState'
import ProductTable from '../../components/ProductTable'
import { PRODUCT_CATEGORIES } from '../../components/ProductForm'

export default function SellerProducts() {
  const location = useLocation()
  const [products, setProducts] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [info, setInfo] = useState(location.state?.message || '')
  const [pending, setPending] = useState(null)
  const [busy, setBusy] = useState(false)
  const [viewing, setViewing] = useState(null)

  const [search, setSearch] = useState('')
  const [category, setCategory] = useState('')
  const [inStockOnly, setInStockOnly] = useState(false)

  async function load() {
    setLoading(true)
    setError('')
    try {
      const params = {}
      if (search.trim()) params.search = search.trim()
      if (category) params.category = category
      if (inStockOnly) params.in_stock = true
      const data = await sellerApi.listProducts(params)
      setProducts(Array.isArray(data) ? data : [])
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [category, inStockOnly])

  function handleSearchSubmit(e) {
    e.preventDefault()
    load()
  }

  async function confirmDelete() {
    if (!pending) return
    setBusy(true)
    try {
      await sellerApi.deleteProduct(pending.product_id)
      setInfo(`Deleted ${pending.name} (${pending.product_id})`)
      setPending(null)
      await load()
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div>
      <div className="page-head">
        <h2>Seller Products</h2>
        <Link className="btn" to="/seller/products/new">
          + Add Product
        </Link>
      </div>

      {error && <div className="error">{error}</div>}
      {info && <div className="success">{info}</div>}

      <div className="panel filter-bar">
        <form onSubmit={handleSearchSubmit} className="search-row">
          <div className="field search-field">
            <input
              type="text"
              placeholder="Search product name..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <div className="field category-field">
            <select value={category} onChange={(e) => setCategory(e.target.value)}>
              <option value="">All Categories</option>
              {PRODUCT_CATEGORIES.map((cat) => (
                <option key={cat} value={cat}>
                  {cat.charAt(0).toUpperCase() + cat.slice(1)}
                </option>
              ))}
            </select>
          </div>
          <label className="inline-check stock-check">
            <input
              type="checkbox"
              checked={inStockOnly}
              onChange={(e) => setInStockOnly(e.target.checked)}
            />
            In Stock Only
          </label>
          <button type="submit" className="btn ghost">
            Search
          </button>
          {(search || category || inStockOnly) && (
            <button
              type="button"
              className="btn ghost"
              onClick={() => {
                setSearch('')
                setCategory('')
                setInStockOnly(false)
              }}
            >
              Reset
            </button>
          )}
        </form>
      </div>

      {loading ? (
        <LoadingState label="Loading products..." />
      ) : products.length === 0 ? (
        <EmptyState
          title="No products found"
          message={
            search || category || inStockOnly
              ? 'No products matched your search or filters.'
              : 'Add your first ready-to-deliver interior product to your catalog.'
          }
          action={
            <Link className="btn" to="/seller/products/new">
              Add Product
            </Link>
          }
        />
      ) : (
        <ProductTable products={products} onDelete={setPending} onView={setViewing} />
      )}

      <ConfirmModal
        open={Boolean(pending)}
        title="Delete product?"
        message={
          pending
            ? `This will permanently remove "${pending.name}" (${pending.product_id}) and remove its vector from Qdrant.`
            : ''
        }
        onCancel={() => setPending(null)}
        onConfirm={confirmDelete}
        busy={busy}
      />

      {viewing && (
        <div className="modal-backdrop" onClick={() => setViewing(null)}>
          <div className="modal-card wide" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>{viewing.name}</h3>
              <span className="mono">{viewing.product_id}</span>
            </div>
            <img className="detail-img" src={assetUrl(viewing.image_path)} alt={viewing.name} />
            <p className="product-desc">{viewing.description || 'No description provided.'}</p>
            <div className="analysis-grid" style={{ marginTop: 14 }}>
              <div>
                <strong>Category</strong>
                {viewing.category} {viewing.subcategory ? `· ${viewing.subcategory}` : ''}
              </div>
              <div>
                <strong>Price</strong>
                {formatINR(viewing.price)} {viewing.currency || 'INR'}
              </div>
              <div>
                <strong>Stock</strong>
                {viewing.stock} units
              </div>
              <div>
                <strong>Status</strong>
                <span className={`pill ${viewing.is_active ? 'ok' : 'off'}`}>
                  {viewing.is_active ? 'Active in Catalog' : 'Inactive'}
                </span>
              </div>
              <div>
                <strong>Color</strong>
                {viewing.color || '—'}
              </div>
              <div>
                <strong>Material</strong>
                {viewing.material || '—'}
              </div>
              <div>
                <strong>Style</strong>
                {Array.isArray(viewing.style) ? viewing.style.join(', ') : viewing.style || '—'}
              </div>
              <div>
                <strong>Dimensions</strong>
                {viewing.dimensions || '—'}
              </div>
            </div>
            <div className="actions" style={{ marginTop: 18 }}>
              <Link className="btn" to={`/seller/products/${viewing.product_id}/edit`}>
                Edit Product
              </Link>
              <button type="button" className="btn ghost" onClick={() => setViewing(null)}>
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
