#!/bin/bash

prompt_input() {
    local prompt_message="$1"
    local user_input
    read -p "$prompt_message" user_input
    echo "$user_input"
}

prompt_secret_input() {
    local prompt_message="$1"
    local user_input
    read -s -p "$prompt_message" user_input
    echo
    echo "$user_input"
}

sanitize_input() {
    local input="$1"
    echo "$input" | tr -d '\n\r'
}

db_user=$(prompt_input "[*] DB user: ")
db_password=$(prompt_secret_input "[*] DB password: ")
echo
db_name=$(prompt_input "[*] DB: ")
redis_url=$(prompt_input "[*] Redis url: ")
smtp_user=$(prompt_input "[*] SMTP email: ")
smtp_password=$(prompt_secret_input "[*] SMTP password: ")
echo

db_user=$(sanitize_input "$db_user")
db_password=$(sanitize_input "$db_password")
db_name=$(sanitize_input "$db_name")
smtp_user=$(sanitize_input "$smtp_user")
smtp_password=$(sanitize_input "$smtp_password")

output_file=".env"

{
    printf "DB_URL=postgresql+asyncpg://%s:%s@localhost:5432/%s\n" "$db_user" "$db_password" "$db_name"
    printf "REDIS_URL=%s\n" "$redis_url"
    printf "SMTP_USER=%s\n" "$smtp_user"
    printf "SMTP_PASSWORD=%s\n" "$smtp_password"
} > "$output_file"

echo "[+] Information saved in $output_file"

