import { Navigate, Route, Routes } from 'react-router-dom'
import ProtectedRoute from './components/ProtectedRoute'
import DashboardLayout from './components/DashboardLayout'
import PublicLayout from './components/PublicLayout'
import HomePage from './pages/HomePage'
import AboutPage from './pages/AboutPage'
import DecorPage from './pages/DecorPage'
import ContactPage from './pages/ContactPage'
import LoginPage from './pages/LoginPage'
import SellerDashboard from './pages/seller/SellerDashboard'
import SellerProducts from './pages/seller/SellerProducts'
import SellerProductFormPage from './pages/seller/SellerProductFormPage'
import SellerProductView from './pages/seller/SellerProductView'
import SellerOrders from './pages/seller/SellerOrders'
import SellerProfile from './pages/seller/SellerProfile'
import AdminDashboard, { AdminPlaceholder } from './pages/admin/AdminPages'
import './App.css'
import './dashboard.css'

export default function App() {
  return (
    <Routes>
      {/* Public Pages wrapped with Global Navbar and Footer */}
      <Route element={<PublicLayout />}>
        <Route path="/" element={<HomePage />} />
        <Route path="/about" element={<AboutPage />} />
        <Route path="/decor" element={<DecorPage />} />
        <Route path="/contact" element={<ContactPage />} />
      </Route>

      {/* Backward Compatibility for legacy /customer/design route */}
      <Route path="/customer/design" element={<Navigate to="/decor" replace />} />
      <Route path="/customer" element={<Navigate to="/decor" replace />} />

      {/* Authentication */}
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<LoginPage />} />

      {/* Protected Seller Portal */}
      <Route
        path="/seller"
        element={
          <ProtectedRoute roles={['seller']}>
            <DashboardLayout role="seller" />
          </ProtectedRoute>
        }
      >
        <Route path="dashboard" element={<SellerDashboard />} />
        <Route path="products" element={<SellerProducts />} />
        <Route path="products/new" element={<SellerProductFormPage />} />
        <Route path="products/:productId" element={<SellerProductView />} />
        <Route path="products/:productId/edit" element={<SellerProductFormPage />} />
        <Route path="orders" element={<SellerOrders />} />
        <Route path="profile" element={<SellerProfile />} />
      </Route>

      {/* Protected Admin Console */}
      <Route
        path="/admin"
        element={
          <ProtectedRoute roles={['admin']}>
            <DashboardLayout role="admin" />
          </ProtectedRoute>
        }
      >
        <Route path="dashboard" element={<AdminDashboard />} />
        <Route path="products" element={<AdminPlaceholder title="Products" resource="Admin products" />} />
        <Route path="sellers" element={<AdminPlaceholder title="Sellers" resource="Sellers" />} />
        <Route path="customers" element={<AdminPlaceholder title="Customers" resource="Customers" />} />
        <Route path="orders" element={<AdminPlaceholder title="Orders" resource="Orders" />} />
        <Route path="settings" element={<AdminPlaceholder title="Settings" resource="Settings" />} />
      </Route>

      {/* Fallback to Public Homepage */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
