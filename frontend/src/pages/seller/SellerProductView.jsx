import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { sellerApi, assetUrl, formatINR } from '../../api'
import { LoadingState } from '../../components/LoadingState'

export default function SellerProductView() {
  const { productId } = useParams()
  const [product, setProduct] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    async function load() {
      try {
        const data = await sellerApi.getProduct(productId)
        if (!cancelled) setProduct(data)
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
  }, [productId])

  if (loading) return <LoadingState label="Loading product..." />
  if (error) return <div className="error">{error}</div>
  if (!product) return null

  return (
    <div className="panel">
      <div className="page-head">
        <h2>{product.name}</h2>
        <Link className="btn" to={`/seller/products/${product.product_id}/edit`}>Edit</Link>
      </div>
      <img className="detail-img" src={assetUrl(product.image_path)} alt="" />
      <p className="muted">{product.product_id}</p>
      <p>{product.description}</p>
      <p>Category: {product.category} {product.subcategory ? `/ ${product.subcategory}` : ''}</p>
      <p>Price: {formatINR(product.price)} {product.currency}</p>
      <p>Stock: {product.stock} · {product.is_active ? 'Active' : 'Inactive'}</p>
      <p>Color: {product.color} · Material: {product.material}</p>
      <p>Style: {Array.isArray(product.style) ? product.style.join(', ') : product.style}</p>
      <p>Dimensions: {product.dimensions || '—'}</p>
    </div>
  )
}
