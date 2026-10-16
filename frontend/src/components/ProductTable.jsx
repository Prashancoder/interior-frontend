import { Link } from 'react-router-dom'
import { assetUrl, formatINR } from '../api'

export default function ProductTable({ products, onDelete, onView }) {
  return (
    <div className="table-wrap">
      <table className="data-table">
        <thead>
          <tr>
            <th>Image</th>
            <th>Name</th>
            <th>Category</th>
            <th>Price</th>
            <th>Stock</th>
            <th>Status</th>
            <th>Product ID</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {products.map((product) => (
            <tr key={product.product_id}>
              <td>
                <img className="thumb" src={assetUrl(product.image_path)} alt="" />
              </td>
              <td>
                <strong>{product.name}</strong>
                <div className="muted small">{product.description || 'No description'}</div>
              </td>
              <td>{product.category}</td>
              <td>{formatINR(product.price)}</td>
              <td>{product.stock}</td>
              <td>
                <span className={`pill ${product.is_active ? 'ok' : 'off'}`}>
                  {product.is_active ? 'Active' : 'Inactive'}
                </span>
              </td>
              <td className="mono">{product.product_id}</td>
              <td className="table-actions">
                <button type="button" className="link-btn" onClick={() => onView(product)}>
                  View
                </button>
                <Link to={`/seller/products/${product.product_id}/edit`}>Edit</Link>
                <button type="button" className="link-btn danger-text" onClick={() => onDelete(product)}>
                  Delete
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
