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
                { label: "ChatGPT", href: "https://chat.openai.com", icon: "/chatgpt.svg" },
                { label: "Google Gemini", href: "https://gemini.google.com", icon: "/gemini.svg" },
                { label: "Anthropic Claude", href: "https://claude.ai", icon: "/claude.svg" },
                { label: "Google NotebookLM", href: "https://notebooklm.google.com", icon: "/notebooklm.svg" },
              ].map((item) => (
                <a
                  key={item.label}
                  href={item.href}
                  target="_blank"
                  rel="noopener noreferrer"
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
                  <img
                    src={item.icon}
                    alt={item.label}
                    style={{
                      width: 20,
                      height: 20,
                      objectFit: "contain",
                    }}
                  />

                  <span style={{ fontSize: 14 }}>{item.label}</span>
                </a>
              ))}
            </div>

            {/* 블로그 배너 추가 */}
            <div
              style={{
                marginTop: 18,
                padding: 16,
                borderRadius: 12,
                background: "rgba(255,255,255,0.04)",
                border: "1px solid rgba(255,255,255,0.08)",
              }}
            >
              <a
                href="https://blog.naver.com/hanryang72"
                target="_blank"
                rel="noopener noreferrer"
                style={{
                  textDecoration: "none",
                  color: "#e6edf3",
                  display: "block",
                }}
              >
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 10,
                    marginBottom: 8,
                  }}
                >
                  <div
                    style={{
                      width: 28,
                      height: 28,
                      borderRadius: 8,
                      background: "rgba(3, 199, 90, 0.18)",
                      border: "1px solid rgba(3, 199, 90, 0.35)",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      fontSize: 14,
                      fontWeight: 800,
                      color: "#e6edf3",
                      lineHeight: 1,
                    }}
                  >
                    N
                  </div>

                  <div style={{ fontSize: 15, fontWeight: 800 }}>ACresearch 센터</div>
                </div>

                <div style={{ fontSize: 12, opacity: 0.75, lineHeight: 1.5 }}>
                  ACresearch로 만든 정보를 공유하는 블로그입니다.
                </div>
              </a>
            </div>

            <div style={{ height: 18 }} />
          </aside>

          <main style={{ flex: 1, padding: 28, boxSizing: "border-box" }}>{children}</main>
        </div>
      </body>
    </html>
  );
}
