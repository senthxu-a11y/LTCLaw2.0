# PowerShell script to update LTClaw icon across all required locations
# Usage: .\update-icons.ps1

$ErrorActionPreference = "Stop"
$RepoRoot = (Get-Item $PSScriptRoot).Parent.FullName
Write-Host "LTClaw Icon Update Script"
Write-Host "========================="
Write-Host "Repo Root: $RepoRoot"

# Check Python availability
$PythonExe = if (Get-Command python -ErrorAction SilentlyContinue) { "python" } else { "python3" }
Write-Host "Using Python: $PythonExe"

# Ensure Pillow is installed
Write-Host "`n[1/5] Ensuring Pillow is installed..."
& $PythonExe -m pip install -q Pillow

# Locate the new icon image (user must provide this)
$IconDir = Join-Path $RepoRoot "scripts\pack\assets"
$SourceImage = Join-Path $RepoRoot "console\public\ltclaw-logo.png"

if (-not (Test-Path $SourceImage)) {
    Write-Host "[ERROR] Source image not found: $SourceImage" -ForegroundColor Red
    Write-Host "Please save your icon as PNG to console/public/ltclaw-logo.png first"
    exit 1
}

Write-Host "`n[2/5] Converting PNG to ICO and other formats..."
$ConvertScript = @"
import sys
from pathlib import Path
from PIL import Image

source = Path(r'$SourceImage')
icon_dir = Path(r'$IconDir')

img = Image.open(source).convert("RGBA")

# ICO for Windows (256x256)
ico_256 = img.resize((256, 256), Image.Resampling.LANCZOS)
ico_256.save(icon_dir / "icon.ico", format="ICO", sizes=[(256, 256)])
print(f"✓ Created: icon.ico (256x256)")

# PNG versions
png_512 = img.resize((512, 512), Image.Resampling.LANCZOS)
png_512.save(icon_dir / "icon.png")
print(f"✓ Created: icon.png (512x512)")

# Favicon sizes
favicon_32 = img.resize((32, 32), Image.Resampling.LANCZOS)
favicon_32.save(icon_dir / "favicon.png")
print(f"✓ Created: favicon.png (32x32)")

# Additional favicon.ico
favicon_ico = img.resize((64, 64), Image.Resampling.LANCZOS)
favicon_ico.save(icon_dir / "favicon.ico", format="ICO")
print(f"✓ Created: favicon.ico (64x64)")
"@

$ConvertScript = $ConvertScript.Replace("✓ Created:", "Created:")

$ConvertScript | & $PythonExe

# Copy favicon to console/public
Write-Host "`n[3/5] Updating console favicon files..."
$ConsolePubDir = Join-Path $RepoRoot "console\public"
Copy-Item (Join-Path $IconDir "favicon.png") -Destination (Join-Path $ConsolePubDir "favicon.png") -Force
Write-Host "Updated: console/public/favicon.png"

# Update HTML favicon link
Write-Host "`n[4/5] Updating console/index.html favicon link..."
$HtmlFile = Join-Path $RepoRoot "console\index.html"
$HtmlContent = Get-Content $HtmlFile -Raw

# Update favicon link
$OldLink = '<link rel="icon"[^>]*href="/[^"]*"[^>]*>'
$NewLink = '<link rel="icon" type="image/png" href="/favicon.png" />'

$HtmlContent = $HtmlContent -replace $OldLink, $NewLink
Set-Content $HtmlFile -Value $HtmlContent -NoNewline

Write-Host "Updated: console/index.html favicon link to /favicon.png"

# Create SVG version for backward compatibility
Write-Host "`n[5/5] Creating SVG version..."
$SvgContent = @"
<!-- LTClaw Logo - Generated from PNG -->
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1024 1024" width="1024" height="1024">
  <style>
    image { image-rendering: crisp-edges; }
  </style>
  <defs>
    <filter id="shadow" x="-50%" y="-50%" width="200%" height="200%">
      <feGaussianBlur in="SourceAlpha" stdDeviation="3"/>
      <feOffset dx="0" dy="1" result="offsetblur"/>
      <feComponentTransfer>
        <feFuncA type="linear" slope="0.3"/>
      </feComponentTransfer>
      <feMerge>
        <feMergeNode/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>
  </defs>
  <!-- Background -->
  <rect width="1024" height="1024" rx="190" fill="#5865F2"/>
  <!-- Placeholder for updated icon -->
  <text x="512" y="512" text-anchor="middle" dominant-baseline="middle" 
        font-size="280" font-weight="bold" fill="#FFFFFF" opacity="0.8">LT</text>
</svg>
"@

$SvgFile = Join-Path $ConsolePubDir "favicon.svg"
Set-Content $SvgFile -Value $SvgContent -Encoding UTF8
Write-Host "Created: console/public/favicon.svg"

Write-Host "`n======================================"
Write-Host "Icon Update Complete!" -ForegroundColor Green
Write-Host "======================================"
Write-Host ""
Write-Host "Summary of changes:"
Write-Host "  1. Windows desktop shortcut icon: scripts/pack/assets/icon.ico"
Write-Host "  2. Installer package icon: scripts/pack/assets/icon.ico"
Write-Host "  3. Desktop packing resources: scripts/pack/assets/ (all formats)"
Write-Host "  4. Console favicon: console/public/favicon.png & favicon.svg"
Write-Host "     - Updated: console/index.html favicon link"
Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. Run 'npm.cmd run build' in console/ to rebuild frontend"
Write-Host "  2. Run '.\scripts\pack\build_win.ps1' to rebuild installer with new icon"
Write-Host ""
