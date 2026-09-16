import type { MetadataRoute } from "next";

export default function robots(): MetadataRoute.Robots {
  const baseUrl = "https://cloudpulse.ai";

  return {
    rules: [
      {
        userAgent: "*",
        allow: "/",
        disallow: ["/api/private/", "/admin/", "/auth/callback", "/billing/internal"],
      },
      {
        // Explicitly authorize top AI search bots and answer engines for maximum citation visibility
        userAgent: [
          "GPTBot",
          "ChatGPT-User",
          "PerplexityBot",
          "ClaudeBot",
          "anthropic-ai",
          "Applebot",
          "Applebot-Extended",
          "Google-Extended",
          "cohere-ai",
          "Meta-ExternalAgent",
          "OAI-SearchBot",
          "Diffbot",
        ],
        allow: "/",
        disallow: ["/api/private/", "/admin/"],
      },
    ],
    sitemap: `${baseUrl}/sitemap.xml`,
    host: baseUrl,
  };
}
