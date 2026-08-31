#!/usr/bin/env python3

import json
import sys
import urllib.request
import ipaddress
from pathlib import Path

SOURCE_URL = "https://s3.amazonaws.com/okta-ip-ranges/ip_ranges.json"

# Existing full list
OUTPUT_FILE = Path("site/okta-ip-ranges/okta-ip-ranges.txt")

# New US Cell 10 list
US_CELL10_OUTPUT_FILE = Path("site/okta-ip-ranges/okta-us-cell10.txt")


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
    """
    Extract every valid IP network from the entire Okta JSON.
    This preserves the existing behavior of the original script.
    """
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


def extract_cell_networks(data, cell_name):
    """
    Extract IP networks from a specific Okta cell,
    such as us_cell_10.
    """
    networks = set()

    cell = data.get(cell_name, {})

    if not isinstance(cell, dict):
        return networks

    ip_ranges = cell.get("ip_ranges", [])

    if not isinstance(ip_ranges, list):
        return networks

    for value in ip_ranges:
        if not isinstance(value, str):
            continue

        try:
            network = ipaddress.ip_network(
                value.strip(),
                strict=False
            )
            networks.add(str(network))
        except ValueError:
            pass

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


def write_networks(output_file, networks):
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with output_file.open(
        "w",
        encoding="utf-8",
        newline="\n"
    ) as f:
        for network in networks:
            f.write(network + "\n")


def main():
    print(f"Downloading: {SOURCE_URL}")

    data = download_json(SOURCE_URL)

    # --------------------------------------------------
    # Full Okta list
    # --------------------------------------------------

    networks = extract_networks(data)

    if not networks:
        print("ERROR: No IP networks were found in the Okta JSON.")
        sys.exit(1)

    networks = sort_networks(networks)

    write_networks(OUTPUT_FILE, networks)

    print(
        f"Wrote {len(networks)} networks to {OUTPUT_FILE}"
    )

    # --------------------------------------------------
    # US Cell 10
    # --------------------------------------------------

    us_cell10_networks = extract_cell_networks(
        data,
        "us_cell_10"
    )

    if not us_cell10_networks:
        print(
            "ERROR: No IP networks were found for us_cell_10."
        )
        sys.exit(1)

    us_cell10_networks = sort_networks(
        us_cell10_networks
    )

    write_networks(
        US_CELL10_OUTPUT_FILE,
        us_cell10_networks
    )

    print(
        f"Wrote {len(us_cell10_networks)} networks "
        f"to {US_CELL10_OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()
