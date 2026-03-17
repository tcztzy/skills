param(
    [ValidateSet("discover", "resolve", "exec")]
    [string]$Mode = "discover",

    [string]$Project,

    [string]$Distro,

    [string[]]$SearchRoots,

    [int]$MaxDepth = 4,

    [string]$Command,

    [switch]$Json,

    [switch]$IncludeHomeFallback,

    [switch]$IncludeNested,

    [switch]$AllMatches
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$script:HomeCache = @{}
$script:DiscoveryCache = @{}

function Invoke-ExternalCapture {
    param(
        [string]$FilePath,
        [string[]]$Arguments,
        [switch]$AllowFailure
    )

    $text = & $FilePath @Arguments 2>&1 | Out-String
    $exitCode = $LASTEXITCODE
    $clean = ($text -replace "`0", "").Trim()

    if (-not $AllowFailure -and $exitCode -ne 0) {
        throw "$FilePath exited with code $exitCode`n$clean"
    }

    [pscustomobject]@{
        ExitCode = $exitCode
        Output = $clean
    }
}

function Invoke-WslCapture {
    param(
        [string[]]$Arguments,
        [switch]$AllowFailure
    )

    Invoke-ExternalCapture -FilePath "wsl.exe" -Arguments $Arguments -AllowFailure:$AllowFailure
}

function ConvertTo-BashLiteral {
    param([string]$Text)

    $escaped = $Text.Replace("\", "\\").Replace('"', '\"').Replace('$', '\$')
    '"' + $escaped + '"'
}

function Get-LeafName {
    param([string]$Path)

    [System.IO.Path]::GetFileName($Path.TrimEnd("/", [char]92))
}

function Normalize-LinuxPath {
    param([string]$Path)

    if ([string]::IsNullOrWhiteSpace($Path)) {
        return $Path
    }

    $normalized = $Path -replace '\\', '/'
    if ($normalized.Length -gt 1) {
        $normalized = $normalized.TrimEnd('/')
    }

    $normalized
}

function Get-LinuxPathDepth {
    param([string]$Path)

    $normalized = Normalize-LinuxPath -Path $Path
    if ($normalized -eq "/") {
        return 0
    }

    @($normalized -split '/' | Where-Object { $_ }).Count
}

function Test-LinuxPathAncestor {
    param(
        [string]$ParentPath,
        [string]$ChildPath
    )

    $parent = Normalize-LinuxPath -Path $ParentPath
    $child = Normalize-LinuxPath -Path $ChildPath

    if ($parent -eq $child) {
        return $false
    }

    $child.StartsWith($parent + "/")
}

function New-ProjectRecord {
    param(
        [string]$DistroName,
        [string]$LinuxPath
    )

    [pscustomobject]@{
        Distro = $DistroName
        LinuxPath = Normalize-LinuxPath -Path $LinuxPath
        Name = Get-LeafName -Path $LinuxPath
    }
}

function Get-ValidLinuxCandidatePaths {
    param([string]$Output)

    if (-not $Output) {
        return @()
    }

    $Output -split "\r?\n" |
        ForEach-Object { $_.Trim() } |
        Where-Object { $_ -and $_.StartsWith("/") }
}

function Get-TopLevelProjects {
    param([object[]]$Projects)

    $ordered = @(
        $Projects |
            Sort-Object `
                @{ Expression = { Get-LinuxPathDepth -Path $_.LinuxPath } }, `
                @{ Expression = { $_.LinuxPath } }
    )

    $topLevel = New-Object System.Collections.Generic.List[object]
    foreach ($project in $ordered) {
        $isNested = $false
        foreach ($kept in $topLevel) {
            if ($kept.Distro -eq $project.Distro -and (Test-LinuxPathAncestor -ParentPath $kept.LinuxPath -ChildPath $project.LinuxPath)) {
                $isNested = $true
                break
            }
        }

        if (-not $isNested) {
            [void]$topLevel.Add($project)
        }
    }

    @($topLevel | Sort-Object Distro, Name, LinuxPath)
}

function Get-WslDistros {
    $result = Invoke-WslCapture -Arguments @("--list", "--verbose")
    $lines = $result.Output -split "\r?\n" |
        ForEach-Object { $_.TrimEnd() } |
        Where-Object { $_ -and $_ -notmatch '^\s*NAME\s+STATE\s+VERSION\s*$' }

    $distros = foreach ($line in $lines) {
        if ($line -match '^(?<marker>\*)?\s*(?<name>.+?)\s+(?<state>Running|Stopped|Installing|Uninstalling)\s+(?<version>\d+)\s*$') {
            $isDefault = $false
            if ($matches.ContainsKey("marker") -and $matches.marker) {
                $isDefault = $true
            }

            [pscustomobject]@{
                Name = $matches.name.Trim()
                State = $matches.state
                Version = [int]$matches.version
                IsDefault = $isDefault
            }
        }
    }

    if (-not $distros) {
        throw "Unable to parse `wsl.exe --list --verbose` output."
    }

    $distros
}

function Get-PreferredDistros {
    param([string]$RequestedDistro)

    $distros = Get-WslDistros | Where-Object { $_.Name -notlike "docker-desktop*" }

    if ($RequestedDistro) {
        $selected = $distros | Where-Object { $_.Name -eq $RequestedDistro }
        if (-not $selected) {
            throw "WSL distro not found: $RequestedDistro"
        }

        return @($selected)
    }

    $distros |
        Sort-Object `
            @{ Expression = { if ($_.State -eq "Running") { 0 } else { 1 } } }, `
            @{ Expression = { if ($_.IsDefault) { 0 } else { 1 } } }, `
            Name
}

function Test-WslPathExists {
    param(
        [string]$DistroName,
        [string]$LinuxPath
    )

    $literal = ConvertTo-BashLiteral $LinuxPath
    $result = Invoke-WslCapture -Arguments @(
        "-d", $DistroName, "--", "bash", "-lc",
        "[ -e $literal ] && printf yes || printf no"
    )

    $result.Output -eq "yes"
}

function Get-WslHome {
    param([string]$DistroName)

    if ($script:HomeCache.ContainsKey($DistroName)) {
        return $script:HomeCache[$DistroName]
    }

    $linuxHome = (Invoke-WslCapture -Arguments @(
        "-d", $DistroName, "--", "bash", "-lc", 'printf "%s" "$HOME"'
    )).Output

    if (-not $linuxHome) {
        throw "Unable to determine HOME for distro $DistroName"
    }

    $script:HomeCache[$DistroName] = $linuxHome
    $linuxHome
}

function Get-WslWindowsPath {
    param(
        [string]$DistroName,
        [string]$LinuxPath
    )

    (Invoke-WslCapture -Arguments @("-d", $DistroName, "--", "wslpath", "-w", $LinuxPath)).Output
}

function Normalize-SearchRoots {
    param(
        [string]$DistroName,
        [string[]]$RequestedRoots,
        [switch]$AllowHomeFallback
    )

    $linuxHome = Get-WslHome -DistroName $DistroName

    if ($RequestedRoots -and $RequestedRoots.Count -gt 0) {
        $roots = $RequestedRoots | ForEach-Object { $_ -replace '^\$HOME\b', $linuxHome }
        return @($roots)
    }

    $candidates = @(
        "$linuxHome/workspace",
        "$linuxHome/projects",
        "$linuxHome/src",
        "$linuxHome/dev",
        "$linuxHome/code",
        "$linuxHome/repos",
        "$linuxHome/git"
    )

    if ($AllowHomeFallback) {
        return @($candidates + $linuxHome)
    }

    @($candidates)
}

function Discover-WslProjects {
    param(
        [string]$DistroName,
        [string[]]$Roots,
        [int]$SearchDepth
    )

    $cacheKey = "{0}|{1}|{2}" -f $DistroName, $SearchDepth, (($Roots | Sort-Object) -join ";")
    if ($script:DiscoveryCache.ContainsKey($cacheKey)) {
        return $script:DiscoveryCache[$cacheKey]
    }

    $linuxHome = Get-WslHome -DistroName $DistroName
    $manifests = @(
        "package.json",
        "pyproject.toml",
        "Cargo.toml",
        "go.mod",
        "pom.xml",
        "build.gradle",
        "CMakeLists.txt",
        "mix.exs",
        "composer.json"
    )

    $candidates = New-Object System.Collections.Generic.HashSet[string]
    foreach ($root in $Roots) {
        $rootLiteral = ConvertTo-BashLiteral $root
        $homeAwarePrefix = ""
        if ($root -eq $linuxHome) {
            $homePrunePattern = ConvertTo-BashLiteral ($root + "/.*")
            $homeAwarePrefix = "-mindepth 1 -path $homePrunePattern -prune -o "
        }

        $gitCommand = "find $rootLiteral -maxdepth $SearchDepth $homeAwarePrefix -type d -name .git -printf '%h\n' 2>/dev/null"
        $gitResult = Invoke-WslCapture -Arguments @("-d", $DistroName, "--", "bash", "-lc", $gitCommand) -AllowFailure
        foreach ($path in (Get-ValidLinuxCandidatePaths -Output $gitResult.Output)) {
            [void]$candidates.Add($path)
        }

        $manifestExpr = ($manifests | ForEach-Object { "-name $_" }) -join " -o "
        $manifestCommand = "find $rootLiteral -maxdepth $SearchDepth $homeAwarePrefix -type f \( $manifestExpr \) -printf '%h\n' 2>/dev/null"
        $manifestResult = Invoke-WslCapture -Arguments @("-d", $DistroName, "--", "bash", "-lc", $manifestCommand) -AllowFailure
        foreach ($path in (Get-ValidLinuxCandidatePaths -Output $manifestResult.Output)) {
            [void]$candidates.Add($path)
        }
    }

    $allProjects = @($candidates | Sort-Object | ForEach-Object {
        New-ProjectRecord -DistroName $DistroName -LinuxPath $_
    })

    $discovery = [pscustomobject]@{
        AllCandidates = $allProjects
        TopLevelCandidates = @(Get-TopLevelProjects -Projects $allProjects)
    }

    $script:DiscoveryCache[$cacheKey] = $discovery
    $discovery
}

function Get-ExactProjectMatches {
    param(
        [string]$Query,
        [object[]]$Projects,
        [string[]]$DistroOrder
    )

    if (-not $Query) {
        return @()
    }

    $orderMap = @{}
    for ($i = 0; $i -lt $DistroOrder.Count; $i++) {
        $orderMap[$DistroOrder[$i]] = $i
    }

    $needle = $Query.ToLowerInvariant()
    $matches = foreach ($project in $Projects) {
        $name = $project.Name.ToLowerInvariant()
        $path = $project.LinuxPath.ToLowerInvariant()
        $score = -1
        $matchType = $null

        if ($name -eq $needle) {
            $score = 100
            $matchType = "exact-name"
        }
        elseif ($path -eq $needle -or $path.EndsWith("/$needle")) {
            $score = 95
            $matchType = "exact-path-suffix"
        }

        if ($score -ge 0) {
            [pscustomobject]@{
                Distro = $project.Distro
                LinuxPath = $project.LinuxPath
                Name = $project.Name
                Score = $score
                MatchType = $matchType
                DistroRank = $orderMap[$project.Distro]
            }
        }
    }

    $matches | Sort-Object `
        @{ Expression = { -$_.Score } }, `
        @{ Expression = { $_.DistroRank } }, `
        Name, `
        LinuxPath
}

function Get-FuzzyProjectMatches {
    param(
        [string]$Query,
        [object[]]$Projects,
        [string[]]$DistroOrder
    )

    if (-not $Query) {
        return @()
    }

    $orderMap = @{}
    for ($i = 0; $i -lt $DistroOrder.Count; $i++) {
        $orderMap[$DistroOrder[$i]] = $i
    }

    $needle = $Query.ToLowerInvariant()
    $matches = foreach ($project in $Projects) {
        $name = $project.Name.ToLowerInvariant()
        $path = $project.LinuxPath.ToLowerInvariant()
        $score = -1
        $matchType = $null

        if ($name.Contains($needle)) {
            $score = 80
            $matchType = "name-contains"
        }
        elseif ($path.Contains("/$needle/")) {
            $score = 75
            $matchType = "path-segment-contains"
        }
        elseif ($path.Contains($needle)) {
            $score = 70
            $matchType = "path-contains"
        }

        if ($score -ge 0) {
            [pscustomobject]@{
                Distro = $project.Distro
                LinuxPath = $project.LinuxPath
                Name = $project.Name
                Score = $score
                MatchType = $matchType
                DistroRank = $orderMap[$project.Distro]
            }
        }
    }

    $matches | Sort-Object `
        @{ Expression = { -$_.Score } }, `
        @{ Expression = { $_.DistroRank } }, `
        Name, `
        LinuxPath
}

function Resolve-WslProject {
    param(
        [string]$ProjectQuery,
        [string]$RequestedDistro,
        [string[]]$RequestedRoots,
        [int]$SearchDepth,
        [switch]$AllowHomeFallback,
        [switch]$IncludeNestedCandidates,
        [switch]$ReturnAllMatches
    )

    $distros = @(Get-PreferredDistros -RequestedDistro $RequestedDistro)
    $distroNames = @($distros | Select-Object -ExpandProperty Name)

    if ([string]::IsNullOrWhiteSpace($ProjectQuery)) {
        $selected = $distros[0]
        $linuxHome = Get-WslHome -DistroName $selected.Name
        return [pscustomobject]@{
            Status = "resolved"
            Distro = $selected.Name
            LinuxPath = $linuxHome
            WindowsPath = Get-WslWindowsPath -DistroName $selected.Name -LinuxPath $linuxHome
            Name = Get-LeafName -Path $linuxHome
            MatchType = "home"
        }
    }

    if ($ProjectQuery -match '^\\\\wsl(?:\.localhost)?\\(?<distro>[^\\]+)\\(?<rest>.*)$') {
        $uncDistro = $matches.distro
        $linuxPath = "/" + (($matches.rest -replace '\\', '/').TrimStart('/'))
        return Resolve-WslProject -ProjectQuery $linuxPath -RequestedDistro $uncDistro -RequestedRoots $RequestedRoots -SearchDepth $SearchDepth -AllowHomeFallback:$AllowHomeFallback -IncludeNestedCandidates:$IncludeNestedCandidates -ReturnAllMatches:$ReturnAllMatches
    }

    if ($ProjectQuery -match '^[A-Za-z]:[\\/]') {
        $targetDistro = $distros[0].Name
        $linuxPath = (Invoke-WslCapture -Arguments @("-d", $targetDistro, "--", "wslpath", ($ProjectQuery -replace '\\', '/'))).Output
        return [pscustomobject]@{
            Status = "resolved"
            Distro = $targetDistro
            LinuxPath = $linuxPath
            WindowsPath = $ProjectQuery
            Name = Get-LeafName -Path $linuxPath
            MatchType = "windows-path"
        }
    }

    if ($ProjectQuery.StartsWith("/")) {
        foreach ($candidate in $distros) {
            if (Test-WslPathExists -DistroName $candidate.Name -LinuxPath $ProjectQuery) {
                return [pscustomobject]@{
                    Status = "resolved"
                    Distro = $candidate.Name
                    LinuxPath = $ProjectQuery
                    WindowsPath = Get-WslWindowsPath -DistroName $candidate.Name -LinuxPath $ProjectQuery
                    Name = Get-LeafName -Path $ProjectQuery
                    MatchType = "linux-path"
                }
            }
        }

        throw "Linux path not found in the selected distros: $ProjectQuery"
    }

    $discoveries = foreach ($candidate in $distros) {
        $roots = Normalize-SearchRoots -DistroName $candidate.Name -RequestedRoots $RequestedRoots -AllowHomeFallback:$AllowHomeFallback
        Discover-WslProjects -DistroName $candidate.Name -Roots $roots -SearchDepth $SearchDepth
    }

    $allProjects = @($discoveries | ForEach-Object { $_.AllCandidates })
    $matchProjects = @($discoveries | ForEach-Object {
        if ($IncludeNestedCandidates) {
            $_.AllCandidates
        }
        else {
            $_.TopLevelCandidates
        }
    })

    $matches = @(Get-ExactProjectMatches -Query $ProjectQuery -Projects $allProjects -DistroOrder $distroNames)
    if (-not $matches) {
        $matches = @(Get-FuzzyProjectMatches -Query $ProjectQuery -Projects $matchProjects -DistroOrder $distroNames)
    }

    if (-not $matches) {
        throw "No WSL project matched: $ProjectQuery"
    }

    if ($ReturnAllMatches) {
        return [pscustomobject]@{
            Status = "matches"
            Matches = $matches | ForEach-Object {
                [pscustomobject]@{
                    Distro = $_.Distro
                    LinuxPath = $_.LinuxPath
                    Name = $_.Name
                    MatchType = $_.MatchType
                    Score = $_.Score
                }
            }
        }
    }

    $topScore = $matches[0].Score
    $topMatches = @($matches | Where-Object { $_.Score -eq $topScore })

    if ($topMatches.Count -gt 1) {
        return [pscustomobject]@{
            Status = "ambiguous"
            Query = $ProjectQuery
            Matches = $topMatches | ForEach-Object {
                [pscustomobject]@{
                    Distro = $_.Distro
                    LinuxPath = $_.LinuxPath
                    Name = $_.Name
                    MatchType = $_.MatchType
                    Score = $_.Score
                }
            }
        }
    }

    $resolved = $matches[0]
    [pscustomobject]@{
        Status = "resolved"
        Distro = $resolved.Distro
        LinuxPath = $resolved.LinuxPath
        WindowsPath = Get-WslWindowsPath -DistroName $resolved.Distro -LinuxPath $resolved.LinuxPath
        Name = $resolved.Name
        MatchType = $resolved.MatchType
    }
}

function Write-Json {
    param($Value)

    $Value | ConvertTo-Json -Depth 6
}

switch ($Mode) {
    "discover" {
        $distros = @(Get-PreferredDistros -RequestedDistro $Distro)
        $projects = foreach ($candidate in $distros) {
            $roots = Normalize-SearchRoots -DistroName $candidate.Name -RequestedRoots $SearchRoots -AllowHomeFallback:$IncludeHomeFallback
            $discovery = Discover-WslProjects -DistroName $candidate.Name -Roots $roots -SearchDepth $MaxDepth
            if ($IncludeNested) {
                $discovery.AllCandidates
            }
            else {
                $discovery.TopLevelCandidates
            }
        }

        $projects = @($projects | Sort-Object Distro, Name, LinuxPath)

        if ($Json) {
            Write-Json @{
                status = "ok"
                mode = "discover"
                includeNested = [bool]$IncludeNested
                projects = $projects
            }
            break
        }

        if (-not $projects) {
            "No WSL projects discovered."
            break
        }

        $projects | Format-Table Distro, Name, LinuxPath -AutoSize | Out-String
        break
    }

    "resolve" {
        $resolved = Resolve-WslProject -ProjectQuery $Project -RequestedDistro $Distro -RequestedRoots $SearchRoots -SearchDepth $MaxDepth -AllowHomeFallback:$IncludeHomeFallback -IncludeNestedCandidates:$IncludeNested -ReturnAllMatches:$AllMatches

        if ($Json) {
            Write-Json $resolved
            break
        }

        if ($resolved.Status -eq "ambiguous") {
            "Ambiguous project match:"
            $resolved.Matches | Format-Table Distro, Name, LinuxPath, MatchType, Score -AutoSize | Out-String
            exit 2
        }

        if ($resolved.Status -eq "matches") {
            $resolved.Matches | Format-Table Distro, Name, LinuxPath, MatchType, Score -AutoSize | Out-String
            break
        }

        @(
            "Distro: $($resolved.Distro)"
            "LinuxPath: $($resolved.LinuxPath)"
            "WindowsPath: $($resolved.WindowsPath)"
            "Name: $($resolved.Name)"
            "MatchType: $($resolved.MatchType)"
        ) -join [Environment]::NewLine
        break
    }

    "exec" {
        if (-not $Command) {
            throw "Mode exec requires -Command."
        }

        $resolved = Resolve-WslProject -ProjectQuery $Project -RequestedDistro $Distro -RequestedRoots $SearchRoots -SearchDepth $MaxDepth -AllowHomeFallback:$IncludeHomeFallback -IncludeNestedCandidates:$IncludeNested

        if ($resolved.Status -eq "ambiguous") {
            if ($Json) {
                Write-Json $resolved
            }
            else {
                "Ambiguous project match:"
                $resolved.Matches | Format-Table Distro, Name, LinuxPath, MatchType, Score -AutoSize | Out-String
            }
            exit 2
        }

        $pathLiteral = ConvertTo-BashLiteral $resolved.LinuxPath
        $bashScript = "cd $pathLiteral && $Command"
        $result = Invoke-WslCapture -Arguments @("-d", $resolved.Distro, "--", "bash", "-lc", $bashScript) -AllowFailure

        if ($Json) {
            Write-Json @{
                status = "executed"
                distro = $resolved.Distro
                linuxPath = $resolved.LinuxPath
                windowsPath = $resolved.WindowsPath
                command = $Command
                exitCode = $result.ExitCode
                output = $result.Output
            }
        }
        elseif ($result.Output) {
            $result.Output
        }

        exit $result.ExitCode
    }
}
