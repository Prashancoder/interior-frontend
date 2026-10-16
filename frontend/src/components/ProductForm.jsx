import { useEffect, useState } from 'react'

export const PRODUCT_CATEGORIES = [
  'sofa',
  'chair',
  'table',
  'ottoman',
  'bed',
  'curtain',
  'cushion',
  'rug',
  'lighting',
  'plant',
  'planter',
  'painting',
  'mirror',
  'decor',
  'wallpaper',
]

const EMPTY = {
  name: '',
  description: '',
  category: 'sofa',
  subcategory: '',
  price: '',
  currency: 'INR',
  stock: '1',
  color: '',
  material: '',
  style: 'modern',
  dimensions: '',
  is_active: true,
}

const ALLOWED_TYPES = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp']

export default function ProductForm({
  mode = 'create',
  initialProduct,
  submitting,
  error,
  onSubmit,
}) {
  const [form, setForm] = useState(EMPTY)
  const [file, setFile] = useState(null)
  const [preview, setPreview] = useState('')
  const [dragOver, setDragOver] = useState(false)
  const [localError, setLocalError] = useState('')

  useEffect(() => {
    if (!initialProduct) return
    setForm({
      name: initialProduct.name || '',
      description: initialProduct.description || '',
      category: initialProduct.category || 'sofa',
      subcategory: initialProduct.subcategory || '',
      price: initialProduct.price ?? '',
      currency: initialProduct.currency || 'INR',
      stock: initialProduct.stock ?? '1',
      color: initialProduct.color || '',
      material: initialProduct.material || '',
      style: Array.isArray(initialProduct.style)
        ? initialProduct.style.join(', ')
        : initialProduct.style || '',
      dimensions: initialProduct.dimensions || '',
      is_active: Boolean(initialProduct.is_active),
    })
    if (initialProduct.image_path) {
      setPreview(`/${String(initialProduct.image_path).replace(/^\/+/, '')}`)
    }
  }, [initialProduct])

  function setField(key, value) {
    setForm((prev) => ({ ...prev, [key]: value }))
  }

  function acceptFile(nextFile) {
    if (!nextFile) return
    if (!ALLOWED_TYPES.includes(nextFile.type) && !/\.(jpe?g|png|webp)$/i.test(nextFile.name)) {
      setLocalError('Please upload a JPEG, PNG, or WEBP image.')
      return
    }
    if (nextFile.size > 10 * 1024 * 1024) {
      setLocalError('Image must be 10MB or smaller.')
      return
    }
    setLocalError('')
    setFile(nextFile)
    setPreview(URL.createObjectURL(nextFile))
  }

  function handleDrop(e) {
    e.preventDefault()
    setDragOver(false)
    acceptFile(e.dataTransfer.files?.[0])
  }

  function handleSubmit(e) {
    e.preventDefault()
    setLocalError('')
    if (!form.name.trim() || form.name.trim().length < 2) {
      setLocalError('Product name is required.')
      return
    }
    if (!form.category) {
      setLocalError('Category is required.')
      return
    }
    if (!form.price || Number(form.price) <= 0) {
      setLocalError('Price must be greater than 0.')
      return
    }
    if (!form.color.trim() || !form.material.trim() || !form.style.trim()) {
      setLocalError('Color, material, and style are required.')
      return
    }
    if (mode === 'create' && !file) {
      setLocalError('Please upload a product image.')
      return
    }

    const data = new FormData()
    data.append('name', form.name.trim())
    data.append('category', form.category)
    data.append('subcategory', form.subcategory.trim())
    data.append('description', form.description.trim())
    data.append('price', String(form.price))
    data.append('currency', form.currency || 'INR')
    data.append('color', form.color.trim())
    data.append('material', form.material.trim())
    data.append('style', form.style.trim())
    data.append('dimensions', form.dimensions.trim())
    data.append('stock', String(form.stock ?? 0))
    data.append('is_active', form.is_active ? 'true' : 'false')
    if (file) data.append('file', file)
    onSubmit(data)
  }

  return (
    <form className="panel" onSubmit={handleSubmit}>
      {(localError || error) && <div className="error">{localError || error}</div>}

      <div
        className={`dropzone ${dragOver ? 'over' : ''}`}
        onDragOver={(e) => {
          e.preventDefault()
          setDragOver(true)
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
      >
        <p>Drag and drop a product image, or choose a file.</p>
        <input
          type="file"
          accept="image/jpeg,image/png,image/webp"
          onChange={(e) => acceptFile(e.target.files?.[0])}
        />
        {preview && (
          <div className="preview">
            <img src={preview} alt="Product preview" />
          </div>
        )}
      </div>

      <div className="auth-grid" style={{ marginTop: 16 }}>
        <div className="field">
          <label>Product name</label>
          <input value={form.name} onChange={(e) => setField('name', e.target.value)} required />
        </div>
        <div className="field">
          <label>Category</label>
          <select value={form.category} onChange={(e) => setField('category', e.target.value)}>
            {PRODUCT_CATEGORIES.map((cat) => (
              <option key={cat} value={cat}>
                {cat}
              </option>
            ))}
          </select>
        </div>
        <div className="field">
          <label>Subcategory</label>
          <input
            value={form.subcategory}
            onChange={(e) => setField('subcategory', e.target.value)}
            placeholder="e.g. coffee table, floor lamp"
          />
        </div>
        <div className="field">
          <label>Price (INR)</label>
          <input
            type="number"
            min="1"
            step="0.01"
            value={form.price}
            onChange={(e) => setField('price', e.target.value)}
            required
          />
        </div>
        <div className="field">
          <label>Currency</label>
          <input value={form.currency} onChange={(e) => setField('currency', e.target.value)} />
        </div>
        <div className="field">
          <label>Stock</label>
          <input
            type="number"
            min="0"
            value={form.stock}
            onChange={(e) => setField('stock', e.target.value)}
          />
        </div>
        <div className="field">
          <label>Color</label>
          <input value={form.color} onChange={(e) => setField('color', e.target.value)} required />
        </div>
        <div className="field">
          <label>Material</label>
          <input value={form.material} onChange={(e) => setField('material', e.target.value)} required />
        </div>
        <div className="field">
          <label>Style</label>
          <input
            value={form.style}
            onChange={(e) => setField('style', e.target.value)}
            placeholder="modern, contemporary"
            required
          />
        </div>
        <div className="field">
          <label>Dimensions</label>
          <input
            value={form.dimensions}
            onChange={(e) => setField('dimensions', e.target.value)}
            placeholder="e.g. 180x80x75 cm"
          />
        </div>
        <div className="field">
          <label>Status</label>
          <label className="inline-check">
            <input
              type="checkbox"
              checked={form.is_active}
              onChange={(e) => setField('is_active', e.target.checked)}
            />
            Active in catalog
          </label>
        </div>
      </div>

      <div className="field" style={{ marginTop: 12 }}>
        <label>Description</label>
        <textarea
          rows={4}
          value={form.description}
          onChange={(e) => setField('description', e.target.value)}
        />
      </div>

      <div className="actions">
        <button className="btn" type="submit" disabled={submitting}>
          {submitting ? 'Saving...' : mode === 'create' ? 'Create Product' : 'Save Changes'}
        </button>
      </div>
    </form>
  )
}
