#!/usr/bin/env python3
"""IP address information lookup tool using ip-api.com (free, no key required)."""

import sys
import io
import socket
import requests

# Force UTF-8 output on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

API_URL = "http://ip-api.com/json/{ip}?fields=status,message,country,countryCode,regionName,city,zip,lat,lon,timezone,isp,org,as,asname,reverse,query"


def get_ip_info(ip: str) -> dict:
    try:
        resp = requests.get(API_URL.format(ip=ip), timeout=8)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError:
        print("[ERROR] No internet connection or API is unreachable.")
        sys.exit(1)
    except requests.exceptions.Timeout:
        print("[ERROR] Request timed out.")
        sys.exit(1)
    except requests.exceptions.HTTPError as e:
        print(f"[ERROR] HTTP error: {e}")
        sys.exit(1)


def resolve_hostname(target: str) -> str | None:
    """Try to resolve domain to IP if not already an IP."""
    try:
        socket.inet_aton(target)
        return target  # already an IPv4
    except OSError:
        pass
    try:
        socket.inet_pton(socket.AF_INET6, target)
        return target  # already an IPv6
    except OSError:
        pass
    try:
        return socket.gethostbyname(target)
    except socket.gaierror:
        return None


def print_info(data: dict) -> None:
    if data.get("status") != "success":
        msg = data.get("message", "Unknown error")
        print(f"[ERROR] API returned failure: {msg}")
        sys.exit(1)

    # Build display lines
    rows = [
        ("IP",          data.get("query", "—")),
        ("Country",     f"{data.get('country', '-')} ({data.get('countryCode', '-')})"),
        ("Region",      data.get("regionName", "-")),
        ("City",        data.get("city", "-")),
        ("ZIP",         data.get("zip", "-")),
        ("Coordinates", f"{data.get('lat', '-')}, {data.get('lon', '-')}"),
        ("Timezone",    data.get("timezone", "-")),
        ("ISP",         data.get("isp", "-")),
        ("Org",         data.get("org", "-")),
        ("AS",          data.get("as", "-")),
        ("AS Name",     data.get("asname", "-")),
        ("Hostname",    data.get("reverse", "-") or "-"),
    ]

    width = max(len(label) for label, _ in rows) + 2
    sep = "-" * (width + 42)

    print()
    print(f"  IP Info: {data.get('query', '')}")
    print(f"  {sep}")
    for label, value in rows:
        if value and value != "-":
            print(f"  {label:<{width}} {value}")
    print(f"  {sep}")
    print()


def main() -> None:
    if len(sys.argv) < 2:
        target = input("Enter IP or hostname: ").strip()
    else:
        target = sys.argv[1].strip()

    if not target:
        print("[ERROR] No address provided.")
        sys.exit(1)

    ip = resolve_hostname(target)
    if ip is None:
        print(f"[ERROR] Could not resolve '{target}'.")
        sys.exit(1)

    if ip != target:
        print(f"Resolved {target} -> {ip}")

    data = get_ip_info(ip)
    print_info(data)


if __name__ == "__main__":
    main()
