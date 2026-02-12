"use client";

import { useCallback, useMemo, useState } from "react";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://127.0.0.1:8000";

type TabId = "dart" | "sec" | "youtube" | "papers";

interface ResearchMeta {
  elapsed_ms: number;
  errors: { source: string; message: string }[];
}

interface ResearchResponse {
  query: string;
  slug: string;
  results: {
    dart: any[];
    sec: any[];
    youtube: any[];
    papers: any[];
  };
  meta: ResearchMeta;
}

const pillStyle = (active: boolean) => ({
  display: "inline-flex",
  alignItems: "center",
  gap: 8,
  padding: "8px 12px",
  borderRadius: 10,
  border: "1px solid rgba(255,255,255,0.14)",
  background: active ? "rgba(255,255,255,0.14)" : "rgba(255,255,255,0.06)",
  color: "#e6edf3",
  cursor: "pointer",
  userSelect: "none" as const,
  fontSize: 13,
});

const chipStyle = (active: boolean) => ({
  display: "inline-flex",
  alignItems: "center",
  gap: 6,
  padding: "6px 10px",
  borderRadius: 999,
  border: "1px solid rgba(255,255,255,0.14)",
  background: active ? "rgba(255,80,80,0.85)" : "rgba(255,255,255,0.06)",
  color: "#e6edf3",
  cursor: "pointer",
  userSelect: "none" as const,
  fontSize: 12,
});

function countOf(data: ResearchResponse | null, tab: TabId) {
  if (!data) return 0;
  return Array.isArray(data.results[tab]) ? data.results[tab].length : 0;
}

