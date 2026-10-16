export function LoadingState({ label = 'Loading...' }) {
  return (
    <div className="loading-state">
      <div className="spinner" />
      <p>{label}</p>
    </div>
  )
}

export function SkeletonCards({ count = 3 }) {
  return (
    <div className="stat-grid">
      {Array.from({ length: count }).map((_, i) => (
        <div className="stat-card skeleton" key={i}>
          <div className="skel-line" />
          <div className="skel-line short" />
        </div>
      ))}
    </div>
  )
}
