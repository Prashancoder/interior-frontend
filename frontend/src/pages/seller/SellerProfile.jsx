import { useAuth } from '../../auth'

export default function SellerProfile() {
  const { user } = useAuth()

  return (
    <div>
      <div className="page-head">
        <div>
          <h2>Store Profile</h2>
          <p className="muted" style={{ margin: 0 }}>
            Authenticated seller credentials and store identity information
          </p>
        </div>
      </div>

      <div className="panel profile-hero-card">
        <div className="profile-badge-row">
          <div className="profile-avatar">
            {(user?.business_name || user?.name || 'S').charAt(0).toUpperCase()}
          </div>
          <div>
            <h3 style={{ margin: 0 }}>{user?.business_name || user?.name}</h3>
            <p className="muted" style={{ margin: '4px 0 0' }}>
              Registered Seller Account · Role: <span className="pill ok">seller</span>
            </p>
          </div>
        </div>
      </div>

      <section className="panel">
        <div className="page-head" style={{ marginBottom: 14 }}>
          <h3 style={{ margin: 0 }}>Account & Store Information</h3>
          <span className="pill">Read Only</span>
        </div>
        <div className="analysis-grid">
          <div>
            <strong>Seller Name</strong>
            {user?.name || '—'}
          </div>
          <div>
            <strong>Business / Brand Name</strong>
            {user?.business_name || '—'}
          </div>
          <div>
            <strong>Email Address</strong>
            {user?.email || '—'}
          </div>
          <div>
            <strong>Phone Number</strong>
            {user?.phone || '—'}
          </div>
          <div>
            <strong>Seller ID</strong>
            <span className="mono">{user?.user_id || '—'}</span>
          </div>
          <div>
            <strong>Account Status</strong>
            <span className={`pill ${user?.is_active !== false ? 'ok' : 'off'}`}>
              {user?.is_active !== false ? 'Active' : 'Inactive'}
            </span>
          </div>
          <div>
            <strong>Member Since</strong>
            {user?.created_at
              ? new Date(user.created_at).toLocaleDateString(undefined, {
                  year: 'numeric',
                  month: 'short',
                  day: 'numeric',
                })
              : 'Active Session'}
          </div>
          <div>
            <strong>Authentication</strong>
            JWT Bearer Signed
          </div>
        </div>
        <p className="muted small" style={{ marginTop: 16 }}>
          Note: Store profile fields are managed through the authentication service. Contact platform administrator for account detail updates.
        </p>
      </section>
    </div>
  )
}
