#!/usr/bin/env pwsh
$ErrorActionPreference = "Stop"

$PROJECT_ROOT = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $PROJECT_ROOT

$command = if ($args.Count -gt 0) { $args[0] } else { "help" }
$rest = if ($args.Count -gt 1) { $args[1..($args.Count - 1)] } else { @() }

switch ($command) {
    "test" {
        uv run pytest $rest
    }
    "sync" {
        uv sync
    }
    "publish" {
        Write-Host "Building package..."
        uv build
        Write-Host "Publishing to PyPI..."
        uv publish $rest
    }
    "copy-libs" {
        rclone sync "$SRCDIR/odttpl/src/odttpl" "$PROJECT_ROOT/src/laudo/odttpl"
    }
    "help" {
        Write-Host "Usage: $($MyInvocation.MyCommand.Name) <command> [args...]"
        Write-Host ""
        Write-Host "Commands:"
        Write-Host "  test         Run tests (passes extra args to pytest)"
        Write-Host "  sync         Sync dependencies"
        Write-Host "  publish      Upload to PyPI"
        Write-Host "  run [args]   Run laudo CLI"
        exit 1
    }
    default {
        uv run laudo $args
    }
}
