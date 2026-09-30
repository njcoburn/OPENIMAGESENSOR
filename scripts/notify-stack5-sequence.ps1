param(
    [Parameter(Mandatory=$true)][string]$StatusPath,
    [Parameter(Mandatory=$true)][string]$NotificationStatePath,
    [switch]$CheckOnly
)
$ErrorActionPreference = 'Stop'
$started = [DateTime]::UtcNow
$shell = New-Object -ComObject WScript.Shell
function Save-State($phase, $message) {
    @{pid=$PID; phase=$phase; message=$message; updated_at_utc=[DateTime]::UtcNow.ToString('o'); status_path=$StatusPath} |
        ConvertTo-Json | Set-Content -LiteralPath $NotificationStatePath -Encoding UTF8
}
while ($true) {
    $message = $null
    $outcome = 'waiting'
    try {
        $file = Get-Item -LiteralPath $StatusPath
        $status = Get-Content -LiteralPath $StatusPath -Raw | ConvertFrom-Json
        if ($status.finished) {
            $outcome = 'complete'
            if ($status.completed -and $status.all_selected_screens_pass) {
                $message = 'The queued 64-column candidate tests and independent audits finished and passed their selected checks.'
            } else {
                $outcome = 'attention'
                $message = 'The 64-column candidate sequence stopped for review. Results are saved; later stages have not been started.'
            }
        } elseif (([DateTime]::UtcNow - $file.LastWriteTimeUtc).TotalMinutes -gt 75) {
            $outcome = 'attention'
            $message = 'The candidate status has not updated for over 75 minutes. Completion is unconfirmed; check the controller and simulations.'
        }
    } catch {
        Save-State 'watching' ('Waiting for status: ' + $_.Exception.Message)
    }
    if (!$message -and ([DateTime]::UtcNow - $started).TotalHours -ge 62) {
        $outcome = 'attention'
        $message = 'The notification monitor reached its deadline. Check current simulation status; completion is unconfirmed.'
    }
    if ($CheckOnly) { Save-State $outcome $message; @{outcome=$outcome; message=$message} | ConvertTo-Json; exit 0 }
    if ($message) {
        $message += "`r`n`r`nSee docs/overview.html, the verification journal and PICK_UP_HERE.md in OPENIMAGESENSOR."
        Save-State 'alert_open' $message
        [void]$shell.Popup($message, 0, 'OPENIMAGESENSOR - candidate sequence', 64)
        Save-State 'dismissed' $message
        exit 0
    }
    Save-State 'watching' 'Waiting for the candidate sequence; successful stages advance automatically.'
    Start-Sleep -Seconds 30
}
