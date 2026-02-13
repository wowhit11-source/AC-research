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
            {(["source_type", "url", "published_date", "ticker", "title", "date"] as SortKey[]).map(
              (key, i, arr) => (
                <th
                  key={key}
                  style={{
                    ...styles.th,
                    borderRight:
                      i !== arr.length - 1
                        ? "1px solid rgba(255,255,255,0.08)"
                        : undefined,
                  }}
                >
                  <button style={styles.thButton} onClick={() => handleSort(key)}>
                    {key} {sortIndicator(key)}
                  </button>
                </th>
              )
            )}
          </tr>
        </thead>

        <tbody>
          {sortedRows.map((row, idx) => (
            <tr key={`${row.url}-${idx}`} style={styles.tr}>
              {(["source_type", "url", "published_date", "ticker", "title", "date"] as SortKey[]).map(
                (key, i, arr) => {
                  const value = row[key];
                  const isLast = i === arr.length - 1;

                  return (
                    <td
                      key={key}
                      style={{
                        ...styles.td,
                        borderRight: !isLast
                          ? "1px solid rgba(255,255,255,0.06)"
                          : undefined,
                      }}
                    >
                      {key === "url" ? (
                        <a
                          href={value}
                          target="_blank"
                          rel="noopener noreferrer"
                          style={styles.link}
                        >
                          {value}
                        </a>
                      ) : (
                        <span>{value}</span>
                      )}
                    </td>
                  );
                }
              )}
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
    border: "1px solid rgba(255,255,255,0.15)",
  },
  th: {
    textAlign: "left",
    padding: "12px 10px",
    borderBottom: "1px solid rgba(255,255,255,0.10)",
    whiteSpace: "nowrap",
  },
  thButton: {
    all: "unset",
    cursor: "pointer",
  },
  tr: {},
  td: {
    padding: "12px 10px",
    borderBottom: "1px solid rgba(255,255,255,0.05)",
    whiteSpace: "nowrap",
  },
  link: {
    textDecoration: "underline",
    wordBreak: "break-all",
    color: "#7aa2ff",
  },
};

