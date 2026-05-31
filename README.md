# ip-info

Console tool to look up public information about an IP address or hostname.

It accepts clean IPs, hostnames, URLs, proxy-style strings, and pasted bot output.

## Usage

```bat
python ip_info.py 8.8.8.8
python ip_info.py yandex.ru
python ip_info.py "connect http://170.168.20.81"
python ip_info.py "IP: 65.109.79.155 BGP (https://bgp.tools/prefix/65.109.0.0/16)"
```

Or double-click `ip_info.bat` for an interactive prompt. If the clipboard contains
an IP/host or text with an IP inside it, pressing Enter uses that value.

## Shows

- Country, region, city, coordinates, timezone
- ISP, org, AS number/name, reverse hostname
- Mobile/proxy/hosting flags from ip-api
- Quick links: BGP, Censys, IPinfo, IPQS, More

## Requirements

```bat
pip install requests
```

Data provided by [ip-api.com](http://ip-api.com) - free, no API key needed.
