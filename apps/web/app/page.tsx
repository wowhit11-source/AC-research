'use client';

import { useCallback, useState } from 'react';

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000';

type TabId = 'dart' | 'sec' | 'youtube' | 'papers';

interface ResearchMeta {
  elapsed_ms: number;
  errors: { source: string; message: string }[];
}

interface ResearchResponse {
  query: string;
  slug: string;
  results: {
    dart: { items: Record<string, unknown>[] } | null;
    sec: { items: Record<string, unknown>[] } | null;
    youtube: Record<string, unknown>[];
    papers: Record<string, unknown>[];
  };
  meta: ResearchMeta;
}

export default function Home() {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<ResearchResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<TabId>('sec');

  const search = useCallback(async () => {
    const q = query.trim();
    if (!q) return;
    setLoading(true);
    setError(null);
    setData(null);
    try {
      const res = await fetch(`${BACKEND_URL}/api/research`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: q }),
      });
      if (!res.ok) {
        const t = await res.text();
        throw new Error(t || `HTTP ${res.status}`);
      }
      const json: ResearchResponse = await res.json();
      setData(json);
      if (json.results.dart?.items?.length) setTab('dart');
      else if (json.results.sec?.items?.length) setTab('sec');
      else if (json.results.youtube?.length) setTab('youtube');
      else if (json.results.papers?.length) setTab('papers');
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }, [query]);

  const downloadExcel = useCallback(() => {
    if (!data?.slug) return;
    const url = `${BACKEND_URL}/api/research/${encodeURIComponent(data.slug)}/excel`;
    window.open(url, '_blank');
  }, [data?.slug]);

  const tabs: { id: TabId; label: string; count: number }[] = [
    { id: 'dart', label: 'DART', count: data?.results.dart?.items?.length ?? 0 },
    { id: 'sec', label: 'SEC', count: data?.results.sec?.items?.length ?? 0 },
    { id: 'youtube', label: 'YouTube', count: data?.results.youtube?.length ?? 0 },
    { id: 'papers', label: 'Papers', count: data?.results.papers?.length ?? 0 },
  ];

  const currentItems: Record<string, unknown>[] = (() => {
    if (!data) return [];
    if (tab === 'dart') return data.results.dart?.items ?? [];
    if (tab === 'sec') return data.results.sec?.items ?? [];
    if (tab === 'youtube') return data.results.youtube ?? [];
    if (tab === 'papers') return data.results.papers ?? [];
    return [];
  })();

  return (
    <main style={{ maxWidth: 960, margin: '0 auto', padding: 24 }}>
      <h1>AC-research</h1>
      <p style={{ color: '#666' }}>
        키워드 하나로 미국 SEC / 국내 DART 재무제표, 유튜브, 논문을 검색합니다.
      </p>

      <div style={{ display: 'flex', gap: 8, marginBottom: 24 }}>
        <input
          type="text"
          placeholder="예: DIS, 005930, AI inference"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && search()}
          style={{ flex: 1, padding: '10px 12px', fontSize: 16 }}
        />
        <button onClick={search} disabled={loading} style={{ padding: '10px 20px' }}>
          {loading ? '검색 중…' : '검색'}
        </button>
      </div>

      {error && <p style={{ color: 'crimson' }}>{error}</p>}
      {data?.meta?.errors?.length ? (
        <p style={{ color: 'orange' }}>
          일부 소스 오류: {data.meta.errors.map((e) => `${e.source}: ${e.message}`).join('; ')}
        </p>
      ) : null}

      {data && (
        <>
          <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
            {tabs.map((t) => (
              <button
                key={t.id}
                onClick={() => setTab(t.id)}
                style={{
                  padding: '8px 16px',
                  fontWeight: tab === t.id ? 600 : 400,
                  border: tab === t.id ? '2px solid #333' : '1px solid #ccc',
                }}
              >
                {t.label} ({t.count})
              </button>
            ))}
            <button
              onClick={downloadExcel}
              style={{ marginLeft: 'auto', padding: '8px 16px' }}
            >
              엑셀 다운로드
            </button>
          </div>

          {data.meta.elapsed_ms != null && (
            <p style={{ fontSize: 14, color: '#666' }}>소요: {data.meta.elapsed_ms} ms</p>
          )}

          <section>
            {currentItems.length === 0 ? (
              <p>결과 없음</p>
            ) : (
              <ul style={{ listStyle: 'none', padding: 0 }}>
                {currentItems.map((item, i) => (
                  <li
                    key={i}
                    style={{
                      borderBottom: '1px solid #eee',
                      padding: '12px 0',
                    }}
                  >
                    <a
                      href={(item.url as string) || '#'}
                      target="_blank"
                      rel="noopener noreferrer"
                      style={{ fontWeight: 600 }}
                    >
                      {String(item.title ?? '')}
                    </a>
                    {(item.date || item.snippet) && (
                      <div style={{ fontSize: 14, color: '#555', marginTop: 4 }}>
                        {item.date && <span>{String(item.date)}</span>}
                        {item.snippet && <span> — {String(item.snippet)}</span>}
                      </div>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </section>
        </>
      )}
    </main>
  );
}
