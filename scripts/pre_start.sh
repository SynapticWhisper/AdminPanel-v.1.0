#!/bin/bash

# Function to check the result of the last command and exit if it failed
check_result() {
    if [ $? -ne 0 ]; then
        echo "[!] $1"
        exit 1
    fi
}

# Generate RSA keys
echo "[i] GENERATING RSA-KEYS"
chmod +x ./scripts/create_secrets.sh
./scripts/create_secrets.sh
check_result "[!] FAILED TO GENERATE RSA KEYS"
echo "[+] SUCCESS"

echo

# Create .env file
echo "[i] CREATING .ENV FILE"
chmod +x ./scripts/create_dotenv.sh
./scripts/create_dotenv.sh
check_result "[!] FAILED TO CREATE .ENV FILE"
echo "[+] SUCCESS"

echo
