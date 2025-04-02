
# Development notes

## Releases

In the repository settings, go to `Actions -> General -> Workflow permissions` and enable `Read and write permissions`.

A release is created when pushing a tag, e.g.:

```bash
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0
```

A tag can be deleted with:

```bash
# Delete the tag locally
git tag -d v1.0.0
# Delete the tag remotely
git push origin :refs/tags/v1.0.0
# or
git push origin --delete v1.0.0
```

## Certificate

### 1. Generate a self-signed certificate
```powershell
$cert = New-SelfSignedCertificate -Type CodeSigningCert -Subject "CN=Syncthing Overlay" -CertStoreLocation Cert:\CurrentUser\My

# Export the certificate to a PFX file
Export-PfxCertificate -Cert $cert -FilePath "syncthing-overlay.pfx" -Password (ConvertTo-SecureString -String "yourpassword" -Force -AsPlainText)
```

### 2. Add secrets to GitHub

1. Go to your repository's `Settings > Secrets and variables > Actions`.
2. Add the following secrets:
  - `CERT_PASSWORD`: The password you used when exporting the `.pfx` file.
  - `CERT_FILE`: Base64-encoded content of the `.pfx` file.

To encode the `.pfx` file in Base64, run this command locally:

```powershell
[Convert]::ToBase64String((Get-Content -Path "syncthing-overlay.pfx" -AsByteStream)) > cert_base64.txt
```
Copy the content of cert_base64.txt and add it as the `CERT_FILE` secret.

### 3. Notes:

- A self-signed certificate will still show a warning unless the user manually trusts it.
- For production, consider purchasing a certificate from a trusted Certificate Authority (CA), like DigiCert, Sectigo, or GlobalSign.