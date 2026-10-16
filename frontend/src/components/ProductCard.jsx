import { assetUrl, formatINR } from '../api'

export default function ProductCard({ product }) {
  return (
    <article className="product-card">
      <img src={assetUrl(product.image_path)} alt={product.name} />
      <div>
        <h3>{product.name}</h3>
        <p className="price">{formatINR(product.price)} {product.currency || 'INR'}</p>
        <p className="muted">{product.category}{product.subcategory ? ` · ${product.subcategory}` : ''}</p>
        <p className="muted">Stock: {product.stock} · {product.is_active ? 'Active' : 'Inactive'}</p>
      </div>
    </article>
  )
}
