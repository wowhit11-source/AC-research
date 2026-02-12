export default function SearchBar({ value, onChange, onSubmit, loading, onDownloadExcel, hasResults, slug }) {
  return (
    <form className="search-bar" onSubmit={onSubmit}>
      <input
        type="text"
        className="search-bar__input"
        placeholder="Query (e.g. AAPL)"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={loading}
        autoFocus
      />
      <button type="submit" className="search-bar__btn" disabled={loading}>
        {loading ? 'Searching…' : 'Search'}
      </button>
      {hasResults && slug && (
        <button
          type="button"
          className="search-bar__btn search-bar__btn--secondary"
          onClick={onDownloadExcel}
          disabled={loading}
        >
          Download Excel
        </button>
      )}
    </form>
  );
}
