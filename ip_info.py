#!/usr/bin/env python3
"""IP address information lookup tool using ip-api.com (free, no key required)."""

from __future__ import annotations

import io
import ipaddress
import re
import socket
import sys
from urllib.parse import urlparse

import requests

# Force UTF-8 output on Windows.
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

API_URL = (
    "http://ip-api.com/json/{ip}"
    "?fields=status,message,country,countryCode,regionName,city,zip,lat,lon,"
    "timezone,isp,org,as,asname,reverse,mobile,proxy,hosting,query"
)

IPV4_RE = re.compile(r"(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}(?![\d.])")
TOKEN_SPLIT_RE = re.compile(r"[\s|<>\[\]{}()]+")
EXIT_WORDS = {"q", "quit", "exit", "й", "выйти"}


class IpInfoError(RuntimeError):
    """User-facing lookup error."""


def bool_mark(value: object) -> str:
    if value is True:
        return "YES"
    if value is False:
        return "NO"
    return "-"


def valid_ip(value: str) -> str | None:
    try:
        return str(ipaddress.ip_address(value.strip("[]")))
    except ValueError:
        return None


def normalize_clip_text(text: str) -> str:
    return (
        text.replace("\u200b", "")
        .replace("\u200c", "")
        .replace("\u200d", "")
        .replace("\ufeff", "")
        .strip()
    )


def first_ipv4(text: str) -> str | None:
    for match in IPV4_RE.finditer(text):
        ip = valid_ip(match.group(0))
        if ip:
            return ip
    return None


def host_from_url_or_token(token: str) -> str | None:
    token = token.strip().strip("'\"`.,;")
    if not token:
        return None

    lowered = token.lower()
    if lowered in {"connect", "http", "https", "socks", "socks4", "socks5"}:
        return None

    if "://" in token:
        parsed = urlparse(token)
    elif "/" in token or ":" in token:
        parsed = urlparse("//" + token)
    else:
        parsed = None

    if parsed and parsed.hostname:
        return parsed.hostname.strip("[]")

    return token.strip("[]")


def looks_like_hostname(value: str) -> bool:
    value = value.strip(".")
    if len(value) > 253 or "." not in value:
        return False
    labels = value.split(".")
    return all(
        0 < len(label) <= 63
        and not label.startswith("-")
        and not label.endswith("-")
        and re.fullmatch(r"[A-Za-z0-9-]+", label)
        for label in labels
    )


def extract_target(raw: str) -> str | None:
    """Extract an IP/host from raw text, URLs, proxy commands, or bot output."""
    text = normalize_clip_text(raw)
    if not text:
        return None

    ip = first_ipv4(text)
    if ip:
        return ip

    # IPv6 is easier to identify after tokenization because it uses ":" heavily.
    for token in TOKEN_SPLIT_RE.split(text):
        host = host_from_url_or_token(token)
        if not host:
            continue
        ip = valid_ip(host)
        if ip:
            return ip

    for token in TOKEN_SPLIT_RE.split(text):
        host = host_from_url_or_token(token)
        if host and looks_like_hostname(host):
            return host.strip(".")

    return None


def get_clipboard_text() -> str | None:
    try:
        import tkinter as tk

        root = tk.Tk()
        root.withdraw()
        try:
            return root.clipboard_get()
        finally:
            root.destroy()
    except Exception:
        return None


def clipboard_target() -> str | None:
    text = get_clipboard_text()
    if not text:
        return None
    return extract_target(text)


def get_ip_info(ip: str) -> dict:
    try:
        resp = requests.get(API_URL.format(ip=ip), timeout=8)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError as exc:
        raise IpInfoError("No internet connection or API is unreachable.") from exc
    except requests.exceptions.Timeout as exc:
        raise IpInfoError("Request timed out.") from exc
    except requests.exceptions.HTTPError as exc:
        raise IpInfoError(f"HTTP error: {exc}") from exc
    except ValueError as exc:
        raise IpInfoError("API returned invalid JSON.") from exc


