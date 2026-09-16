"""
Unit tests for AEO Studio UI HTTP server and REST endpoints.
"""

import threading
import json
import urllib.request
import urllib.error
from aeo_graph_engine.ui_server import start_ui_server


def test_ui_server_get_html():
    server = start_ui_server(host="127.0.0.1", port=0)
    host, port = server.server_address
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()

    try:
        url = f"http://{host}:{port}/"
        with urllib.request.urlopen(url) as response:
            assert response.status == 200
            html = response.read().decode("utf-8")
            assert "AEO Studio" in html
            assert "Google Sans" in html
            assert "google-dots" in html
            assert "Live Multi-Page AEO &amp; AI Readiness Crawler" in html or "Live Multi-Page AEO & AI Readiness Crawler" in html

        # Test API Status
        status_url = f"http://{host}:{port}/api/status"
        with urllib.request.urlopen(status_url) as response:
            assert response.status == 200
            data = json.loads(response.read().decode("utf-8"))
            assert data["status"] == "healthy"
            assert data["engine"] == "aeo-graph-engine"

        # Test API Generate
        gen_url = f"http://{host}:{port}/api/generate"
        req_data = json.dumps({"site_name": "API Tester", "niche": "saas"}).encode("utf-8")
        req = urllib.request.Request(gen_url, data=req_data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req) as response:
            assert response.status == 200
            gen_res = json.loads(response.read().decode("utf-8"))
            assert "schema" in gen_res
            assert "llms_txt" in gen_res
            assert "robots_txt" in gen_res

        # Test API Inject
        inj_url = f"http://{host}:{port}/api/inject"
        inj_data = json.dumps({"html": "<html><head><title>App</title></head><body></body></html>", "config": {"site_name": "App"}}).encode("utf-8")
        inj_req = urllib.request.Request(inj_url, data=inj_data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(inj_req) as response:
            assert response.status == 200
            inj_res = json.loads(response.read().decode("utf-8"))
            assert "<script type=\"application/ld+json\">" in inj_res["injected_html"]

        # Test API Live Scan endpoint on self
        scan_url = f"http://{host}:{port}/api/scan"
        scan_data = json.dumps({"url": f"http://{host}:{port}", "max_pages": 1}).encode("utf-8")
        scan_req = urllib.request.Request(scan_url, data=scan_data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(scan_req) as response:
            assert response.status == 200
            scan_res = json.loads(response.read().decode("utf-8"))
            assert "overall_aeo_score" in scan_res
            assert "category_scores" in scan_res
            assert "ai_engine_compatibility" in scan_res
            assert "backlink_and_distribution_intelligence" in scan_res

    finally:
        server.shutdown()
        server.server_close()
