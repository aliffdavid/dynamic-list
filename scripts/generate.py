#!/usr/bin/env python3

import json
import sys
import urllib.request
import ipaddress
from pathlib import Path

SOURCE_URL = "https://s3.amazonaws.com/okta-ip-ranges/ip_ranges.json"
OUTPUT_FILE = Path("site/okta-ip-ranges/okta-ip-ranges.txt")


def download_json(url):
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "okta-csdac-github-action/1.0"
        }
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def extract_networks(data):
    networks = set()

    def walk(value):
        if isinstance(value, dict):
            for child in value.values():
                if isinstance(child, str):
                    try:
                        network = ipaddress.ip_network(
                            child.strip(),
                            strict=False
                        )
                        networks.add(str(network))
                    except ValueError:
                        pass

                walk(child)

        elif isinstance(value, list):
            for child in value:
                walk(child)

        elif isinstance(value, str):
            try:
                network = ipaddress.ip_network(
                    value.strip(),
                    strict=False
                )
                networks.add(str(network))
            except ValueError:
                pass

    walk(data)

    return networks


def sort_networks(networks):
    return sorted(
        networks,
        key=lambda x: (
            ipaddress.ip_network(x).version,
            int(ipaddress.ip_network(x).network_address),
            ipaddress.ip_network(x).prefixlen,
        ),
    )


def main():
    print(f"Downloading: {SOURCE_URL}")

    data = download_json(SOURCE_URL)

    networks = extract_networks(data)

    if not networks:
        print("ERROR: No IP networks were found in the Okta JSON.")
        sys.exit(1)

    networks = sort_networks(networks)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_FILE.open("w", encoding="utf-8", newline="\n") as f:
        for network in networks:
            f.write(network + "\n")

    print(f"Wrote {len(networks)} networks to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
