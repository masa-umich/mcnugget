# Fetch the certificate in security/synnax-ca.crt from web and install it in the system keychain
# This script is used by the Windows installer to install the certificate in the system keychain
Write-Host "Fetching certificate from web..."
Invoke-WebRequest -Uri https://raw.githubusercontent.com/masa-umich/mcnugget/main/security/synnax-ca.crt -OutFile synnax-ca.crt
Write-Host "Installing certificate in system keychain. You may be prompted for administrator credentials."
Import-Certificate -FilePath synnax-ca.crt -CertStoreLocation Cert:\LocalMachine\Root
Write-Host "Installed certificate in system keychain. You're good to go!"
