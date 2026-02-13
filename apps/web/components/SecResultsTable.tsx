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
    <div style={{ width: "100%" }}>
      <div style={styles.toolbar}>
        <button type="button" style={styles.copyAllBtn} onClick={copyAllUrls}>
          {copiedAll ? "Copied" : `Copy all URLs (${sortedRows.length})`}
        </button>
        <div style={styles.hint}>정렬 상태 그대로 URL만 줄바꿈으로 복사됨</div>
      </div>

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
        `}</style>
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  toolbar: {
    display: "flex",
    alignItems: "center",
    gap: 12,
    marginBottom: 10,
  },
  copyAllBtn: {
    height: 32,
    padding: "0 12px",
    borderRadius: 10,
    border: "1px solid rgba(255,255,255,0.18)",
    background: "rgba(255,255,255,0.08)",
    color: "#e6edf3",
    cursor: "pointer",
    fontSize: 13,
    whiteSpace: "nowrap",
  },
  hint: {
    fontSize: 12,
    opacity: 0.75,
  },
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
};
