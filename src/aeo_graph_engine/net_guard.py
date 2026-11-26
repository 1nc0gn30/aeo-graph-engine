"""
SSRF & Network Target Guard for AEO Graph Engine.
Strictly enforces http/https schemes and blocks loopback, RFC1918 private,
link-local (including AWS/GCP/Azure IMDS 169.254.169.254), multicast,
unspecified, and reserved IP addresses before any outbound connection or
HTTP redirect is followed.

Zero external runtime dependencies (Python standard library only).
"""

from __future__ import annotations

import ipaddress
import os
import re
import socket
import urllib.parse
import urllib.request
from typing import Optional

_BARE_HOST_RE = re.compile(
    r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+(?::\d{1,5})?(?:/.*)?$"
)

_BLOCKED_HOSTNAMES = {
    "localhost",
    "localhost.localdomain",
    "ip6-localhost",
    "ip6-loopback",
    "metadata.google.internal",
    "metadata.goog",
    "metadata",
    "instance-data",
}

_BLOCKED_SUFFIXES = (
    ".localhost",
    ".local",
    ".internal",
    ".localdomain",
    ".home.arpa",
)


class SSRFBlockedError(ValueError):
    """Raised when a target URL violates SSRF / scheme / private-IP policy."""


def _is_blocked_ip(ip_str: str) -> Optional[str]:
    """Returns a reason string if the IP is non-public/disallowed, else None."""
    try:
        addr = ipaddress.ip_address(ip_str.split("%")[0])
    except ValueError:
        return f"Invalid IP address '{ip_str}'"

    # Unwrap IPv4-mapped IPv6 addresses (e.g., ::ffff:127.0.0.1)
    if isinstance(addr, ipaddress.IPv6Address) and addr.ipv4_mapped is not None:
        addr = addr.ipv4_mapped

    if addr.is_loopback:
        return f"Loopback address blocked ({addr})"
    if addr.is_link_local:
        return f"Link-local / cloud metadata address blocked ({addr})"
    if addr.is_private:
        return f"Private network address blocked ({addr})"
    if addr.is_multicast:
        return f"Multicast address blocked ({addr})"
    if addr.is_unspecified:
        return f"Unspecified address blocked ({addr})"
    if addr.is_reserved:
        return f"Reserved IP address blocked ({addr})"
    return None


def validate_public_url(raw_url: str, *, allow_private: bool = False) -> str:
    """
    Validates and normalizes a target URL for outbound scanning/crawling.

    - Strictly requires http:// or https:// (never rewrites file://, ftp://, etc.).
    - Bare hostnames without any scheme (e.g. 'example.com/docs') are prefixed with https://.
    - Rejects embedded userinfo/credentials and malformed ports.
    - Unless allow_private=True (or AEO_ALLOW_PRIVATE_URLS=1 for test harnesses),
      blocks loopback, RFC1918 private, link-local/IMDS, multicast, and reserved IPs.
    """
    if not isinstance(raw_url, str) or not raw_url.strip():
        raise SSRFBlockedError("Target URL must be a non-empty string.")

    url = raw_url.strip()

    # Reject control characters or whitespace inside URL
    if any(ord(ch) < 32 or ch.isspace() for ch in url):
        raise SSRFBlockedError("Target URL contains invalid whitespace or control characters.")

    # Check scheme explicitly — never silently prepend https:// onto file://, ftp://, etc.
    if "://" in url:
        scheme = url.split("://", 1)[0].lower()
        if scheme not in ("http", "https"):
            raise SSRFBlockedError(f"Unsupported URL scheme '{scheme}://'; only http:// and https:// are permitted.")
    elif ":" in url.split("/", 1)[0]:
        # Could be host:port OR a scheme like javascript:, data:, file:
        head = url.split("/", 1)[0]
        left, _, right = head.partition(":")
        if right.isdigit() and "." in left:
            url = "https://" + url
        else:
            raise SSRFBlockedError(f"Unsupported or malformed URL scheme '{left}:'; only http:// and https:// are permitted.")
    elif _BARE_HOST_RE.match(url):
        url = "https://" + url
    else:
        raise SSRFBlockedError(f"Invalid target URL '{url}'; expected an http:// or https:// URL.")

    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise SSRFBlockedError(f"Unsupported URL scheme '{parsed.scheme}'; only http and https are permitted.")

    if parsed.username is not None or parsed.password is not None:
        raise SSRFBlockedError("Credentials embedded in target URL are not permitted.")

    try:
        port = parsed.port
    except ValueError as exc:
        raise SSRFBlockedError(f"Invalid port in target URL: {exc}") from exc

    if port is not None and not (1 <= port <= 65535):
        raise SSRFBlockedError(f"Port out of range: {port}")

    hostname = (parsed.hostname or "").strip().lower().rstrip(".")
    if not hostname:
        raise SSRFBlockedError("Target URL is missing a valid hostname.")

    effective_allow_private = allow_private or os.environ.get("AEO_ALLOW_PRIVATE_URLS") == "1"
    if effective_allow_private:
        return url

    # 1. Explicit hostname blocklist
    if hostname in _BLOCKED_HOSTNAMES or any(hostname.endswith(sfx) for sfx in _BLOCKED_SUFFIXES):
        raise SSRFBlockedError(f"Access to internal/local hostname '{hostname}' is blocked by SSRF policy.")

    # 2. Direct IP literal check (blocks before DNS)
    try:
        ipaddress.ip_address(hostname)
        reason = _is_blocked_ip(hostname)
        if reason:
            raise SSRFBlockedError(f"SSRF policy violation: {reason}.")
        return url
    except ValueError:
        pass  # Not an IP literal; resolve via DNS

    # 3. DNS resolution check — block if ANY resolved address is non-public
    try:
        addr_infos = socket.getaddrinfo(hostname, port or (443 if parsed.scheme == "https" else 80), type=socket.SOCK_STREAM)
    except socket.gaierror:
        # Unresolvable external domain — safe to let caller surface normal fetch/DNS error
        return url

    for info in addr_infos:
        sockaddr = info[4]
        ip_str = sockaddr[0]
        reason = _is_blocked_ip(ip_str)
        if reason:
            raise SSRFBlockedError(f"SSRF policy violation: '{hostname}' resolves to blocked address ({reason}).")

    return url


class _SafeRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Re-validates every HTTP redirect destination against SSRF policy."""

    def __init__(self, allow_private: bool = False):
        super().__init__()
        self._allow_private = allow_private

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        resolved = urllib.parse.urljoin(req.full_url, newurl)
        validate_public_url(resolved, allow_private=self._allow_private)
        return super().redirect_request(req, fp, code, msg, headers, resolved)


def build_safe_opener(*, allow_private: bool = False) -> urllib.request.OpenerDirector:
    """Returns a urllib opener that validates redirects against SSRF policy."""
    return urllib.request.build_opener(_SafeRedirectHandler(allow_private=allow_private))


def safe_urlopen(
    req_or_url,
    *,
    timeout: float = 8.0,
    allow_private: bool = False,
):
    """Validates target URL and executes urlopen with SSRF-safe redirect checks."""
    target_url = req_or_url.full_url if isinstance(req_or_url, urllib.request.Request) else str(req_or_url)
    validate_public_url(target_url, allow_private=allow_private)
    opener = build_safe_opener(allow_private=allow_private)
    return opener.open(req_or_url, timeout=timeout)
