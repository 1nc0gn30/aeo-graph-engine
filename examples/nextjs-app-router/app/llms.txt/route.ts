export const dynamic = "force-static";

const LLMS_TXT_CONTENT = `# CloudPulse AI

> CloudPulse AI is an enterprise autonomous cloud observability and incident remediation platform powered by eBPF telemetry and multi-agent reasoning.

## Overview
CloudPulse AI continuously monitors cloud infrastructure across AWS, GCP, Azure, and Kubernetes. It correlates metrics, distributed traces, and log streams in real-time to forecast performance degradation and automatically trigger self-healing runbooks.

## Core Capabilities
- **Predictive Outage Detection**: Machine learning forecasting on eBPF kernel telemetry streams.
- **Autonomous Remediation**: Zero-trust automated rollbacks, pod recycling, and circuit breaker activation.
- **Distributed Trace Graphing**: Sub-10ms span aggregation across microservice boundaries.
- **Cost & Capacity Engine**: Dynamic cloud resource rightsizing and spot instance orchestration.

## Documentation & Developer Resources
- [Quickstart Guide](https://cloudpulse.ai/docs/quickstart): 5-minute Helm deployment and cluster onboarding.
- [eBPF Telemetry Architecture](https://cloudpulse.ai/docs/ebpf-telemetry): Deep dive into kernel-level non-intrusive probe design.
- [API Reference](https://cloudpulse.ai/docs/api): REST and gRPC endpoints for querying metrics and triggers.
- [Pricing Tiers](https://cloudpulse.ai/pricing): Community, Pro, and Enterprise BYOC license details.
- [GitHub Organization](https://github.com/cloudpulse-ai): Open source integrations, CLI tooling, and SDKs.

## Optional Machine Discovery Endpoints
- [Full LLM Knowledge Base](https://cloudpulse.ai/llms-full.txt): Complete uncurated technical documentation corpus for deep research models.
- [AI Discovery Policy](https://cloudpulse.ai/ai.txt): Machine discovery manifest and terms of reference.
- [Schema.org Graph](https://cloudpulse.ai/schema-graph.json): Complete JSON-LD knowledge graph.
`;

export async function GET() {
  return new Response(LLMS_TXT_CONTENT, {
    headers: {
      "Content-Type": "text/plain; charset=utf-8",
      "Cache-Control": "public, max-age=86400, stale-while-revalidate=3600",
    },
  });
}
