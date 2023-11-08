# Fetch the certificate in security/synnax-ca.crt and install it in the system keychain
echo "Fetching the Synnax CA certificate"
curl -s https://raw.githubusercontent.com/masa-umich/mcnugget/main/security/synnax-ca.crt > /tmp/synnax-ca.crt
echo "Installing the Synnax CA certificate. You may be prompted for your password"
sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain /tmp/synnax-ca.crt
echo "Installed the Synnax CA certificate. You're good to go!"