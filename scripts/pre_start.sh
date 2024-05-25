#!/bin/bash

HOME_DIR=".."

# Function to check the result of the last command and exit if it failed
check_result() {
    if [ $? -ne 0 ]; then
        echo "[!] $1"
        exit 1
    fi
}

# Create virtual environment and install requirements
echo "[i] CREATING A VIRTUAL ENVIRONMENT"
python3 -m venv $HOME_DIR/.venv
check_result "[!] FAILED TO CREATE VIRTUAL ENVIRONMENT"

source $HOME_DIR/.venv/bin/activate
check_result "[!] FAILED TO ACTIVATE VIRTUAL ENVIRONMENT"

# Count the number of lines in requirements.txt
req_file="$HOME_DIR/requirements.txt"
total_lines=$(wc -l < "$req_file")
check_result "[!] FAILED TO READ REQUIREMENTS FILE"

echo

echo "[i] INSTALLING REQUIREMENTS"
current_line=0

# Install requirements one by one
while IFS= read -r requirement; do
    pip install -q "$requirement"
    check_result "[!] FAILED TO INSTALL REQUIREMENT: $requirement"
    current_line=$((current_line + 1))
    echo "[+] INSTALLED $current_line/$total_lines: $requirement"
done < "$req_file"

echo "[+] SUCCESSFULLY INSTALLED ALL REQUIREMENTS"

echo 

# Generate RSA keys
echo "[i] GENERATING RSA-KEYS"
chmod +x create_secrets.sh
./create_secrets.sh
check_result "[!] FAILED TO GENERATE RSA KEYS"
echo "[+] SUCCESS"

echo

# Create .env file
echo "[i] CREATING .ENV FILE"
chmod +x create_dotenv.sh
./create_dotenv.sh
check_result "[!] FAILED TO CREATE .ENV FILE"
echo "[+] SUCCESS"

echo