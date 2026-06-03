# Get local network segment in CIDR notation for VPN exclusion
# Usage: .\Get-LocalNetworkCIDR.ps1

function Get-LocalNetworkCIDR {
    <#
    .SYNOPSIS
    Returns the local network segment in CIDR notation

    .DESCRIPTION
    Detects the system's local IP address and subnet mask,
    then returns the network in CIDR notation suitable for VPN exclusion.

    .EXAMPLE
    Get-LocalNetworkCIDR
    192.168.1.0/24
    #>

    try {
        # Get active network adapters
        $adapters = Get-NetIPAddress -AddressFamily IPv4 -ErrorAction Stop |
                    Where-Object { $_.IPAddress -notmatch "^127\." }

        if (-not $adapters) {
            Write-Error "No active network adapters found"
            return $null
        }

        # Take the first active adapter
        $ip = $adapters[0].IPAddress
        $prefixLength = $adapters[0].PrefixLength

        # Convert prefix length to CIDR
        $networkAddress = Get-NetworkAddress $ip $prefixLength
        $cidr = "$networkAddress/$prefixLength"

        return $cidr
    }
    catch {
        Write-Error "Error getting network info: $_"
        return $null
    }
}

function Get-NetworkAddress {
    param(
        [string]$IPAddress,
        [int]$PrefixLength
    )

    $ipObj = [System.Net.IPAddress]::Parse($IPAddress)
    $ipBytes = $ipObj.GetAddressBytes()

    # Calculate host bits to mask
    $hostBits = 32 - $PrefixLength
    $maskValue = 0xFFFFFFFF -shl $hostBits

    # Convert to bytes and apply mask
    [byte[]]$maskBytes = @(
        [byte](($maskValue -shr 24) -band 0xFF),
        [byte](($maskValue -shr 16) -band 0xFF),
        [byte](($maskValue -shr 8) -band 0xFF),
        [byte]($maskValue -band 0xFF)
    )

    # Apply mask to IP
    for ($i = 0; $i -lt 4; $i++) {
        $ipBytes[$i] = $ipBytes[$i] -band $maskBytes[$i]
    }

    return [System.Net.IPAddress]::new($ipBytes).ToString()
}

# Main execution
$result = Get-LocalNetworkCIDR
if ($result) {
    Write-Output $result
}
else {
    Write-Error "Failed to determine local network CIDR"
    exit 1
}
