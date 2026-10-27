# Creates a read-only BigQuery service account for the hosted dashboard and writes the
# Streamlit secrets block to paste into share.streamlit.io -> app -> Settings -> Secrets.
# Run it yourself after `gcloud auth login`. The key file and secrets file are NEVER committed.
param(
    [string]$Project = "project-cc51f331-7539-4662-a83",
    [string]$OutDir  = "$env:USERPROFILE\idp-gcp-secrets"
)
$ErrorActionPreference = "Stop"
$sa = "idp-dashboard@$Project.iam.gserviceaccount.com"
New-Item -ItemType Directory -Force $OutDir | Out-Null

gcloud services enable iam.googleapis.com bigquerystorage.googleapis.com --project $Project
gcloud iam service-accounts create idp-dashboard --project $Project --display-name "IDP dashboard (read-only BigQuery)"
foreach ($role in "roles/bigquery.dataViewer", "roles/bigquery.jobUser", "roles/bigquery.readSessionUser") {
    gcloud projects add-iam-policy-binding $Project --member "serviceAccount:$sa" --role $role --condition None --format none
}
$key = Join-Path $OutDir "idp-dashboard-key.json"
gcloud iam service-accounts keys create $key --iam-account $sa
if ($LASTEXITCODE -ne 0) {   # e.g. org policy iam.disableServiceAccountKeyCreation is enforced
    Remove-Item $key -ErrorAction SilentlyContinue
    throw "Key creation failed - nothing written. See the error above."
}

# Convert the JSON key into the TOML block Streamlit expects
$j = Get-Content $key -Raw | ConvertFrom-Json
$lines = @("[bigquery]", "project = `"$Project`"", "dataset = `"idp`"", "", "[gcp_service_account]")
foreach ($p in $j.PSObject.Properties) {
    $v = ($p.Value -replace '\\', '\\' -replace "`n", '\n' -replace '"', '\"')
    $lines += "$($p.Name) = `"$v`""
}
$toml = Join-Path $OutDir "streamlit_secrets.toml"
$lines -join "`n" | Out-File -Encoding utf8 $toml
Write-Host "Done. Paste the contents of $toml into the app's Secrets box (keep any [postgres] block out)."
