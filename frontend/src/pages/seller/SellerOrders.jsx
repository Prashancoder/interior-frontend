import EmptyState from '../../components/EmptyState'

export default function SellerOrders() {
  return (
    <div>
      <h2>Orders</h2>
      <EmptyState
        title="Orders coming soon"
        message="No seller order APIs are available in the backend yet. This page is a placeholder."
      />
    </div>
  )
}
