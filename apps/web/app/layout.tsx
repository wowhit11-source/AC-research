// apps/web/app/layout.tsx
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "AC-research",
  description: "AC-research",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko">
      <body style={{ margin: 0, background: "#0b0f14", color: "#e6edf3" }}>
        <div style={{ display: "flex", minHeight: "100vh" }}>
          <aside
            style={{
              width: 260,
              background: "#0f1621",
              borderRight: "1px solid rgba(255,255,255,0.08)",
              padding: 16,
              boxSizing: "border-box",
            }}
          >
            <div style={{ fontSize: 16, fontWeight: 700, marginBottom: 14 }}>리서치 보조 도구</div>

            <div style={{ display: "grid", gap: 10 }}>
              {[
                { label: "ChatGPT", href: "#" },
                { label: "Google Gemini", href: "#" },
                { label: "Anthropic Claude", href: "#" },
                { label: "Google NotebookLM", href: "#" },
              ].map((item) => (
                <a
                  key={item.label}
                  href={item.href}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 10,
                    padding: "10px 12px",
                    borderRadius: 10,
                    border: "1px solid rgba(255,255,255,0.10)",
                    textDecoration: "none",
                    color: "#e6edf3",
                    background: "rgba(255,255,255,0.02)",
                  }}
                >
                  <span
                    style={{
                      width: 18,
                      height: 18,
                      borderRadius: 4,
                      background: "rgba(255,255,255,0.12)",
                      display: "inline-block",
                    }}
                  />
                  <span style={{ fontSize: 14 }}>{item.label}</span>
                </a>
              ))}
            </div>

            <div style={{ height: 18 }} />

            <div style={{ borderTop: "1px solid rgba(255,255,255,0.08)", paddingTop: 14 }}>
              <div style={{ fontSize: 13, opacity: 0.85, marginBottom: 10 }}>실행 방법</div>
              <div
                style={{
                  fontFamily: "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace",
                  fontSize: 12,
                  background: "rgba(255,255,255,0.04)",
                  border: "1px solid rgba(255,255,255,0.10)",
                  borderRadius: 10,
                  padding: 12,
                  color: "#c9d1d9",
                  lineHeight: 1.5,
                }}
              >
                streamlit run app.py
              </div>
            </div>
          </aside>

          <main style={{ flex: 1, padding: 28, boxSizing: "border-box" }}>{children}</main>
        </div>
      </body>
    </html>
  );
}
