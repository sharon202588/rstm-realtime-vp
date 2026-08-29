function Get-NextReleaseVersion {
    param(
        [Parameter(Mandatory = $true)]
        [string]$ReleaseRoot
    )

    $latest = $null
    if (Test-Path -LiteralPath $ReleaseRoot) {
        foreach ($directory in Get-ChildItem -LiteralPath $ReleaseRoot -Directory) {
            if ($directory.Name -notmatch '^RealtimeVoiceVP V(?<version>\d+\.\d+\.\d+)$') {
                continue
            }
            try {
                $candidate = [Version]$Matches.version
            } catch {
                continue
            }
            if ($null -eq $latest -or $candidate -gt $latest) {
                $latest = $candidate
            }
        }
    }

    if ($null -eq $latest) {
        return '1.0.0'
    }
    return '{0}.{1}.{2}' -f $latest.Major, $latest.Minor, ($latest.Build + 1)
}