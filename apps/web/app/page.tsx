"use client";

import { useCallback, useMemo, useState } from "react";
import SecResultsTable from "@/components/SecResultsTable";

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

function unwrap(arrOrObj: any): any[] {
  if (Array.isArray(arrOrObj)) return arrOrObj;
  if (arrOrObj && Array.isArray(arrOrObj.items)) return arrOrObj.items;
  if (arrOrObj && Array.isArray(arrOrObj.results)) return arrOrObj.results;
  return [];
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

  const openExternal = (url: string) => {
    window.open(url, "_blank");
  };

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

      const raw = await res.json();

      const normalized: ResearchResponse = {
        ...raw,
        results: {
          dart: unwrap(raw?.results?.dart),
          sec: unwrap(raw?.results?.sec),
          youtube: unwrap(raw?.results?.youtube),
          papers: unwrap(raw?.results?.papers),
        },
      };

      setData(normalized);

      const priority: TabId[] = ["dart", "sec", "youtube", "papers"];
      const firstNonEmpty = priority.find((k) => (normalized.results?.[k]?.length ?? 0) > 0) || "sec";
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

  const secRows = useMemo(() => {
    if (tab !== "sec") return [];
    return (currentItems as any[]).map((r: any) => {
      const published = r?.published_date ?? "";
      const ticker = r?.ticker ?? "";
      return {
        source_type: r?.source_type ?? "SEC",
        url: r?.url ?? "",
        published_date: published,
        ticker,
        title: r?.title ?? `${ticker} SEC ${published}`,
        date: r?.date ?? published,
      };
    });
  }, [tab, currentItems]);

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

        <div
          style={{
            background: "rgba(255,255,255,0.04)",
            border: "1px solid rgba(255,255,255,0.10)",
            borderRadius: 14,
            padding: 20,
            marginBottom: 20,
            lineHeight: 1.7,
          }}
        >
          <div style={{ fontSize: 16, fontWeight: 700, marginBottom: 12 }}>재무제표 검색 안내</div>

          <div style={{ fontSize: 14, opacity: 0.9, marginBottom: 14 }}>
            재무제표 검색 시 미국 주식은 티커(symbol), 국내 주식은 종목번호를 기준으로 조회됩니다. 정확한 검색을 위해 티커 또는
            종목번호만 단독으로 입력하는 것을 권장합니다. 다른 단어를 함께 입력할 경우 검색 정확도가 떨어질 수 있습니다. 유튜브
            영상이나 논문을 검색할 때 티커 또는 종목번호만으로 검색하면 원하는 결과가 정확히 나오지 않을 수 있습니다. 이 경우에는
            기업명 또는 관련 키워드를 함께 활용해 검색하시기 바랍니다.
          </div>

          <div style={{ fontSize: 15, fontWeight: 700, marginBottom: 10 }}>사용 방법 (Notebook LM 기준)</div>

          <ol style={{ paddingLeft: 18, fontSize: 14, opacity: 0.9 }}>
            <li>Notebook LM에 접속하여 새 노트를 생성합니다.</li>
            <li>좌측의 소스 추가 버튼을 클릭한 뒤 웹사이트를 선택합니다.</li>
            <li>프로그램에서 검색된 URL을 복사해 붙여넣고 추가합니다. 필요한 URL을 모두 추가합니다.</li>
            <li>소스 추가가 완료되면 궁금한 내용을 질문하거나, 스튜디오 기능을 실행하여 분석을 진행합니다.</li>
            <li>다른 AI 플랫폼에서도 동일한 방식으로 URL을 추가해 활용하시면 됩니다.</li>
            <li>국내주식 재무제표는 DART의 API구조 특성상 검색후 최대 10초까지 시간이 소요될 수 있습니다. 양해부탁드립니다.</li>
          </ol>
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
            <div
              style={{
                padding: 14,
                borderBottom: "1px solid rgba(255,255,255,0.08)",
                fontSize: 14,
                fontWeight: 700,
              }}
            >
              {tab === "sec" ? "SEC 결과 (미국)" : tab === "dart" ? "DART 결과 (국내)" : tab === "youtube" ? "YouTube 결과" : "Papers 결과"}
            </div>

            <div style={{ padding: 14 }}>
              {currentItems.length === 0 ? (
                <div style={{ opacity: 0.75, fontSize: 13 }}>결과 없음</div>
              ) : tab === "sec" ? (
                <SecResultsTable rows={secRows} />
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
                  <div style={{ marginTop: 10, fontSize: 12, opacity: 0.75 }}>표시 제한: 최대 50행, 최대 6컬럼</div>
                </div>
              )}
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
