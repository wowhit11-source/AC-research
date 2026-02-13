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
  const [copiedUrl, setCopiedUrl] = useState<string | null>(null);

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

  async function handleCopyUrl(url: string) {
    if (!url) return;
    const ok = await copyToClipboard(url);
    if (!ok) return;

    setCopiedUrl(url);
    window.setTimeout(() => {
      setCopiedUrl((prev) => (prev === url ? null : prev));
    }, 900);
  }

  return (
    <div style={{ overflowX: "auto", width: "100%" }}>
      <table style={styles.table}>
        <thead>
          <tr>
            {COLS.map((key) => (
              <th key={key} style={styles.th}>
                <button style={styles.thButton} onClick={() => handleSort(key)}>
                  {key} {sortIndicator(key)}
                </button>
              </th>
            ))}
          </tr>
        </thead>

        <tbody>
          {sortedRows.map((row, idx) => (
            <tr key={`${row.url}-${idx}`}>
              {COLS.map((key) => (
                <td key={key} style={styles.td}>
                  {key === "url" ? (
                    <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
                      <a
                        href={row.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        style={styles.link}
                        onClick={(e) => e.stopPropagation()}
                      >
                        {row.url}
                      </a>

                      <button
                        type="button"
                        style={styles.copyBtn}
                        onClick={(e) => {
                          e.preventDefault();
                          e.stopPropagation();
                          handleCopyUrl(row.url);
                        }}
                        title="URL 복사"
                      >
                        {copiedUrl === row.url ? "Copied" : "Copy"}
                      </button>
                    </div>
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
  },
  thButton: {
    all: "unset",
    cursor: "pointer",
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
  copyBtn: {
    height: 24,
    padding: "0 10px",
    borderRadius: 8,
    border: "1px solid rgba(255,255,255,0.18)",
    background: "rgba(255,255,255,0.06)",
    color: "#e6edf3",
    cursor: "pointer",
    fontSize: 12,
    whiteSpace: "nowrap",
  },
};