def resolve_hostname(target: str) -> str | None:
    ip = valid_ip(target)
    if ip:
        return ip

    try:
        infos = socket.getaddrinfo(target, None, proto=socket.IPPROTO_TCP)
    except socket.gaierror:
        return None

    for family, _, _, _, sockaddr in infos:
        if family in (socket.AF_INET, socket.AF_INET6):
            return sockaddr[0]
    return None


def print_links(ip: str) -> None:
    links = [
        ("BGP", f"https://bgp.tools/ip/{ip}"),
        ("Censys", f"https://platform.censys.io/hosts/{ip}"),
        ("IPinfo", f"https://ipinfo.io/{ip}"),
        ("IPQS", f"https://www.ipqualityscore.com/free-ip-lookup-proxy-vpn-test/lookup/{ip}"),
        ("More", f"https://ipregion.xyz/{ip}"),
    ]
    print("  Links")
    for label, url in links:
        print(f"    {label:<7} {url}")


def print_info(data: dict) -> None:
    if data.get("status") != "success":
        msg = data.get("message", "Unknown error")
        raise IpInfoError(f"API returned failure: {msg}")

    rows = [
        ("IP", data.get("query", "-")),
        ("Country", f"{data.get('country', '-')} ({data.get('countryCode', '-')})"),
        ("Region", data.get("regionName", "-")),
        ("City", data.get("city", "-")),
        ("ZIP", data.get("zip", "-")),
        ("Coordinates", f"{data.get('lat', '-')}, {data.get('lon', '-')}"),
        ("Timezone", data.get("timezone", "-")),
        ("ISP", data.get("isp", "-")),
        ("Org", data.get("org", "-")),
        ("AS", data.get("as", "-")),
        ("AS Name", data.get("asname", "-")),
        ("Hostname", data.get("reverse", "-") or "-"),
        ("Mobile", bool_mark(data.get("mobile"))),
        ("Proxy", bool_mark(data.get("proxy"))),
        ("Hosting", bool_mark(data.get("hosting"))),
    ]

    width = max(len(label) for label, _ in rows) + 2
    sep = "-" * 72

    print()
    print(f"  IP Info: {data.get('query', '')}")
    print(f"  {sep}")
    for label, value in rows:
        if value and value != "-":
            print(f"  {label:<{width}} {value}")
    print(f"  {sep}")
    print_links(str(data.get("query", "")))
    print()


def lookup(raw: str) -> None:
    target = extract_target(raw)
    if not target:
        raise IpInfoError("No IP address or hostname found in the input.")

    ip = resolve_hostname(target)
    if ip is None:
        raise IpInfoError(f"Could not resolve '{target}'.")

    if ip != target:
        print(f"Resolved {target} -> {ip}")

    data = get_ip_info(ip)
    print_info(data)


def prompt(default: str | None) -> str:
    if default:
        return input(f"Enter IP, URL, host, or pasted text [{default}] (q to exit): ").strip()
    return input("Enter IP, URL, host, or pasted text (q to exit): ").strip()


def interactive_loop() -> None:
    print()
    print("  IP / Hostname Lookup")
    print("  Paste text like: connect http://170.168.20.81")
    print("  Press Enter to use the IP/host found in the clipboard.")
    print()

    while True:
        default = clipboard_target()
        raw = prompt(default)
        if raw.lower() in EXIT_WORDS:
            return
        if not raw and default:
            raw = default
        if not raw:
            continue

        try:
            lookup(raw)
        except IpInfoError as exc:
            print(f"[ERROR] {exc}")


def main() -> None:
    raw = " ".join(sys.argv[1:]).strip()
    if raw:
        try:
            lookup(raw)
        except IpInfoError as exc:
            print(f"[ERROR] {exc}")
            sys.exit(1)
        return

    interactive_loop()


if __name__ == "__main__":
    main()
