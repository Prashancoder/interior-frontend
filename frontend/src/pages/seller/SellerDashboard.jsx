import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { sellerApi, assetUrl, formatINR } from '../../api'
import { LoadingState, SkeletonCards } from '../../components/LoadingState'

function StatCard({ label, value, hint, accent = false }) {
  return (
    <div className={`stat-card ${accent ? 'stat-card-accent' : ''}`}>
      <span>{label}</span>
      <strong>{value}</strong>
      {hint && <small className="muted">{hint}</small>}
    </div>
  )
}

export default function SellerDashboard() {
  const [stats, setStats] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    async function load() {
      try {
        const data = await sellerApi.stats()
        if (!cancelled) setStats(data)
      } catch (err) {
        if (!cancelled) setError(err.message)
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    load()
    return () => {
      cancelled = true
    }
  }, [])

  if (loading) {
    return (
      <div>
        <div className="page-head">
          <h2>Seller Dashboard</h2>
        </div>
        <SkeletonCards count={3} />
        <LoadingState label="Loading seller stats..." />
      </div>
    )
  }

  return (
    <div>
      <div className="page-head">
        <div>
          <h2>Seller Dashboard</h2>
          <p className="muted" style={{ margin: 0 }}>
            Manage ready-to-deliver interior inventory and track catalog status
          </p>
        </div>
        <div className="actions" style={{ margin: 0 }}>
          <Link className="btn" to="/seller/products/new">
            + Add Product
          </Link>
          <Link className="btn ghost" to="/seller/products">
            View All Products
          </Link>
        </div>
      </div>

      {error && <div className="error">{error}</div>}

      {stats && (
        <div className="stat-grid">
          {'total_products' in stats && (
            <StatCard
              label="Total Products"
              value={stats.total_products}
              hint="In your store catalog"
              accent
            />
          )}
          {'active_products' in stats && (
            <StatCard
              label="Active in Catalog"
              value={stats.active_products}
              hint="Indexed & available for AI matching"
            />
          )}
          {'out_of_stock_products' in stats && (
            <StatCard
              label="Out of Stock"
              value={stats.out_of_stock_products}
              hint={stats.out_of_stock_products > 0 ? 'Requires restocking' : 'All items in stock'}
            />
          )}
          {'total_orders' in stats && (
            <StatCard label="Total Orders" value={stats.total_orders} />
          )}
          {'revenue' in stats && (
            <StatCard label="Revenue" value={stats.revenue} />
          )}
        </div>
      )}

      <div className="auth-grid" style={{ marginBottom: 18 }}>
        <div className="panel quick-action-card">
          <h3>Quick Upload</h3>
          <p className="muted">
            Add sofas, tables, chairs, lamps, mirrors, rugs, or decor items directly to your catalog.
            Products are automatically indexed in Qdrant for AI design matching.
          </p>
          <Link className="btn" to="/seller/products/new">
            Add New Product
          </Link>
        </div>

        <div className="panel quick-action-card">
          <h3>Store Profile</h3>
          <p className="muted">
            Review your business details, contact information, and store identifier associated with your products.
          </p>
          <Link className="btn ghost" to="/seller/profile">
            View Profile
          </Link>
        </div>
      </div>

      <section className="panel">
        <div className="page-head" style={{ marginBottom: 12 }}>
          <h3 style={{ margin: 0 }}>Recent Products</h3>
          {stats?.recent_products?.length > 0 && (
            <Link to="/seller/products" className="link-btn">
              View All ({stats.total_products}) →
            </Link>
          )}
        </div>

        {stats?.recent_products?.length ? (
          <div className="card-grid">
            {stats.recent_products.map((product) => (
              <article className="product-card" key={product.product_id}>
                <img
                  src={assetUrl(product.image_path)}
                  alt={product.name}
                  onError={(e) => {
                    e.currentTarget.style.visibility = 'hidden'
                  }}
                />
                <div className="product-card-body">
                  <div className="product-card-head">
                    <h4>{product.name}</h4>
                    <span className={`pill ${product.is_active ? 'ok' : 'off'}`}>
                      {product.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </div>
                  <p className="price">
                    {formatINR(product.price)} {product.currency || 'INR'}
                  </p>
                  <p className="muted small">
                    {product.category}
                    {product.subcategory ? ` · ${product.subcategory}` : ''}
                  </p>
                  <p className="muted small">Stock: {product.stock} units</p>
                  <div className="actions" style={{ marginTop: 8 }}>
                    <Link
                      className="btn ghost small-btn"
                      to={`/seller/products/${product.product_id}/edit`}
                    >
                      Edit
                    </Link>
                    <Link
                      className="btn ghost small-btn"
                      to={`/seller/products/${product.product_id}`}
                    >
                      Details
                    </Link>
                  </div>
                </div>
              </article>
            ))}
          </div>
        ) : (
          <div className="empty-inline">
            <p className="muted">No products yet in your catalog.</p>
            <Link className="btn" to="/seller/products/new">
              Upload Your First Product
            </Link>
          </div>
        )}
      </section>
    </div>
  )
}
