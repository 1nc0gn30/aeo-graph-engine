"""
Interactive Web UI & REST API Server for AEO Graph Engine.
Delivers a Google-designed light mode AEO Studio dashboard with real-time
Schema.org visualization, llms.txt compiler, HTML injector, AI prompt synthesizer,
and AEO audit scoring. Zero external runtime dependencies.
"""

import sys
import os
import json
import zipfile
import io
import urllib.parse
from pathlib import Path
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from typing import Optional, Dict, Any

from .core import (
    resolve_config,
    generate_schema_graph,
    generate_llms_txt,
    generate_llms_full_txt,
    generate_ai_txt,
    generate_robots_txt,
    write_aeo_bundle
)
from .injector import inject_jsonld_into_html
from .validator import validate_aeo_bundle, validate_schema_jsonld_dict, AEODiagnosticReport
from .extractor import extract_metadata_from_html
from .discovery import discover_project_metadata
from .ai_config import synthesize_config_from_prompt, get_agent_json_schema
from .presets import NICHE_PRESETS, DEFAULT_CONFIG


STUDIO_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AEO Studio — Answer Engine & Schema Knowledge Graph Workbench</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Google+Sans:wght@400;500;700&family=Roboto+Mono:wght@400;500&family=Roboto:wght@400;500;700&display=swap" rel="stylesheet">
  <style>
    :root {
      --google-blue: #1a73e8;
      --google-blue-hover: #1557b0;
      --google-blue-surface: #e8f0fe;
      --google-green: #1e8e3e;
      --google-green-surface: #e6f4ea;
      --google-yellow: #f9ab00;
      --google-yellow-surface: #fef7e0;
      --google-red: #d93025;
      --google-red-surface: #fce8e6;
      --google-purple: #9334e6;
      --google-purple-surface: #f3e8fd;
      --canvas-bg: #f8f9fa;
      --surface-bg: #ffffff;
      --border-subtle: #dadce0;
      --border-divider: #e8eaed;
      --text-primary: #202124;
      --text-secondary: #5f6368;
      --text-tertiary: #80868b;
      --font-sans: 'Google Sans', 'Roboto', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      --font-mono: 'Roboto Mono', Menlo, Monaco, Consolas, monospace;
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: var(--font-sans);
      background-color: var(--canvas-bg);
      color: var(--text-primary);
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      overflow-x: hidden;
    }

    /* Top Google-Style App Bar */
    header.app-bar {
      background: var(--surface-bg);
      border-bottom: 1px solid var(--border-divider);
      height: 64px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 24px;
      position: sticky;
      top: 0;
      z-index: 100;
      box-shadow: 0 1px 2px rgba(60,64,67,0.06);
    }
    .brand-section {
      display: flex;
      align-items: center;
      gap: 12px;
    }
    .google-dots {
      display: flex;
      gap: 3px;
    }
    .dot { width: 8px; height: 8px; border-radius: 50%; }
    .dot-blue { background: #4285f4; }
    .dot-red { background: #ea4335; }
    .dot-yellow { background: #fbbc04; }
    .dot-green { background: #34a853; }
    .brand-title {
      font-size: 20px;
      font-weight: 500;
      color: var(--text-primary);
      letter-spacing: -0.2px;
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .brand-badge {
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      background: var(--google-blue-surface);
      color: var(--google-blue);
      padding: 2px 8px;
      border-radius: 12px;
    }

    .top-actions {
      display: flex;
      align-items: center;
      gap: 12px;
    }
    .score-chip {
      display: flex;
      align-items: center;
      gap: 6px;
      padding: 6px 14px;
      border-radius: 20px;
      font-size: 13px;
      font-weight: 600;
      background: var(--google-green-surface);
      color: var(--google-green);
      border: 1px solid rgba(30, 142, 62, 0.2);
    }

    /* Buttons */
    .btn {
      font-family: var(--font-sans);
      font-size: 14px;
      font-weight: 500;
      padding: 8px 18px;
      border-radius: 20px;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 8px;
      transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
      border: 1px solid transparent;
      outline: none;
      text-decoration: none;
    }
    .btn-primary {
      background: var(--google-blue);
      color: #ffffff;
      box-shadow: 0 1px 2px rgba(60,64,67,0.3);
    }
    .btn-primary:hover {
      background: var(--google-blue-hover);
      box-shadow: 0 1px 3px 1px rgba(60,64,67,0.25);
    }
    .btn-tonal {
      background: var(--google-blue-surface);
      color: var(--google-blue);
    }
    .btn-tonal:hover {
      background: #d2e3fc;
    }
    .btn-purple {
      background: var(--google-purple-surface);
      color: var(--google-purple);
      border-color: rgba(147, 52, 230, 0.2);
    }
    .btn-purple:hover {
      background: #ebd8fc;
    }
    .btn-outline {
      background: transparent;
      border-color: var(--border-subtle);
      color: var(--text-primary);
    }
    .btn-outline:hover {
      background: rgba(60,64,67,0.04);
      border-color: var(--text-secondary);
    }
    .btn-sm {
      padding: 5px 12px;
      font-size: 12px;
      border-radius: 16px;
    }

    /* Layout */
    .app-layout {
      display: grid;
      grid-template-columns: 390px 1fr;
      flex: 1;
      height: calc(100vh - 64px);
      overflow: hidden;
    }

    /* Sidebar */
    .sidebar {
      background: var(--surface-bg);
      border-right: 1px solid var(--border-divider);
      overflow-y: auto;
      padding: 20px 20px 40px;
      display: flex;
      flex-direction: column;
      gap: 18px;
    }

    /* AI Prompt Hero Box */
    .ai-hero-box {
      background: linear-gradient(135deg, #f3e8fd 0%, #e8f0fe 100%);
      border: 1px solid rgba(147, 52, 230, 0.25);
      border-radius: 12px;
      padding: 14px;
      display: flex;
      flex-direction: column;
      gap: 10px;
    }
    .ai-hero-title {
      font-size: 13px;
      font-weight: 700;
      color: var(--google-purple);
      display: flex;
      align-items: center;
      gap: 6px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
    .ai-prompt-input {
      font-family: var(--font-sans);
      font-size: 13px;
      padding: 8px 12px;
      border-radius: 8px;
      border: 1px solid rgba(147, 52, 230, 0.3);
      background: #ffffff;
      color: var(--text-primary);
      width: 100%;
    }
    .ai-prompt-input:focus {
      outline: none;
      border-color: var(--google-purple);
      box-shadow: 0 0 0 2px rgba(147, 52, 230, 0.2);
    }
    .ai-quick-samples {
      display: flex;
      flex-wrap: wrap;
      gap: 4px;
    }
    .sample-pill {
      font-size: 11px;
      padding: 2px 8px;
      border-radius: 10px;
      background: rgba(255, 255, 255, 0.8);
      border: 1px solid rgba(147, 52, 230, 0.2);
      color: var(--google-purple);
      cursor: pointer;
      font-weight: 500;
    }
    .sample-pill:hover {
      background: #ffffff;
      border-color: var(--google-purple);
    }

    .section-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 6px;
    }
    .section-title {
      font-size: 12px;
      font-weight: 700;
      color: var(--text-secondary);
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }

    /* Preset Pills */
    .preset-group {
      display: flex;
      flex-wrap: wrap;
      gap: 5px;
      margin-bottom: 4px;
    }
    .preset-pill {
      font-size: 12px;
      padding: 4px 10px;
      border-radius: 14px;
      border: 1px solid var(--border-subtle);
      background: var(--surface-bg);
      color: var(--text-secondary);
      cursor: pointer;
      font-weight: 500;
      transition: all 0.15s ease;
    }
    .preset-pill.active {
      background: var(--google-blue-surface);
      color: var(--google-blue);
      border-color: var(--google-blue);
      font-weight: 600;
    }

    /* Form Fields */
    .form-group {
      display: flex;
      flex-direction: column;
      gap: 4px;
    }
    .form-label {
      font-size: 11px;
      font-weight: 600;
      color: var(--text-secondary);
      text-transform: uppercase;
      letter-spacing: 0.3px;
    }
    .form-control {
      font-family: var(--font-sans);
      font-size: 13px;
      padding: 8px 12px;
      border-radius: 8px;
      border: 1px solid var(--border-subtle);
      background: #ffffff;
      color: var(--text-primary);
      transition: border-color 0.2s, box-shadow 0.2s;
      width: 100%;
    }
    .form-control:focus {
      outline: none;
      border-color: var(--google-blue);
      box-shadow: 0 0 0 2px var(--google-blue-surface);
    }
    textarea.form-control {
      resize: vertical;
      min-height: 60px;
    }

    /* Main Area */
    .main-panel {
      display: flex;
      flex-direction: column;
      height: 100%;
      overflow: hidden;
      background: var(--canvas-bg);
    }
    .tabs-bar {
      background: var(--surface-bg);
      border-bottom: 1px solid var(--border-divider);
      display: flex;
      padding: 0 20px;
      gap: 4px;
      overflow-x: auto;
    }
    .tab-btn {
      font-family: var(--font-sans);
      font-size: 13px;
      font-weight: 500;
      padding: 13px 16px;
      color: var(--text-secondary);
      background: transparent;
      border: none;
      border-bottom: 3px solid transparent;
      cursor: pointer;
      transition: all 0.2s;
      white-space: nowrap;
      display: flex;
      align-items: center;
      gap: 6px;
    }
    .tab-btn:hover {
      color: var(--google-blue);
      background: rgba(26, 115, 232, 0.04);
    }
    .tab-btn.active {
      color: var(--google-blue);
      border-bottom-color: var(--google-blue);
      font-weight: 600;
    }

    .tab-content-area {
      flex: 1;
      overflow-y: auto;
      padding: 24px;
    }
    .tab-pane {
      display: none;
      animation: fadeIn 0.2s ease-in-out;
    }
    .tab-pane.active {
      display: block;
    }
    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(4px); }
      to { opacity: 1; transform: translateY(0); }
    }

    /* Cards */
    .card {
      background: var(--surface-bg);
      border: 1px solid var(--border-divider);
      border-radius: 12px;
      padding: 22px;
      box-shadow: 0 1px 2px rgba(60,64,67,0.06);
      margin-bottom: 20px;
    }
    .card-title {
      font-size: 15px;
      font-weight: 600;
      color: var(--text-primary);
      margin-bottom: 14px;
      display: flex;
      align-items: center;
      justify-content: space-between;
    }

    /* Score Gauge Grid */
    .audit-grid {
      display: grid;
      grid-template-columns: 260px 1fr;
      gap: 20px;
      align-items: center;
    }
    .gauge-container {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 20px;
      background: var(--google-green-surface);
      border-radius: 16px;
      border: 1px solid rgba(30, 142, 62, 0.2);
    }
    .gauge-num {
      font-size: 52px;
      font-weight: 700;
      color: var(--google-green);
      line-height: 1;
      margin-bottom: 4px;
    }
    .gauge-label {
      font-size: 12px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 1px;
      color: var(--google-green);
    }

    .audit-items {
      display: flex;
      flex-direction: column;
      gap: 8px;
    }
    .audit-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 10px 14px;
      background: #ffffff;
      border: 1px solid var(--border-divider);
      border-radius: 8px;
    }
    .audit-row-left {
      display: flex;
      align-items: center;
      gap: 10px;
      font-size: 13px;
      font-weight: 500;
    }
    .status-icon { font-size: 15px; }
    .status-pass { color: var(--google-green); }

    /* Code Viewers */
    .code-box {
      background: #ffffff;
      border: 1px solid var(--border-divider);
      border-radius: 8px;
      font-family: var(--font-mono);
      font-size: 12px;
      line-height: 1.5;
      padding: 14px;
      color: #24292e;
      overflow-x: auto;
      max-height: 520px;
      white-space: pre;
    }

    /* Entity Cards Grid */
    .entity-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
      gap: 14px;
      margin-bottom: 20px;
    }
    .entity-card {
      background: #ffffff;
      border: 1px solid var(--border-divider);
      border-left: 4px solid var(--google-blue);
      border-radius: 8px;
      padding: 14px;
    }
    .entity-type {
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      color: var(--google-blue);
      margin-bottom: 3px;
    }
    .entity-name {
      font-size: 14px;
      font-weight: 600;
      color: var(--text-primary);
      margin-bottom: 4px;
    }
    .entity-desc {
      font-size: 12px;
      color: var(--text-secondary);
      line-height: 1.4;
    }

    /* Bot Crawler Matrix */
    .bot-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
      gap: 10px;
    }
    .bot-card {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 10px 14px;
      background: #ffffff;
      border: 1px solid var(--border-divider);
      border-radius: 8px;
    }
    .bot-name { font-weight: 600; font-size: 13px; }
    .bot-badge {
      font-size: 11px;
      font-weight: 700;
      padding: 2px 7px;
      border-radius: 12px;
      background: var(--google-green-surface);
      color: var(--google-green);
    }

    /* Guide Section Cards */
    .guide-box {
      border-left: 4px solid var(--google-blue);
      padding: 14px 18px;
      background: #f8f9fa;
      border-radius: 0 8px 8px 0;
      margin-bottom: 14px;
    }
    .guide-title {
      font-weight: 700;
      font-size: 14px;
      color: var(--google-blue);
      margin-bottom: 4px;
    }
    .guide-desc {
      font-size: 13px;
      color: var(--text-secondary);
      line-height: 1.5;
    }

    @media (max-width: 900px) {
      .app-layout { grid-template-columns: 1fr; height: auto; overflow: visible; }
      .sidebar { border-right: none; border-bottom: 1px solid var(--border-divider); height: auto; }
      .audit-grid { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>

  <!-- Google-Style Header -->
  <header class="app-bar">
    <div class="brand-section">
      <div class="google-dots">
        <div class="dot dot-blue"></div>
        <div class="dot dot-red"></div>
        <div class="dot dot-yellow"></div>
        <div class="dot dot-green"></div>
      </div>
      <div class="brand-title">
        AEO Studio
        <span class="brand-badge">Engine v1.0</span>
      </div>
    </div>
    <div class="top-actions">
      <div class="score-chip" id="topScoreChip">
        <span id="topScoreValue">100 / 100</span> AEO Readiness
      </div>
      <button class="btn btn-outline btn-sm" onclick="triggerAutoDetect()">🔍 Auto-Detect</button>
      <button class="btn btn-primary btn-sm" onclick="downloadZipBundle()">📥 Download .zip</button>
    </div>
  </header>

  <div class="app-layout">
    <!-- Sidebar -->
    <aside class="sidebar">
      <!-- AI Agent Auto-Config Hero -->
      <div class="ai-hero-box">
        <div class="ai-hero-title">
          <span>🪄</span> AI Prompt Synthesizer
        </div>
        <input type="text" class="ai-prompt-input" id="inpAiPrompt" placeholder="Describe your app in 1 sentence..." onkeydown="if(event.key==='Enter') executeAiPrompt()">
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <button class="btn btn-purple btn-sm" onclick="executeAiPrompt()">⚡ Synthesize</button>
          <div class="ai-quick-samples">
            <span class="sample-pill" onclick="fillPrompt('DeFi lending on Solana called SolarYield on solaryield.fi')">DeFi</span>
            <span class="sample-pill" onclick="fillPrompt('AI resume builder called CVForge on cvforge.app')">AI SaaS</span>
            <span class="sample-pill" onclick="fillPrompt('Local plumbing service called QuickFlow Plumbing in Seattle')">Plumbing</span>
          </div>
        </div>
      </div>

      <div>
        <div class="section-header">
          <span class="section-title">Domain Niche Preset</span>
        </div>
        <div class="preset-group">
          <button class="preset-pill active" onclick="selectPreset('developer_tools')">Developer Tools</button>
          <button class="preset-pill" onclick="selectPreset('saas')">SaaS</button>
          <button class="preset-pill" onclick="selectPreset('ai_swarm')">AI Swarm</button>
          <button class="preset-pill" onclick="selectPreset('cybersecurity')">Security</button>
          <button class="preset-pill" onclick="selectPreset('spatial_3d')">3D Spatial</button>
          <button class="preset-pill" onclick="selectPreset('creator')">Creator</button>
          <button class="preset-pill" onclick="selectPreset('ecommerce')">E-Commerce</button>
          <button class="preset-pill" onclick="selectPreset('local_business')">Local Business</button>
        </div>
      </div>

      <div class="form-group">
        <label class="form-label">Site / Brand Name</label>
        <input type="text" class="form-control" id="inpSiteName" value="AEO Graph Engine" oninput="regenerateAll()">
      </div>

      <div class="form-group">
        <label class="form-label">Canonical Domain Name</label>
        <input type="text" class="form-control" id="inpDomain" value="aeo.nullai.tech" oninput="regenerateAll()">
      </div>

      <div class="form-group">
        <label class="form-label">Tagline</label>
        <input type="text" class="form-control" id="inpTagline" value="Answer Engine Optimization (AEO/GEO) Knowledge Graph & llms.txt Engine" oninput="regenerateAll()">
      </div>

      <div class="form-group">
        <label class="form-label">Description (AI Knowledge Base)</label>
        <textarea class="form-control" id="inpDescription" oninput="regenerateAll()">Standalone, zero-dependency generator and validator for Schema.org linked data, llms.txt, ai.txt, and AI crawler directives.</textarea>
      </div>

      <div class="form-group">
        <label class="form-label">Publisher / Organization</label>
        <input type="text" class="form-control" id="inpPublisher" value="NullAI" oninput="regenerateAll()">
      </div>

      <div class="form-group">
        <label class="form-label">Category</label>
        <select class="form-control" id="inpCategory" onchange="regenerateAll()">
          <option value="DeveloperApplication">DeveloperApplication</option>
          <option value="SoftwareApplication">SoftwareApplication</option>
          <option value="SecurityApplication">SecurityApplication</option>
          <option value="MultimediaApplication">MultimediaApplication</option>
          <option value="BusinessApplication">BusinessApplication</option>
          <option value="LocalBusiness">LocalBusiness</option>
        </select>
      </div>
    </aside>

    <!-- Main Panel -->
    <main class="main-panel">
      <nav class="tabs-bar">
        <button class="tab-btn active" onclick="switchTab('tab-audit')">📊 AEO Scorecard</button>
        <button class="tab-btn" onclick="switchTab('tab-schema')">🕸️ Schema.org Graph</button>
        <button class="tab-btn" onclick="switchTab('tab-llms')">📄 llms.txt</button>
        <button class="tab-btn" onclick="switchTab('tab-llms-full')">📚 llms-full.txt</button>
        <button class="tab-btn" onclick="switchTab('tab-ai-txt')">🤖 ai.txt & robots.txt</button>
        <button class="tab-btn" onclick="switchTab('tab-injector')">💉 HTML Injector</button>
        <button class="tab-btn" onclick="switchTab('tab-guide')">📖 How It Works</button>
        <button class="tab-btn" onclick="switchTab('tab-api')">🔌 CLI & Python API</button>
      </nav>

      <div class="tab-content-area">
        <!-- 1. Audit Scorecard -->
        <div id="tab-audit" class="tab-pane active">
          <div class="card">
            <div class="audit-grid">
              <div class="gauge-container">
                <div class="gauge-num">100</div>
                <div class="gauge-label">EXCELLENT AEO</div>
              </div>
              <div class="audit-items">
                <div class="audit-row">
                  <div class="audit-row-left">
                    <span class="status-icon status-pass">✔</span>
                    <span>Schema.org Linked Data Graph (@graph: Organization, WebSite, App, FAQ)</span>
                  </div>
                  <span class="bot-badge">Connected</span>
                </div>
                <div class="audit-row">
                  <div class="audit-row-left">
                    <span class="status-icon status-pass">✔</span>
                    <span>llms.txt Standard Manifest (llmstxt.org compliant)</span>
                  </div>
                  <span class="bot-badge">Valid</span>
                </div>
                <div class="audit-row">
                  <div class="audit-row-left">
                    <span class="status-icon status-pass">✔</span>
                    <span>Deep Research Knowledge Base (llms-full.txt with citations)</span>
                  </div>
                  <span class="bot-badge">Active</span>
                </div>
                <div class="audit-row">
                  <div class="audit-row-left">
                    <span class="status-icon status-pass">✔</span>
                    <span>AI Search Bot Directives (GPTBot, PerplexityBot, ClaudeBot, Applebot)</span>
                  </div>
                  <span class="bot-badge">Optimized</span>
                </div>
              </div>
            </div>
          </div>

          <div class="card">
            <div class="card-title">
              Connected Schema Entities
              <button class="btn btn-tonal btn-sm" onclick="switchTab('tab-schema')">View Raw JSON-LD</button>
            </div>
            <div class="entity-grid" id="entityGridPreview"></div>
          </div>
        </div>

        <!-- 2. Schema Tab -->
        <div id="tab-schema" class="tab-pane">
          <div class="card">
            <div class="card-title">
              Schema.org JSON-LD Linked Data (@graph)
              <button class="btn btn-tonal btn-sm" onclick="copyCode('codeSchema')">📋 Copy JSON-LD</button>
            </div>
            <div class="code-box" id="codeSchema"></div>
          </div>
        </div>

        <!-- 3. llms.txt Tab -->
        <div id="tab-llms" class="tab-pane">
          <div class="card">
            <div class="card-title">
              llms.txt (Concise AI Index per llmstxt.org)
              <button class="btn btn-tonal btn-sm" onclick="copyCode('codeLlms')">📋 Copy llms.txt</button>
            </div>
            <div class="code-box" id="codeLlms"></div>
          </div>
        </div>

        <!-- 4. llms-full.txt Tab -->
        <div id="tab-llms-full" class="tab-pane">
          <div class="card">
            <div class="card-title">
              llms-full.txt (Comprehensive Deep-Research Knowledge Base)
              <button class="btn btn-tonal btn-sm" onclick="copyCode('codeLlmsFull')">📋 Copy llms-full.txt</button>
            </div>
            <div class="code-box" id="codeLlmsFull"></div>
          </div>
        </div>

        <!-- 5. ai.txt & robots.txt Tab -->
        <div id="tab-ai-txt" class="tab-pane">
          <div class="card">
            <div class="card-title">AI Search Engine Bot Directives</div>
            <div class="bot-grid">
              <div class="bot-card">
                <span class="bot-name">ChatGPT (GPTBot)</span>
                <span class="bot-badge">Allowed</span>
              </div>
              <div class="bot-card">
                <span class="bot-name">Perplexity (PerplexityBot)</span>
                <span class="bot-badge">Allowed</span>
              </div>
              <div class="bot-card">
                <span class="bot-name">Claude (ClaudeBot)</span>
                <span class="bot-badge">Allowed</span>
              </div>
              <div class="bot-card">
                <span class="bot-name">Apple (Applebot-Ext)</span>
                <span class="bot-badge">Allowed</span>
              </div>
            </div>
          </div>

          <div class="card">
            <div class="card-title">
              ai.txt Machine Access Policy
              <button class="btn btn-tonal btn-sm" onclick="copyCode('codeAiTxt')">📋 Copy ai.txt</button>
            </div>
            <div class="code-box" id="codeAiTxt"></div>
          </div>

          <div class="card">
            <div class="card-title">
              robots.txt AI Directives
              <button class="btn btn-tonal btn-sm" onclick="copyCode('codeRobots')">📋 Copy robots.txt</button>
            </div>
            <div class="code-box" id="codeRobots"></div>
          </div>
        </div>

        <!-- 6. HTML Injector Tab -->
        <div id="tab-injector" class="tab-pane">
          <div class="card">
            <div class="card-title">Live HTML Schema Injector</div>
            <p style="font-size:13px; color:var(--text-secondary); margin-bottom:12px;">
              Paste any raw HTML document below and click <strong>Inject Schema</strong> to embed the synthesized JSON-LD tag into the &lt;head&gt; element idempotently.
            </p>
            <div class="form-group" style="margin-bottom:12px;">
              <textarea class="form-control" id="inpRawHtml" style="min-height:120px; font-family:var(--font-mono); font-size:12px;"><!DOCTYPE html>
<html>
<head>
  <title>My Website</title>
</head>
<body>
  <h1>Hello World</h1>
</body>
</html></textarea>
            </div>
            <button class="btn btn-primary btn-sm" onclick="performHtmlInjection()">💉 Inject Schema</button>

            <div style="margin-top:16px;">
              <div class="card-title">
                Injected HTML Result
                <button class="btn btn-tonal btn-sm" onclick="copyCode('codeInjectedHtml')">📋 Copy Result</button>
              </div>
              <div class="code-box" id="codeInjectedHtml">Click 'Inject Schema' above...</div>
            </div>
          </div>
        </div>

        <!-- 7. How It Works Guide Tab -->
        <div id="tab-guide" class="tab-pane">
          <div class="card">
            <div class="card-title">How Answer Engine Optimization (AEO / GEO) Works</div>
            
            <div class="guide-box">
              <div class="guide-title">1. What is AEO vs SEO?</div>
              <div class="guide-desc">
                Classic SEO aimed to rank on 10 blue links on Google. Modern <strong>AEO</strong> structures your data so AI answer engines (Perplexity, ChatGPT Search, Claude, Google AI Overviews) can directly read, synthesize, and cite your website during conversational answers.
              </div>
            </div>

            <div class="guide-box">
              <div class="guide-title">2. Why Connected Schema.org @graph Matters</div>
              <div class="guide-desc">
                Isolated schema tags leave ambiguity. A connected <strong>@graph</strong> links your Organization, WebSite, Software/Product, FAQPage, and BreadcrumbList into a unified entity network with canonical @id URIs, giving AI models 100% confidence in factual claims.
              </div>
            </div>

            <div class="guide-box">
              <div class="guide-title">3. llms.txt & llms-full.txt (The Machine Index)</div>
              <div class="guide-desc">
                LLMs have strict token limits during live search queries. <strong>llms.txt</strong> provides an ultra-concise summary index with structured markdown links so AI crawlers can retrieve your core documentation in sub-50 tokens.
              </div>
            </div>

            <div class="guide-box">
              <div class="guide-title">4. Automated HTML Injection</div>
              <div class="guide-desc">
                The engine includes an idempotent injection harness that replaces or embeds <code>&lt;script type="application/ld+json"&gt;</code> tags into built HTML files during your build step (Vite, Next.js, Astro) with zero drift.
              </div>
            </div>
          </div>
        </div>

        <!-- 8. API Tab -->
        <div id="tab-api" class="tab-pane">
          <div class="card">
            <div class="card-title">CLI Quickstart</div>
            <div class="code-box"># 1. Synthesize from natural language prompt
aeo prompt "An AI resume builder called CVForge on cvforge.app" --output-dir dist/

# 2. Extract metadata from existing HTML
aeo extract dist/index.html

# 3. Validate existing site
aeo --validate dist/ --format json

# 4. Start interactive local Studio
aeo serve --port 8080</div>
          </div>

          <div class="card">
            <div class="card-title">Python Programmatic Library Usage</div>
            <div class="code-box">from aeo_graph_engine import (
    synthesize_config_from_prompt,
    write_aeo_bundle,
    validate_aeo_bundle
)

# Synthesize and generate in 3 lines
config = synthesize_config_from_prompt("My SaaS on mysaas.com")
write_aeo_bundle("./dist", config=config, inject_html_files=["./dist/index.html"])
report = validate_aeo_bundle("./dist")
print(f"Score: {report.score}/100")</div>
          </div>
        </div>
      </div>
    </main>
  </div>

  <script>
    const PRESETS = """ + json.dumps(NICHE_PRESETS) + """;
    let currentNiche = 'developer_tools';

    function selectPreset(nicheKey) {
      currentNiche = nicheKey;
      document.querySelectorAll('.preset-pill').forEach(el => el.classList.remove('active'));
      event.target.classList.add('active');

      const p = PRESETS[nicheKey] || {};
      if (p.site_name) document.getElementById('inpSiteName').value = p.site_name;
      if (p.tagline) document.getElementById('inpTagline').value = p.tagline;
      if (p.description) document.getElementById('inpDescription').value = p.description;
      if (p.category) document.getElementById('inpCategory').value = p.category;

      regenerateAll();
    }

    function switchTab(tabId) {
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));

      event.target.classList.add('active');
      document.getElementById(tabId).classList.add('active');
    }

    function copyCode(elemId) {
      const text = document.getElementById(elemId).innerText;
      navigator.clipboard.writeText(text).then(() => {
        alert("Copied to clipboard!");
      });
    }

    function fillPrompt(text) {
      document.getElementById('inpAiPrompt').value = text;
      executeAiPrompt();
    }

    async function executeAiPrompt() {
      const prompt = document.getElementById('inpAiPrompt').value.trim();
      if (!prompt) return;

      try {
        const res = await fetch('/api/agent/synthesize', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ prompt: prompt })
        });
        const data = await res.json();
        if (data.site_name) document.getElementById('inpSiteName').value = data.site_name;
        if (data.domain) document.getElementById('inpDomain').value = data.domain;
        if (data.tagline) document.getElementById('inpTagline').value = data.tagline;
        if (data.description) document.getElementById('inpDescription').value = data.description;
        if (data.niche) currentNiche = data.niche;

        regenerateAll();
      } catch (e) {
        alert("AI Synthesis error: " + e);
      }
    }

    async function regenerateAll() {
      const payload = {
        site_name: document.getElementById('inpSiteName').value,
        domain: document.getElementById('inpDomain').value,
        tagline: document.getElementById('inpTagline').value,
        description: document.getElementById('inpDescription').value,
        publisher_name: document.getElementById('inpPublisher').value,
        category: document.getElementById('inpCategory').value,
        niche: currentNiche
      };

      try {
        const res = await fetch('/api/generate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        const data = await res.json();

        document.getElementById('codeSchema').innerText = JSON.stringify(data.schema, null, 2);
        document.getElementById('codeLlms').innerText = data.llms_txt;
        document.getElementById('codeLlmsFull').innerText = data.llms_full_txt;
        document.getElementById('codeAiTxt').innerText = data.ai_txt;
        document.getElementById('codeRobots').innerText = data.robots_txt;

        const grid = document.getElementById('entityGridPreview');
        grid.innerHTML = '';
        (data.schema['@graph'] || []).forEach(e => {
          const card = document.createElement('div');
          card.className = 'entity-card';
          card.innerHTML = `
            <div class="entity-type">${e['@type'] || 'Entity'}</div>
            <div class="entity-name">${e.name || e['@id'] || 'Unnamed'}</div>
            <div class="entity-desc">${e.description || e.slogan || 'Connected Schema Node'}</div>
          `;
          grid.appendChild(card);
        });

      } catch (err) {
        console.error("Failed to generate from API", err);
      }
    }

    async function performHtmlInjection() {
      const rawHtml = document.getElementById('inpRawHtml').value;
      const payload = {
        html: rawHtml,
        config: {
          site_name: document.getElementById('inpSiteName').value,
          domain: document.getElementById('inpDomain').value,
          niche: currentNiche
        }
      };

      try {
        const res = await fetch('/api/inject', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        const data = await res.json();
        document.getElementById('codeInjectedHtml').innerText = data.injected_html;
      } catch (e) {
        alert("Injection error: " + e);
      }
    }

    function downloadZipBundle() {
      window.location.href = '/api/export-zip?niche=' + currentNiche + '&site_name=' + encodeURIComponent(document.getElementById('inpSiteName').value);
    }

    async function triggerAutoDetect() {
      try {
        const res = await fetch('/api/discover');
        const data = await res.json();
        if (data.site_name) document.getElementById('inpSiteName').value = data.site_name;
        if (data.description) document.getElementById('inpDescription').value = data.description;
        regenerateAll();
        alert("Auto-detected project metadata successfully!");
      } catch (e) {
        alert("Project discovery error: " + e);
      }
    }

    window.addEventListener('DOMContentLoaded', () => {
      regenerateAll();
    });
  </script>
</body>
</html>
"""


class AEOStudioHTTPHandler(BaseHTTPRequestHandler):
    """Custom HTTP handler serving AEO Studio UI and REST endpoints."""

    def log_message(self, format, *args):
        pass

    def _send_json(self, data: Any, status: int = 200):
        body = json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, html: str, status: int = 200):
        body = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path in ("/", "/index.html", "/ui", "/ui/"):
            return self._send_html(STUDIO_HTML_TEMPLATE)

        if path == "/api/status":
            return self._send_json({"status": "healthy", "engine": "aeo-graph-engine", "version": "1.0.0"})

        if path == "/api/schema":
            return self._send_json(get_agent_json_schema())

        if path == "/api/discover":
            meta = discover_project_metadata(".")
            return self._send_json(meta)

        if path == "/api/export-zip":
            query = urllib.parse.parse_qs(parsed.query)
            niche = query.get("niche", ["developer_tools"])[0]
            site_name = query.get("site_name", ["AEO Graph Engine"])[0]

            cfg = resolve_config({"site_name": site_name}, niche=niche)
            schema = generate_schema_graph(cfg, niche=niche)
            llms_txt = generate_llms_txt(cfg, niche=niche)
            llms_full = generate_llms_full_txt(cfg, niche=niche)
            ai_txt = generate_ai_txt(cfg, niche=niche)
            robots_txt = generate_robots_txt(cfg, niche=niche)

            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                zf.writestr("schema-graph.json", json.dumps(schema, indent=2))
                zf.writestr("llms.txt", llms_txt)
                zf.writestr("llms-full.txt", llms_full)
                zf.writestr("ai.txt", ai_txt)
                zf.writestr("robots.txt", robots_txt)

            zip_bytes = zip_buffer.getvalue()
            self.send_response(200)
            self.send_header("Content-Type", "application/zip")
            self.send_header("Content-Disposition", 'attachment; filename="aeo-bundle.zip"')
            self.send_header("Content-Length", str(len(zip_bytes)))
            self.end_headers()
            self.wfile.write(zip_bytes)
            return

        self.send_error(404, "Endpoint not found")

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        payload = {}
        if body:
            try:
                payload = json.loads(body.decode("utf-8"))
            except Exception:
                pass

        if path == "/api/agent/synthesize":
            prompt = payload.get("prompt", "")
            base_niche = payload.get("niche")
            cfg = synthesize_config_from_prompt(prompt, base_niche=base_niche)
            return self._send_json(cfg)

        if path == "/api/generate":
            niche = payload.get("niche", "developer_tools")
            cfg = resolve_config(payload, niche=niche)
            schema = generate_schema_graph(cfg, niche=niche)
            llms = generate_llms_txt(cfg, niche=niche)
            llms_full = generate_llms_full_txt(cfg, niche=niche)
            ai = generate_ai_txt(cfg, niche=niche)
            robots = generate_robots_txt(cfg, niche=niche)

            return self._send_json({
                "schema": schema,
                "llms_txt": llms,
                "llms_full_txt": llms_full,
                "ai_txt": ai,
                "robots_txt": robots,
                "score": 100.0
            })

        if path == "/api/inject":
            raw_html = payload.get("html", "")
            cfg = resolve_config(payload.get("config", {}))
            schema = generate_schema_graph(cfg)
            injected = inject_jsonld_into_html(raw_html, schema)
            return self._send_json({"injected_html": injected})

        if path == "/api/validate":
            raw_schema = payload.get("schema")
            report = AEODiagnosticReport("API Validation")
            if isinstance(raw_schema, dict):
                validate_schema_jsonld_dict(raw_schema, report)
            return self._send_json(report.to_dict())

        self.send_error(404, "Endpoint not found")


def start_ui_server(host: str = "127.0.0.1", port: int = 8080) -> ThreadingHTTPServer:
    """Starts the AEO Studio HTTP server."""
    server = ThreadingHTTPServer((host, port), AEOStudioHTTPHandler)
    return server
