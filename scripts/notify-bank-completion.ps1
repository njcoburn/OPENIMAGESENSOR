# Local, one-shot notification for the configured bank audit. No external messages.
param(
    [Parameter(Mandatory=$true)][string]$StatusPath,
    [Parameter(Mandatory=$true)][string]$NotificationStatePath,
    [int]$ExpectedCases = 2,
    [switch]$CheckOnly
)
$ErrorActionPreference = 'Stop'
$started = [DateTime]::UtcNow
$shell = New-Object -ComObject WScript.Shell
function Save-State($phase, $message) {
    @{pid=$PID; phase=$phase; message=$message; updated_at_utc=[DateTime]::UtcNow.ToString('o'); status_path=$StatusPath} |
        ConvertTo-Json | Set-Content -LiteralPath $NotificationStatePath -Encoding UTF8
}
Save-State 'watching' 'Waiting for the full-bank audit results.'
while ($true) {
    $message = $null
    $outcome = 'waiting'
    try {
        $file = Get-Item -LiteralPath $StatusPath
        $status = Get-Content -LiteralPath $StatusPath -Raw | ConvertFrom-Json
        $failures = @($status.failures.PSObject.Properties).Count
        $audited = @($status.audited.PSObject.Properties).Count
        if ($status.all_pairs_audited) {
            $outcome = 'complete'
            if ($status.all_selected_screens_pass) {
                $message = 'Both full-bank audits have finished and passed their selected checks.'
            } else {
                $message = 'Both full-bank audits have finished. At least one accuracy or refinement check failed; review the results before moving on.'
            }
            if (@($status.render_failures.PSObject.Properties).Count -gt 0) {
                $message += ' Plot generation also needs attention.'
            }
        } elseif ($status.watcher_expired -or ($failures -gt 0 -and ($audited + $failures) -ge $ExpectedCases)) {
            $outcome = 'attention'
            $message = 'The bank audit watcher stopped with failures or reached its deadline. Qualification is incomplete; some simulations may still be running.'
        } elseif (([DateTime]::UtcNow - $file.LastWriteTimeUtc).TotalMinutes -gt 75) {
            $outcome = 'attention'
            $message = 'The bank audit status has not updated for over 75 minutes. Check the simulation and watcher processes; completion is unconfirmed.'
        }
    } catch {
        Save-State 'watching' ('Waiting for a readable status file: ' + $_.Exception.Message)
    }
    if (!$message -and ([DateTime]::UtcNow - $started).TotalHours -ge 8) {
        $outcome = 'attention'
        $message = 'The notification monitor reached eight hours without a final audit result. Check the running simulations; completion is unconfirmed.'
    }
    if ($CheckOnly) {
        Save-State $outcome $message
        @{outcome=$outcome; message=$message} | ConvertTo-Json
        exit 0
    }
    if ($message) {
        $message += "`r`n`r`nReturn to Codex to review the results and next steps. See docs/overview.html and PICK_UP_HERE.md in OPENIMAGESENSOR."
        Save-State 'alert_open' $message
        # Zero timeout keeps the local alert visible until the user dismisses it.
        [void]$shell.Popup($message, 0, 'OPENIMAGESENSOR - bank audit', 64)
        Save-State 'dismissed' $message
        exit 0
    }
    Save-State 'watching' 'Waiting for the full-bank audit results.'
    Start-Sleep -Seconds 30
}
