// apps/web/app/layout.tsx
import type { Metadata } from "next";

export const metadata: Metadata = {
  metadataBase: new URL("https://ac-airesearch.com"),
  title: "AC-research",
  description: "키워드 하나로 미국 SEC / 국내 DART 재무제표, 유튜브, 논문을 한 번에 검색하는 리서치 도구입니다.",
  alternates: {
    canonical: "https://ac-airesearch.com",
  },
  authors: [
    {
      name: "ACresearch 센터",
      url: "https://blog.naver.com/hanryang72",
    },
  ],
  openGraph: {
    type: "website",
    url: "https://ac-airesearch.com",
    title: "AC-research",
    description: "키워드 하나로 미국 SEC / 국내 DART 재무제표, 유튜브, 논문을 한 번에 검색하는 리서치 도구입니다.",
    siteName: "AC-research",
    locale: "ko_KR",
  },
  twitter: {
    card: "summary",
    title: "AC-research",
    description: "키워드 하나로 미국 SEC / 국내 DART 재무제표, 유튜브, 논문을 한 번에 검색하는 리서치 도구입니다.",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "Organization",
    name: "AC-research",
    url: "https://ac-airesearch.com",
    sameAs: ["https://blog.naver.com/hanryang72"],
  };

  const websiteJsonLd = {
    "@context": "https://schema.org",
    "@type": "WebSite",
    name: "AC-research",
    url: "https://ac-airesearch.com",
    potentialAction: {
      "@type": "SearchAction",
      target: "https://ac-airesearch.com/?q={search_term_string}",
      "query-input": "required name=search_term_string",
    },
  };

  return (
    <html lang="ko">
      <head>
        <link rel="me" href="https://blog.naver.com/hanryang72" />
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
        />
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(websiteJsonLd) }}
        />
      </head>

      <body style={{ margin: 0, background: "#0b0f14", color: "#e6edf3" }}>
        <style jsx global>{`
          .blogBanner {
            display: block;
            text-decoration: none;
            color: #e6edf3;
            transition: transform 140ms ease, background 140ms ease, border-color 140ms ease, box-shadow 140ms ease;
          }
          .blogBannerCard {
            margin-top: 18px;
            padding: 16px;
            border-radius: 12px;
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid rgba(255, 255, 255, 0.08);
            transition: transform 140ms ease, background 140ms ease, border-color 140ms ease, box-shadow 140ms ease;
          }
          .blogBanner:hover .blogBannerCard {
            transform: translateY(-2px);
            background: rgba(255, 255, 255, 0.06);
            border-color: rgba(255, 255, 255, 0.14);
            box-shadow: 0 10px 24px rgba(0, 0, 0, 0.35);
          }
          .blogNBadge {
            width: 28px;
            height: 28px;
            border-radius: 8px;
            background: rgba(3, 199, 90, 0.18);
            border: 1px solid rgba(3, 199, 90, 0.35);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 14px;
            font-weight: 800;
            line-height: 1;
          }
          .blogDesc {
            font-size: 12px;
            opacity: 0.75;
            line-height: 1.5;
          }
        `}</style>

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

            <a
              className="blogBanner"
              href="https://blog.naver.com/hanryang72"
              target="_blank"
              rel="noopener noreferrer"
            >
              <div className="blogBannerCard">
                <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 8 }}>
                  <div className="blogNBadge">N</div>
                  <div style={{ fontSize: 15, fontWeight: 800 }}>ACresearch 센터</div>
                </div>
                <div className="blogDesc">ACresearch로 만든 정보를 공유하는 블로그입니다.</div>
              </div>
            </a>

            <div style={{ height: 18 }} />
          </aside>

          <main style={{ flex: 1, padding: 28, boxSizing: "border-box" }}>{children}</main>
        </div>
      </body>
    </html>
  );
}
