# Papito Mamito AI - Autonomous 1000 Followers Campaign Launcher
# Run this to activate the autonomous engagement system

Write-Host ""
Write-Host "[MUSIC] Papito Mamito AI - 1000 Followers Campaign" -ForegroundColor Magenta
Write-Host "===============================================" -ForegroundColor Magenta
Write-Host ""

$API_BASE = "https://web-production-14aea.up.railway.app"

# Health Check
Write-Host "[CHECK] Checking API health..." -ForegroundColor Cyan
try {
    $health = Invoke-RestMethod -Uri "$API_BASE/health" -Method Get
    Write-Host "[OK] API Status: $($health.status)" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] API unreachable. Check Railway deployment." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "[LIST] 1000 Followers Campaign Checklist" -ForegroundColor Yellow
Write-Host "=====================================" -ForegroundColor Yellow
Write-Host ""
Write-Host "[KEY] API Credentials Required:" -ForegroundColor White
Write-Host "  [ ] Twitter/X API keys configured in .env"
Write-Host "  [ ] OpenAI API key configured"
Write-Host "  [ ] Buffer access token (for Zapier)"
Write-Host "  [ ] Telegram bot token (for notifications)"
Write-Host ""
Write-Host "[TARGET] First 1000 Followers Strategy:" -ForegroundColor White
Write-Host ""
Write-Host "  PHASE 1: Foundation (Week 1-2) -> 0 to 100 followers"
Write-Host "    * 3x daily posts (8am / 2pm / 8pm WAT)"
Write-Host "    * 15+ daily replies to Afrobeat content"
Write-Host "    * Welcome all new followers"
Write-Host ""
Write-Host "  PHASE 2: Momentum (Week 3-4) -> 100 to 300 followers"
Write-Host "    * Start Q&A sessions"
Write-Host "    * Fan recognition posts"
Write-Host "    * Cross-promotion with creators"
Write-Host ""
Write-Host "  PHASE 3: Growth (Week 5-8) -> 300 to 700 followers"
Write-Host "    * Viral content attempts"
Write-Host "    * #FlightMode6000 challenge"
Write-Host "    * Weekly Fan of the Week"
Write-Host ""
Write-Host "  PHASE 4: Consolidation (Week 9-12) -> 700 to 1000 followers"
Write-Host "    * Twitter Spaces hosting"
Write-Host "    * Digital listening parties"
Write-Host "    * VIP fan program"
Write-Host ""

# Check available endpoints
Write-Host "[ENDPOINTS] Available Engagement Endpoints:" -ForegroundColor Cyan
Write-Host "-------------------------------------------" -ForegroundColor DarkGray

$endpoints = @(
    @{Method="POST"; Path="/engagement/process-mentions"; Desc="Reply to mentions"},
    @{Method="POST"; Path="/engagement/discover-afrobeat"; Desc="Engage with Afrobeat content"},
    @{Method="POST"; Path="/fans/welcome-session"; Desc="Welcome new followers"},
    @{Method="POST"; Path="/fans/recognition-session"; Desc="Fan appreciation posts"},
    @{Method="GET";  Path="/fans/top-fans"; Desc="View top engaged fans"},
    @{Method="POST"; Path="/fans/announce-fotw"; Desc="Announce Fan of the Week"}
)

foreach ($ep in $endpoints) {
    Write-Host "  $($ep.Method.PadRight(6)) $($ep.Path.PadRight(35)) $($ep.Desc)" -ForegroundColor White
}

Write-Host ""
Write-Host "[ZAPIER] Zapier Automation Endpoints:" -ForegroundColor Cyan
$zapierEndpoints = @(
    @{Path="/webhooks/zapier/generate-post"; Desc="Generate content for posting"},
    @{Path="/webhooks/zapier/content-types"; Desc="List content types"},
    @{Path="/webhooks/zapier/album-status"; Desc="FLOURISH MODE countdown"}
)

foreach ($ep in $zapierEndpoints) {
    Write-Host "  POST $($ep.Path.PadRight(40)) $($ep.Desc)" -ForegroundColor White
}

Write-Host ""
Write-Host "[SCHEDULE] Recommended Posting Schedule (WAT):" -ForegroundColor Yellow
Write-Host "  07:00 AM  - Morning blessing / motivation"
Write-Host "  12:00 PM  - Music wisdom / production insight"
Write-Host "  03:00 PM  - Challenge promo / engagement post"
Write-Host "  06:00 PM  - Album promo / FLOURISH MODE update"
Write-Host "  09:00 PM  - Fan appreciation / community love"
Write-Host ""

Write-Host "[COMMANDS] Quick Start Commands:" -ForegroundColor Green
Write-Host ""
Write-Host "  # Test content generation" -ForegroundColor DarkGray
Write-Host "  `$body = @{content_type='morning_blessing'; include_album=`$true; platform='twitter'} | ConvertTo-Json" -ForegroundColor White
Write-Host "  Invoke-RestMethod -Uri 'https://web-production-14aea.up.railway.app/webhooks/zapier/generate-post' -Method Post -Body `$body -ContentType 'application/json'" -ForegroundColor White
Write-Host ""
Write-Host "  # Check album countdown" -ForegroundColor DarkGray
Write-Host "  Invoke-RestMethod -Uri 'https://web-production-14aea.up.railway.app/webhooks/zapier/album-status'" -ForegroundColor White
Write-Host ""

# Test content generation
Write-Host "[TEST] Testing content generation..." -ForegroundColor Cyan
try {
    $testBody = @{
        content_type = "morning_blessing"
        include_album = $true
        platform = "twitter"
    } | ConvertTo-Json
    
    $testContent = Invoke-RestMethod -Uri "$API_BASE/webhooks/zapier/generate-post" -Method Post -Body $testBody -ContentType "application/json"
    
    Write-Host ""
    Write-Host "[SUCCESS] Sample Generated Content:" -ForegroundColor Green
    Write-Host "-----------------------------------------------------------" -ForegroundColor DarkGray
    Write-Host $testContent.text -ForegroundColor White
    Write-Host ""
    Write-Host "$($testContent.hashtags)" -ForegroundColor Cyan
    Write-Host "-----------------------------------------------------------" -ForegroundColor DarkGray
} catch {
    Write-Host "[WARNING] Content generation test skipped" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "[NEXT] STEPS TO ACTIVATE:" -ForegroundColor Magenta
Write-Host "--------------------------" -ForegroundColor DarkGray
Write-Host ""
Write-Host "  1. Set up Zapier automation (see /zapier-buffer-setup workflow)"
Write-Host "  2. Configure 3 Zaps for daily posts (7am / 1pm / 7pm)"
Write-Host "  3. Enable Twitter API for engagement"
Write-Host "  4. Start manual engagement session daily"
Write-Host "  5. Track progress in /docs/FIRST_1000_FOLLOWERS_GOAL.md"
Write-Host ""
Write-Host "[GO] LETS GET THOSE 1000 FOLLOWERS! #FlightMode6000" -ForegroundColor Magenta
Write-Host ""
