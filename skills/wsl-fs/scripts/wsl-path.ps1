param(
    [Parameter(Mandatory = $true)]
    [string]$Path,

    [string]$Distro = "Ubuntu-22.04",

    [ValidateSet("to-wsl", "to-win")]
    [string]$Mode = "to-wsl"
)

if ($Mode -eq "to-wsl") {
    $normalized = $Path -replace '\\', '/'
    wsl.exe -d $Distro -- wslpath $normalized
    exit $LASTEXITCODE
}

wsl.exe -d $Distro -- wslpath -w $Path
exit $LASTEXITCODE
