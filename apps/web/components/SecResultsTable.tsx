"use client";

import React, { useMemo, useState } from "react";

type Row = {
  query?: string;
  source_type?: string;
  url?: string;
  published_date?: string;
  ticker?: string;
  title?: string;
  date?: string;
};

type SortKey = keyof Row;  // "query" | "source_type" | "url" | ...
type SortDir = "asc" | "desc";

function parseDate(value?: string) {
  if (!value) return 0;
  const t = Date.parse(value);
  return Number.isFinite(t) ? t : 0;
}

async function copyToClipboard(text: string) {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    try {
      const ta = document.createElement("textarea");
      ta.value = text;
      ta.style.position = "fixed";
      ta.style.left = "-9999px";
      ta.style.top = "-9999px";
      document.body.appendChild(ta);
      ta.focus();
      ta.select();
      const ok = document.execCommand("copy");
      document.body.removeChild(ta);
      return ok;
    } catch {
      return false;
    }
  }
}

export default function SecResultsTable({
  rows,
  label,
}: {
  rows: Row[];
  label: string;
}) {
  const [sortKey, setSortKey] = useState<SortKey>("date");
  const [sortDir, setSortDir] = useState<SortDir>("desc");
  const [copied, setCopied] = useState(false);

  // query 컬럼이 하나라도 있으면 다중 검색 결과 → 컬럼 표시
  const hasQueryCol = rows.some((r) => r.query && r.query.trim() !== "");

  const sortedRows = useMemo(() => {
    const copy = [...rows];

    copy.sort((a, b) => {
      const av = a[sortKey] ?? "";
      const bv = b[sortKey] ?? "";

      let compare = 0;

      if (sortKey === "date" || sortKey === "published_date") {
        compare = parseDate(String(av)) - parseDate(String(bv));
      } else {
        compare = String(av).localeCompare(String(bv));
      }

      return sortDir === "asc" ? compare : -compare;
    });

    return copy;
  }, [rows, sortKey, sortDir]);

  function handleSort(key: SortKey) {
    if (sortKey === key) {
      setSortDir(sortDir === "asc" ? "desc" : "asc");
    } else {
      setSortKey(key);
      setSortDir("asc");
    }
  }

  function sortIndicator(key: SortKey) {
    if (sortKey !== key) return "↕";
    return sortDir === "asc" ? "↑" : "↓";
  }

  async function handleCopyAll() {
    const urls = sortedRows
      .map((r) => (r.url ?? "").trim())
      .filter(Boolean)
      .join("\n");

    if (!urls) return;

    const ok = await copyToClipboard(urls);
    if (ok) {
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1200);
    } else {
      alert("복사에 실패했습니다. 브라우저 권한을 확인해주세요.");
    }
  }

  return (
    <div style={{ width: "100%" }}>
      <div style={{ marginBottom: 10, fontSize: 14, fontWeight: 700 }}>
        {label}
      </div>

      <div style={{ overflowX: "auto" }}>
        <table style={styles.table}>
          <thead>
            <tr>
              {hasQueryCol && (
                <th style={styles.th}>
                  <button style={styles.thButton} onClick={() => handleSort("query")}>
                    query {sortIndicator("query")}
                  </button>
                </th>
              )}
              <th style={styles.th}>
                <button style={styles.thButton} onClick={() => handleSort("source_type")}>
                  source_type {sortIndicator("source_type")}
                </button>
              </th>

              <th style={styles.th}>
                <div style={styles.urlHeaderWrap}>
                  <button style={styles.thButton} onClick={() => handleSort("url")}>
                    url {sortIndicator("url")}
                  </button>

                  <button
                    type="button"
                    onClick={handleCopyAll}
                    style={copied ? styles.copyBtnCopied : styles.copyBtn}
                    title="정렬된 순서 그대로 URL만 줄바꿈 복사"
                  >
                    {copied ? "Copied" : `Copy URLs (${rows.length})`}
                  </button>
                </div>
              </th>

              <th style={styles.th}>
                <button style={styles.thButton} onClick={() => handleSort("published_date")}>
                  published_date {sortIndicator("published_date")}
                </button>
              </th>

              <th style={styles.th}>
                <button style={styles.thButton} onClick={() => handleSort("ticker")}>
                  ticker {sortIndicator("ticker")}
                </button>
              </th>

              <th style={styles.th}>
                <button style={styles.thButton} onClick={() => handleSort("title")}>
                  title {sortIndicator("title")}
                </button>
              </th>

              <th style={styles.th}>
                <button style={styles.thButton} onClick={() => handleSort("date")}>
                  date {sortIndicator("date")}
                </button>
              </th>
            </tr>
          </thead>

          <tbody>
            {sortedRows.map((row, idx) => (
              <tr key={`${row.url ?? "row"}-${idx}`} style={styles.tr}>
                {hasQueryCol && (
                  <td style={{ ...styles.td, ...styles.queryCell }}>{row.query ?? ""}</td>
                )}
                <td style={styles.td}>{row.source_type ?? ""}</td>

                <td style={styles.td}>
                  {row.url ? (
                    <a href={row.url} target="_blank" rel="noopener noreferrer" style={styles.link}>
                      {row.url}
                    </a>
                  ) : (
                    ""
                  )}
                </td>

                <td style={styles.td}>{row.published_date ?? ""}</td>
                <td style={styles.td}>{row.ticker ?? ""}</td>
                <td style={styles.td}>{row.title ?? ""}</td>
                <td style={styles.td}>{row.date ?? ""}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <style>{`
        tbody tr:hover td {
          background: rgba(255,255,255,0.03);
        }
        button[data-copy-btn]:hover {
          transform: translateY(-1px);
        }
      `}</style>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  table: {
    width: "100%",
    borderCollapse: "collapse",
    fontSize: "13px",
  },
  th: {
    textAlign: "left",
    padding: "10px",
    borderBottom: "1px solid rgba(255,255,255,0.1)",
    whiteSpace: "nowrap",
    verticalAlign: "middle",
  },
  thButton: {
    all: "unset",
    cursor: "pointer",
  },
  urlHeaderWrap: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    gap: 10,
    minWidth: 520,
  },
  tr: {
    userSelect: "none",
  },
  td: {
    padding: "10px",
    borderBottom: "1px solid rgba(255,255,255,0.05)",
    verticalAlign: "top",
  },
  link: {
    textDecoration: "underline",
    wordBreak: "break-all",
  },
  copyBtn: {
    background: "rgba(255, 80, 80, 0.92)",
    color: "#fff",
    padding: "6px 12px",
    borderRadius: 8,
    cursor: "pointer",
    fontWeight: 800,
    border: "1px solid rgba(255,255,255,0.18)",
    boxShadow: "0 6px 20px rgba(255, 80, 80, 0.18)",
    transition: "transform 0.08s ease",
    userSelect: "none",
  },
  copyBtnCopied: {
    background: "rgba(80, 200, 120, 0.92)",
    color: "#0b1a12",
    padding: "6px 12px",
    borderRadius: 8,
    cursor: "pointer",
    fontWeight: 900,
    border: "1px solid rgba(255,255,255,0.18)",
    boxShadow: "0 6px 20px rgba(80, 200, 120, 0.16)",
    transition: "transform 0.08s ease",
    userSelect: "none",
  },
  queryCell: {
    fontWeight: 600,
    color: "rgba(255, 180, 80, 0.95)",
    whiteSpace: "nowrap",
    maxWidth: 160,
    overflow: "hidden",
    textOverflow: "ellipsis",
  },
};
