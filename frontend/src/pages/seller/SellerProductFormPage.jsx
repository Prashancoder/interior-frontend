import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { sellerApi } from '../../api'
import ProductForm from '../../components/ProductForm'
import { LoadingState } from '../../components/LoadingState'

export default function SellerProductFormPage() {
  const { productId } = useParams()
  const isEdit = Boolean(productId)
  const navigate = useNavigate()
  const [product, setProduct] = useState(null)
  const [loading, setLoading] = useState(isEdit)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!isEdit) return
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
  }, [isEdit, productId])

  async function handleSubmit(formData) {
    setSubmitting(true)
    setError('')
    try {
      if (isEdit) {
        await sellerApi.updateProduct(productId, formData)
        navigate('/seller/products', { state: { message: 'Product updated.' } })
      } else {
        await sellerApi.createProduct(formData)
        navigate('/seller/products', { state: { message: 'Product created and indexed.' } })
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) return <LoadingState label="Loading product..." />

  return (
    <div>
      <div className="page-head">
        <h2>{isEdit ? 'Edit Product' : 'Add Product'}</h2>
      </div>
      <ProductForm
        mode={isEdit ? 'edit' : 'create'}
        initialProduct={product}
        submitting={submitting}
        error={error}
        onSubmit={handleSubmit}
      />
    </div>
  )
}
