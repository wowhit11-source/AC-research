"use client";

import { useMemo, useState } from "react";

type Row = {
  source_type: string;
  url: string;
  published_date: string;
  ticker: string;
  title: string;
  date: string;
};

type SortKey = keyof Row;
type SortDir = "asc" | "desc";

const COLS: SortKey[] = ["source_type", "url", "published_date", "ticker", "title", "date"];

function parseDate(value: string) {
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

export default function SecResultsTable({ rows }: { rows: Row[] }) {
  const [sortKey, setSortKey] = useState<SortKey>("date");
  const [sortDir, setSortDir] = useState<SortDir>("desc");
  const [copiedAll, setCopiedAll] = useState(false);

  const sortedRows = useMemo(() => {
    const copy = [...rows];

    copy.sort((a, b) => {
      const av = a[sortKey];
      const bv = b[sortKey];

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

  async function copyAllUrls() {
    const urls = sortedRows
      .map((r) => (r?.url ?? "").trim())
      .filter((u) => u && (u.startsWith("http://") || u.startsWith("https://")));

    const text = urls.join("\n");
    const ok = await copyToClipboard(text);
    if (!ok) return;

    setCopiedAll(true);
    window.setTimeout(() => setCopiedAll(false), 900);
  }

  return (
    <div style={{ overflowX: "auto", width: "100%" }}>
      <table style={styles.table}>
        <thead>
          <tr>
            {COLS.map((key) => {
              if (key === "url") {
                return (
                  <th key={key} style={styles.th}>
                    <div style={styles.urlHeaderWrap}>
                      <button style={styles.thButton} onClick={() => handleSort("url")}>
                        url {sortIndicator("url")}
                      </button>

                      <button
                        type="button"
                        style={copiedAll ? styles.copyAllBtnActive : styles.copyAllBtn}
                        onClick={(e) => {
                          e.preventDefault();
                          e.stopPropagation();
                          copyAllUrls();
                        }}
                        title="정렬된 순서 그대로 URL만 줄바꿈 복사"
                      >
                        {copiedAll ? "Copied" : `Copy URLs (${sortedRows.length})`}
                      </button>
                    </div>
                  </th>
                );
              }

              return (
                <th key={key} style={styles.th}>
                  <button style={styles.thButton} onClick={() => handleSort(key)}>
                    {key} {sortIndicator(key)}
                  </button>
                </th>
              );
            })}
          </tr>
        </thead>

        <tbody>
          {sortedRows.map((row, idx) => (
            <tr key={`${row.url}-${idx}`}>
              {COLS.map((key) => (
                <td key={key} style={styles.td}>
                  {key === "url" ? (
                    <a href={row.url} target="_blank" rel="noopener noreferrer" style={styles.link}>
                      {row.url}
                    </a>
                  ) : (
                    <span style={{ userSelect: "text" }}>{String(row[key] ?? "")}</span>
                  )}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>

      <style>{`
        tbody tr:hover td { background: rgba(255,255,255,0.03); }

        .copyAllBtn:hover {
          filter: brightness(1.08);
        }
        .copyAllBtn:active {
          transform: translateY(1px);
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
    border: "1px solid rgba(255,255,255,0.22)",
  },
  th: {
    textAlign: "left",
    padding: "12px 10px",
    whiteSpace: "nowrap",
    border: "1px solid rgba(255,255,255,0.18)",
    background: "rgba(255,255,255,0.03)",
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
  },
  copyAllBtn: {
    height: 26,
    padding: "0 10px",
    borderRadius: 999,
    border: "1px solid rgba(90, 169, 255, 0.55)",
    background: "rgba(90, 169, 255, 0.20)",
    color: "#e6edf3",
    cursor: "pointer",
    fontSize: 12,
    whiteSpace: "nowrap",
  },
  copyAllBtnActive: {
    height: 26,
    padding: "0 10px",
    borderRadius: 999,
    border: "1px solid rgba(80, 220, 170, 0.65)",
    background: "rgba(80, 220, 170, 0.22)",
    color: "#e6edf3",
    cursor: "pointer",
    fontSize: 12,
    whiteSpace: "nowrap",
  },
  td: {
    padding: "12px 10px",
    border: "1px solid rgba(255,255,255,0.12)",
    verticalAlign: "top",
  },
  link: {
    color: "#7aa2ff",
    textDecoration: "underline",
    wordBreak: "break-all",
    userSelect: "text",
  },
};
