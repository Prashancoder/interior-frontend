import { useAuth } from '../../auth'
import EmptyState from '../../components/EmptyState'

export default function AdminDashboard() {
  const { user } = useAuth()

  return (
    <div>
      <div className="page-head">
        <div>
          <h2>Admin Dashboard</h2>
          <p className="muted" style={{ margin: 0 }}>
            Decore AI Platform Administration & System Architecture Status
          </p>
        </div>
        <div>
          <a
            className="btn ghost"
            href="http://127.0.0.1:8000/docs"
            target="_blank"
            rel="noopener noreferrer"
          >
            FastAPI Swagger Docs ↗
          </a>
        </div>
      </div>

      <div className="stat-grid">
        <div className="stat-card">
          <span>Backend Framework</span>
          <strong>FastAPI</strong>
          <small className="muted">v2.0.0 · Port 8000</small>
        </div>
        <div className="stat-card">
          <span>Vector Database</span>
          <strong>Qdrant</strong>
          <small className="muted">Collection: interior_products</small>
        </div>
        <div className="stat-card">
          <span>Vision AI Model</span>
          <strong>Groq Vision</strong>
          <small className="muted">Llama 3.2 11B Vision</small>
        </div>
        <div className="stat-card">
          <span>Vector Embedding</span>
          <strong>OpenCLIP</strong>
          <small className="muted">ViT-B-32 (512-dim)</small>
        </div>
      </div>

      <section className="panel">
        <div className="page-head" style={{ marginBottom: 12 }}>
          <h3 style={{ margin: 0 }}>Administrator Session Details</h3>
          <span className="pill ok">Authorized Admin</span>
        </div>
        <div className="analysis-grid">
          <div>
            <strong>Admin Name</strong>
            {user?.name || 'Administrator'}
          </div>
          <div>
            <strong>Email</strong>
            {user?.email || '—'}
          </div>
          <div>
            <strong>Role</strong>
            <span className="pill ok">{user?.role || 'admin'}</span>
          </div>
          <div>
            <strong>Admin ID</strong>
            <span className="mono">{user?.user_id || '—'}</span>
          </div>
          <div>
            <strong>Access Level</strong>
            Platform Full Access
          </div>
          <div>
            <strong>Token Status</strong>
            Active JWT Session
          </div>
        </div>
      </section>

      <section className="panel">
        <h3>Backend Integration & Admin API Status</h3>
        <p className="muted">
          Decore AI is currently operating with core multi-vendor Seller Management and Customer Vision AI flows.
          Admin-specific platform management endpoints can be connected as backend microservices expand.
        </p>

        <div className="table-wrap" style={{ marginTop: 14 }}>
          <table className="data-table">
            <thead>
              <tr>
                <th>Module</th>
                <th>Active Backend Endpoints</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td><strong>Authentication</strong></td>
                <td>POST /api/auth/login, POST /api/auth/register, GET /api/auth/me</td>
                <td><span className="pill ok">Operational</span></td>
              </tr>
              <tr>
                <td><strong>Seller Catalog</strong></td>
                <td>POST /api/seller/products, GET /api/seller/products, GET /api/seller/stats, PUT/DELETE</td>
                <td><span className="pill ok">Operational</span></td>
              </tr>
              <tr>
                <td><strong>Customer AI Vision</strong></td>
                <td>POST /api/design/analyze-room, POST /api/design/recommend-products, POST /design/prepare</td>
                <td><span className="pill ok">Operational</span></td>
              </tr>
              <tr>
                <td><strong>Admin Management</strong></td>
                <td>Dedicated Admin CRUD Endpoints (/api/admin/*)</td>
                <td><span className="pill off">Planned in Backend</span></td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </div>
  )
}

export function AdminPlaceholder({ title, resource }) {
  return (
    <div>
      <div className="page-head">
        <h2>{title}</h2>
      </div>
      <EmptyState
        title={`${resource} Management`}
        message={`There are no dedicated /api/admin/${resource.toLowerCase()} endpoints currently registered in the FastAPI backend. This console page is ready to connect as soon as admin routes are added.`}
        action={
          <a
            className="btn ghost"
            href="http://127.0.0.1:8000/docs"
            target="_blank"
            rel="noopener noreferrer"
          >
            Check Swagger Documentation
          </a>
        }
      />
    </div>
  )
}
