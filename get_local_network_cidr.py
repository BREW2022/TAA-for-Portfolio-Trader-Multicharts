#!/usr/bin/env python3
"""
Detect local network segment in CIDR notation for VPN exclusion.
Works cross-platform on Windows, Linux, and macOS.
"""
import socket
import ipaddress
import subprocess
import sys
from pathlib import Path


def get_local_ip_and_subnet():
    """Get local IP and calculate CIDR notation."""
    try:
        # Connect to a public IP to determine local IP without sending data
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()

        # Get subnet mask based on platform
        if sys.platform == "win32":
            return get_local_cidr_windows(local_ip)
        else:
            return get_local_cidr_unix(local_ip)
    except Exception as e:
        print(f"Error getting local IP: {e}", file=sys.stderr)
        return None


def get_local_cidr_windows(local_ip):
    """Get CIDR for Windows."""
    try:
        result = subprocess.run(
            ["ipconfig"],
            capture_output=True,
            text=True,
            check=True
        )
        lines = result.stdout.split('\n')

        for i, line in enumerate(lines):
            if local_ip in line:
                # Find subnet mask in nearby lines
                for j in range(max(0, i-2), min(len(lines), i+3)):
                    if "Subnet Mask" in lines[j]:
                        subnet = lines[j].split(":")[-1].strip()
                        return format_cidr(local_ip, subnet)

        # Fallback to /24
        return f"{'.'.join(local_ip.split('.')[:3])}.0/24"
    except Exception as e:
        print(f"Error getting Windows network info: {e}", file=sys.stderr)
        return f"{'.'.join(local_ip.split('.')[:3])}.0/24"


def get_local_cidr_unix(local_ip):
    """Get CIDR for Unix-like systems (Linux/macOS)."""
    try:
        if sys.platform == "darwin":
            result = subprocess.run(
                ["ifconfig"],
                capture_output=True,
                text=True,
                check=True
            )
            return parse_ifconfig(result.stdout, local_ip)
        else:  # Linux
            result = subprocess.run(
                ["ip", "addr"],
                capture_output=True,
                text=True,
                check=True
            )
            return parse_ip_addr(result.stdout, local_ip)
    except Exception as e:
        print(f"Error getting Unix network info: {e}", file=sys.stderr)
        return f"{'.'.join(local_ip.split('.')[:3])}.0/24"


def parse_ip_addr(output, local_ip):
    """Parse 'ip addr' output (Linux)."""
    for line in output.split('\n'):
        if local_ip in line and "/" in line:
            # Line format: "inet 192.168.1.100/24 brd..."
            cidr = line.strip().split()[1]
            return cidr
    return f"{'.'.join(local_ip.split('.')[:3])}.0/24"


def parse_ifconfig(output, local_ip):
    """Parse 'ifconfig' output (macOS)."""
    lines = output.split('\n')
    for i, line in enumerate(lines):
        if local_ip in line:
            # Look for netmask in nearby lines
            for j in range(max(0, i-1), min(len(lines), i+3)):
                if "netmask" in lines[j]:
                    parts = lines[j].split()
                    for k, part in enumerate(parts):
                        if part == "netmask":
                            mask = parts[k+1]
                            return format_cidr(local_ip, mask)
    return f"{'.'.join(local_ip.split('.')[:3])}.0/24"


def format_cidr(ip, netmask):
    """Convert IP and netmask to CIDR notation."""
    try:
        # Handle hex netmask (macOS)
        if netmask.startswith("0x"):
            netmask = ipaddress.IPv4Address(int(netmask, 16))
        else:
            netmask = ipaddress.IPv4Address(netmask)

        ip_obj = ipaddress.IPv4Address(ip)
        network = ipaddress.IPv4Network(
            (ip_obj, netmask),
            strict=False
        )
        return str(network)
    except Exception as e:
        print(f"Error formatting CIDR: {e}", file=sys.stderr)
        return f"{'.'.join(ip.split('.')[:3])}.0/24"


if __name__ == "__main__":
    cidr = get_local_ip_and_subnet()
    if cidr:
        print(cidr)
    else:
        print("127.0.0.1/24", file=sys.stderr)
        sys.exit(1)
