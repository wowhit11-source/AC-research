"use client";

import { useMemo, useState } from "react";

type Row = {
  source_type?: string;
  url?: string;
  published_date?: string;
  ticker?: string;
  title?: string;
  date?: string;
};

type SortKey = keyof Row;
type SortDir = "asc" | "desc";

function parseDate(value?: string) {
  if (!value) return 0;
  const t = Date.parse(value);
  return Number.isFinite(t) ? t : 0;
}

export default function ResultsTable({
  rows,
  label,
}: {
  rows: Row[];
  label: string;
}) {
  const [sortKey, setSortKey] = useState<SortKey>("date");
  const [sortDir, setSortDir] = useState<SortDir>("desc");

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

  function handleCopyAll() {
    const urls = sortedRows
      .map((r) => r.url)
      .filter(Boolean)
      .join("\n");

    navigator.clipboard.writeText(urls);
  }

  return (
    <div style={{ width: "100%" }}>
      <div style={styles.header}>
        <div>{label}</div>
        <button style={styles.copyBtn} onClick={handleCopyAll}>
          Copy URLs ({rows.length})
        </button>
      </div>

      <div style={{ overflowX: "auto" }}>
        <table style={styles.table}>
          <thead>
            <tr>
              <th style={styles.th}>
                <button style={styles.thButton} onClick={() => handleSort("source_type")}>
                  source_type {sortIndicator("source_type")}
                </button>
              </th>

              <th style={styles.th}>
                <button style={styles.thButton} onClick={() => handleSort("url")}>
                  url {sortIndicator("url")}
                </button>
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
              <tr key={`${row.url}-${idx}`} style={styles.tr}>
                <td style={styles.td}>{row.source_type}</td>

                <td style={styles.td}>
                  <a
                    href={row.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    style={styles.link}
                  >
                    {row.url}
                  </a>
                </td>

                <td style={styles.td}>{row.published_date}</td>
                <td style={styles.td}>{row.ticker}</td>
                <td style={styles.td}>{row.title}</td>
                <td style={styles.td}>{row.date}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    padding: "10px 0",
  },
  copyBtn: {
    background: "#1e90ff",
    color: "#fff",
    padding: "6px 14px",
    borderRadius: "6px",
    cursor: "pointer",
    fontWeight: 600,
  },
  table: {
    width: "100%",
    borderCollapse: "collapse",
    fontSize: "13px",
  },
  th: {
    textAlign: "left",
    padding: "10px",
    borderBottom: "1px solid rgba(255,255,255,0.1)",
  },
  thButton: {
    all: "unset",
    cursor: "pointer",
  },
  tr: {
    userSelect: "none",
  },
  td: {
    padding: "10px",
    borderBottom: "1px solid rgba(255,255,255,0.05)",
  },
  link: {
    textDecoration: "underline",
    wordBreak: "break-all",
  },
};