export default function Home() {
  const [query, setQuery] = useState("ALB");
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<ResearchResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<TabId>("sec");

  const [sources, setSources] = useState<TabId[]>(["sec", "youtube", "papers"]);

  const toggleSource = (id: TabId) => {
    setSources((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));
  };

  const search = useCallback(async () => {
    const q = query.trim();
    if (!q) return;

    setLoading(true);
    setError(null);
    setData(null);

    try {
      const res = await fetch(`${BACKEND_URL}/api/research`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: q }),
      });

      if (!res.ok) {
        const t = await res.text();
        throw new Error(t || `HTTP ${res.status}`);
      }

      const json: ResearchResponse = await res.json();
      setData(json);

      const priority: TabId[] = ["dart", "sec", "youtube", "papers"];
      const firstNonEmpty = priority.find((k) => (json.results?.[k]?.length ?? 0) > 0) || "sec";
      setTab(firstNonEmpty);
    } catch (e: any) {
      setError(e?.message ? String(e.message) : "Failed to fetch");
    } finally {
      setLoading(false);
    }
  }, [query]);

  const downloadExcel = useCallback(() => {
    if (!data?.slug) return;
    const url = `${BACKEND_URL}/api/research/${encodeURIComponent(data.slug)}/excel`;
    window.open(url, "_blank");
  }, [data]);

  const tabs = useMemo(
    () => [
      { id: "dart" as const, label: "DART", count: countOf(data, "dart") },
      { id: "sec" as const, label: "SEC", count: countOf(data, "sec") },
      { id: "youtube" as const, label: "YouTube", count: countOf(data, "youtube") },
      { id: "papers" as const, label: "Papers", count: countOf(data, "papers") },
    ],
    [data]
  );

  const currentItems = useMemo(() => {
    if (!data) return [];
    return data.results?.[tab] ?? [];
  }, [data, tab]);

  return (
    <div style={{ maxWidth: 1100, margin: "0 auto" }}>
      <div style={{ fontSize: 34, fontWeight: 800, marginBottom: 10 }}>AC-research</div>
      <div style={{ fontSize: 14, opacity: 0.9, marginBottom: 18 }}>
        키워드 하나로 미국 SEC / 국내 DART 재무제표, 유튜브, 논문을 한 번에 검색하는 리서치 도구입니다.
      </div>

      <div style={{ fontSize: 13, opacity: 0.85, marginBottom: 8 }}>
        검색어 또는 티커 (재무제표는 미국주식 티커, 국내주식은 종목번호, 유튜브/논문 검색어 사용)
      </div>

      <div
        style={{
          background: "rgba(255,255,255,0.04)",
          border: "1px solid rgba(255,255,255,0.10)",
          borderRadius: 14,
          padding: 16,
          marginBottom: 14,
        }}
      >
        <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => (e.key === "Enter" ? search() : null)}
            placeholder="예: D15, 005930, ALB, AI inference"
            style={{
              flex: 1,
              height: 40,
              padding: "0 12px",
              borderRadius: 10,
              border: "1px solid rgba(255,255,255,0.12)",
              background: "rgba(0,0,0,0.25)",
              color: "#e6edf3",
              outline: "none",
              fontSize: 14,
            }}
          />
          <button
            onClick={search}
            disabled={loading}
            style={{
              height: 40,
              padding: "0 14px",
              borderRadius: 10,
              border: "1px solid rgba(255,255,255,0.14)",
              background: "rgba(255,255,255,0.10)",
              color: "#e6edf3",
              cursor: loading ? "not-allowed" : "pointer",
              fontSize: 14,
            }}
          >
            {loading ? "검색 중" : "검색"}
          </button>
        </div>

        <div style={{ height: 12 }} />

        <div style={{ fontSize: 13, opacity: 0.85, marginBottom: 8 }}>검색할 소스 (복수 선택 가능)</div>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" }}>
          <span onClick={() => toggleSource("youtube")} style={chipStyle(sources.includes("youtube"))}>
            유튜브
          </span>
          <span onClick={() => toggleSource("papers")} style={chipStyle(sources.includes("papers"))}>
            논문
          </span>
          <span onClick={() => toggleSource("sec")} style={chipStyle(sources.includes("sec"))}>
            재무제표(SEC)
          </span>
          <span onClick={() => toggleSource("dart")} style={chipStyle(sources.includes("dart"))}>
            재무제표(DART)
          </span>
        </div>

        <div style={{ height: 12 }} />

        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div style={{ fontSize: 13, opacity: 0.9 }}>
            {data?.meta?.elapsed_ms != null ? `소요: ${data.meta.elapsed_ms.toFixed(2)} ms` : ""}
          </div>
          <button
            onClick={downloadExcel}
            disabled={!data?.slug}
            style={{
              height: 36,
              padding: "0 12px",
              borderRadius: 10,
              border: "1px solid rgba(255,255,255,0.14)",
              background: data?.slug ? "rgba(255,255,255,0.10)" : "rgba(255,255,255,0.05)",
              color: "#e6edf3",
              cursor: data?.slug ? "pointer" : "not-allowed",
              fontSize: 13,
            }}
          >
            엑셀 파일 다운로드
          </button>
        </div>

        {error ? <div style={{ color: "#ff6b6b", marginTop: 10, fontSize: 13 }}>{error}</div> : null}

        {data?.meta?.errors?.length ? (
          <div style={{ color: "#ffcc66", marginTop: 10, fontSize: 12 }}>
            오류 소스: {data.meta.errors.map((e) => `${e.source}: ${e.message}`).join(" | ")}
          </div>
        ) : null}
      </div>

      {data ? (
        <div>
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap", alignItems: "center", marginBottom: 14 }}>
            {tabs.map((t) => (
              <span key={t.id} onClick={() => setTab(t.id)} style={pillStyle(tab === t.id)}>
                <span>{t.label}</span>
                <span style={{ opacity: 0.9 }}>({t.count})</span>
              </span>
            ))}
          </div>

          <div
            style={{
              background: "rgba(255,255,255,0.04)",
              border: "1px solid rgba(255,255,255,0.10)",
              borderRadius: 14,
              overflow: "hidden",
            }}
          >
            <div style={{ padding: 14, borderBottom: "1px solid rgba(255,255,255,0.08)", fontSize: 14, fontWeight: 700 }}>
              {tab === "sec" ? "SEC 결과 (미국)" : tab === "dart" ? "DART 결과 (국내)" : tab === "youtube" ? "YouTube 결과" : "Papers 결과"}
            </div>

            <div style={{ padding: 14 }}>
              {currentItems.length === 0 ? (
                <div style={{ opacity: 0.75, fontSize: 13 }}>결과 없음</div>
              ) : (
                <div style={{ overflowX: "auto" }}>
                  <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
                    <thead>
                      <tr>
                        {Object.keys(currentItems[0] ?? {}).slice(0, 6).map((k) => (
                          <th
                            key={k}
                            style={{
                              textAlign: "left",
                              padding: "10px 8px",
                              borderBottom: "1px solid rgba(255,255,255,0.10)",
                              opacity: 0.9,
                              fontWeight: 700,
                            }}
                          >
                            {k}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {currentItems.slice(0, 50).map((row: any, idx: number) => (
                        <tr key={idx}>
                          {Object.keys(currentItems[0] ?? {}).slice(0, 6).map((k) => {
                            const v = row?.[k];
                            const s = v == null ? "" : String(v);
                            const isUrl = s.startsWith("http://") || s.startsWith("https://");
                            return (
                              <td
                                key={k}
                                style={{
                                  padding: "10px 8px",
                                  borderBottom: "1px solid rgba(255,255,255,0.06)",
                                  verticalAlign: "top",
                                  opacity: 0.95,
                                }}
                              >
                                {isUrl ? (
                                  <a href={s} target="_blank" rel="noreferrer" style={{ color: "#7aa2ff" }}>
                                    {s}
                                  </a>
                                ) : (
                                  s
                                )}
                              </td>
                            );
                          })}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  <div style={{ marginTop: 10, fontSize: 12, opacity: 0.75 }}>
                    표시 제한: 최대 50행, 최대 6컬럼
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
