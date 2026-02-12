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

function parseDate(value: string) {
  const t = Date.parse(value);
  return Number.isFinite(t) ? t : 0;
}

export default function SecResultsTable({ rows }: { rows: Row[] }) {
  const [sortKey, setSortKey] = useState<SortKey>("date");
  const [sortDir, setSortDir] = useState<SortDir>("desc");

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

  return (
    <div style={{ overflowX: "auto", width: "100%" }}>
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
              <td style={styles.td}>
                <span style={styles.cellText}>{row.source_type}</span>
              </td>

              <td style={styles.td}>
                <a
                  href={row.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{ ...styles.link, ...styles.cellText }}
                >
                  {row.url}
                </a>
              </td>

              <td style={styles.td}>
                <span style={styles.cellText}>{row.published_date}</span>
              </td>

              <td style={styles.td}>
                <span style={styles.cellText}>{row.ticker}</span>
              </td>

              <td style={styles.td}>
                <span style={styles.cellText}>{row.title}</span>
              </td>

              <td style={styles.td}>
                <span style={styles.cellText}>{row.date}</span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <style>{`
        tbody tr:hover td {
          background: rgba(255,255,255,0.03);
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
    maxWidth: "500px",
  },
  cellText: {
    userSelect: "text",
  },
  link: {
    textDecoration: "underline",
    wordBreak: "break-all",
  },
};
