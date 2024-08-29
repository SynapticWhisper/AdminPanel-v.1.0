#!/bin/bash

DIR="certs"

if [ ! -d "$DIR" ]; then
    echo "[!] Directory '$DIR' isn't exist. Creating..."
    mkdir -p "$DIR"
    echo "[+] Directory '$DIR' was created successfully."
else
    echo "[i] Directory '$DIR' already exists."
fi

openssl genrsa -out "$DIR/jwt-private.pem" 2048
openssl rsa -in "$DIR/jwt-private.pem" -outform PEM -pubout -out "$DIR/jwt-public.pem"

echo "[+] Private and Public rsa-keys were saved to $DIR"