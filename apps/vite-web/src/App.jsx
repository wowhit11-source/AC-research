import { useState } from 'react';
import SearchBar from './components/SearchBar.jsx';
import ResultSection from './components/ResultSection.jsx';
import { postResearch, getResearchExcel } from './services/api.js';
import './App.css';

export default function App() {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [data, setData] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    const q = query.trim();
    if (!q) return;
    setError(null);
    setLoading(true);
    try {
      const res = await postResearch(q);
      setData(res);
    } catch (err) {
      const d = err.response?.data?.detail;
      setError(Array.isArray(d) ? d.map((x) => x.msg || JSON.stringify(x)).join(' ') : d || err.message || 'Request failed');
      setData(null);
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadExcel = async () => {
    const slug = data?.slug;
    if (!slug) return;
    setLoading(true);
    try {
      const blob = await getResearchExcel(slug);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `research_${slug}.xlsx`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      const d = err.response?.data?.detail;
      setError(Array.isArray(d) ? d.map((x) => x.msg || JSON.stringify(x)).join(' ') : d || err.message || 'Download failed');
    } finally {
      setLoading(false);
    }
  };

  const results = data?.results;
  const hasResults = Boolean(
    results?.sec?.items?.length ||
    results?.dart?.items?.length ||
    results?.youtube?.length ||
    results?.papers?.length
  );

  return (
    <div className="app">
      <header className="app__header">
        <h1 className="app__title">AC Research</h1>
        <SearchBar
          value={query}
          onChange={setQuery}
          onSubmit={handleSubmit}
          loading={loading}
          onDownloadExcel={handleDownloadExcel}
          hasResults={hasResults}
          slug={data?.slug}
        />
      </header>

      {loading && !data && (
        <div className="app__loading" aria-busy="true">
          <span className="spinner" /> Searching…
        </div>
      )}

      {error && (
        <div className="app__error" role="alert">
          {error}
        </div>
      )}

      {data && (
        <main className="app__main">
          <ResultSection title="SEC results" items={results?.sec?.items} />
          <ResultSection title="DART results" items={results?.dart?.items} />
          <ResultSection title="YouTube results" items={results?.youtube} />
          <ResultSection title="Papers" items={results?.papers} />
          {!hasResults && (
            <p className="app__empty">No results for this query.</p>
          )}
        </main>
      )}
    </div>
  );
}
