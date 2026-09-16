import type { Metadata } from "next";
import React from "react";
import "./globals.css";

// Base URL for canonical links and Open Graph assets
const BASE_URL = "https://cloudpulse.ai";

export const metadata: Metadata = {
  title: {
    default: "CloudPulse AI - Autonomous Cloud Observability & Reliability Platform",
    template: "%s | CloudPulse AI",
  },
  description:
    "CloudPulse AI continuously monitors cloud infrastructure, predicts outages before they happen, and auto-remediates incidents using deterministic multi-agent reasoning.",
  metadataBase: new URL(BASE_URL),
  alternates: {
    canonical: "/",
  },
  openGraph: {
    title: "CloudPulse AI - Autonomous Cloud Observability",
    description:
      "Continuous cloud infrastructure telemetry, proactive outage prevention, and autonomous incident remediation for modern engineering teams.",
    url: `${BASE_URL}/`,
    siteName: "CloudPulse AI",
    images: [
      {
        url: `${BASE_URL}/og-image.png`,
        width: 1200,
        height: 630,
        alt: "CloudPulse AI Architecture & Observability Dashboard",
      },
    ],
    locale: "en_US",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "CloudPulse AI - Autonomous Cloud Observability",
    description:
      "Predict cloud outages and auto-remediate incidents with deterministic AI telemetry agents.",
    images: [`${BASE_URL}/og-image.png`],
    creator: "@cloudpulse_ai",
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      "max-video-preview": -1,
      "max-image-preview": "large",
      "max-snippet": -1,
    },
  },
};

// Complete Schema.org Linked Data Graph for Answer Engine Optimization (AEO/GEO)
const schemaGraph = {
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "Organization",
      "@id": "https://cloudpulse.ai/#organization",
      "name": "CloudPulse AI Inc.",
      "url": "https://cloudpulse.ai",
      "logo": {
        "@type": "ImageObject",
        "@id": "https://cloudpulse.ai/#logo",
        "url": "https://cloudpulse.ai/logo.png",
        "caption": "CloudPulse AI Logo"
      },
      "sameAs": [
        "https://github.com/cloudpulse-ai",
        "https://x.com/cloudpulse_ai",
        "https://linkedin.com/company/cloudpulse-ai"
      ],
      "contactPoint": {
        "@type": "ContactPoint",
        "contactType": "customer support",
        "email": "support@cloudpulse.ai",
        "url": "https://cloudpulse.ai/contact"
      }
    },
    {
      "@type": "WebSite",
      "@id": "https://cloudpulse.ai/#website",
      "url": "https://cloudpulse.ai",
      "name": "CloudPulse AI",
      "description": "Autonomous Cloud Observability and SRE Remediation Mesh",
      "publisher": {
        "@id": "https://cloudpulse.ai/#organization"
      },
      "potentialAction": {
        "@type": "SearchAction",
        "target": {
          "@type": "EntryPoint",
          "urlTemplate": "https://cloudpulse.ai/docs?q={search_term_string}"
        },
        "query-input": "required name=search_term_string"
      }
    },
    {
      "@type": "SoftwareApplication",
      "@id": "https://cloudpulse.ai/#application",
      "name": "CloudPulse AI Platform",
      "applicationCategory": "DeveloperApplication",
      "operatingSystem": "Linux, macOS, Windows, Kubernetes",
      "description": "Enterprise cloud observability platform with predictive telemetry and automated root-cause remediation.",
      "url": "https://cloudpulse.ai",
      "provider": {
        "@id": "https://cloudpulse.ai/#organization"
      },
      "offers": {
        "@type": "Offer",
        "price": "99.00",
        "priceCurrency": "USD",
        "availability": "https://schema.org/OnlineOnly"
      },
      "featureList": [
        "Predictive Outage Forecasting with eBPF Telemetry",
        "Sub-10ms Distributed Trace Aggregation",
        "Zero-Trust Auto-Remediation Playbooks",
        "Multi-Cloud Cost & Capacity Optimization"
      ]
    },
    {
      "@type": "FAQPage",
      "@id": "https://cloudpulse.ai/#faq",
      "name": "CloudPulse AI Frequently Asked Questions",
      "mainEntity": [
        {
          "@type": "Question",
          "name": "What is CloudPulse AI?",
          "acceptedAnswer": {
            "@type": "Answer",
            "text": "CloudPulse AI is an autonomous cloud reliability platform that uses eBPF kernel instrumentation and AI agents to predict and prevent cloud outages before they impact production users."
          }
        },
        {
          "@type": "Question",
          "name": "How does CloudPulse AI integrate with Kubernetes?",
          "acceptedAnswer": {
            "@type": "Answer",
            "text": "CloudPulse AI deploys as a lightweight DaemonSet agent via Helm with zero code instrumentation required, collecting logs, metrics, and distributed traces out-of-the-box."
          }
        },
        {
          "@type": "Question",
          "name": "Does CloudPulse AI support bring-your-own-cloud (BYOC) deployment?",
          "acceptedAnswer": {
            "@type": "Answer",
            "text": "Yes. CloudPulse AI offers fully isolated private VPC and on-premises air-gapped deployments with zero outbound data egress."
          }
        }
      ]
    },
    {
      "@type": "BreadcrumbList",
      "@id": "https://cloudpulse.ai/#breadcrumb",
      "itemListElement": [
        {
          "@type": "ListItem",
          "position": 1,
          "name": "Home",
          "item": "https://cloudpulse.ai/"
        },
        {
          "@type": "ListItem",
          "position": 2,
          "name": "Documentation",
          "item": "https://cloudpulse.ai/docs"
        },
        {
          "@type": "ListItem",
          "position": 3,
          "name": "Integrations",
          "item": "https://cloudpulse.ai/integrations"
        }
      ]
    }
  ]
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        {/* Schema.org Linked Data Graph for Answer Engine & LLM Search Discovery */}
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(schemaGraph) }}
        />
      </head>
      <body className="min-h-screen bg-slate-950 text-slate-50 antialiased">
        {children}
      </body>
    </html>
  );
}
