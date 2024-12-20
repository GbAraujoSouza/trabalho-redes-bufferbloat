#!/bin/bash

# Function to display usage instructions
usage() {
  echo "Usage: $0 <file_path> [spaces_per_tab]"
  echo "  <file_path>: Path to the file to be converted."
  echo "  [spaces_per_tab]: Optional. Number of spaces per tab. Default is 4."
  exit 1
}

# Check if at least one argument (file_path) is provided
if [ "$#" -lt 1 ]; then
  usage
fi

# Get the file path and number of spaces per tab
file_path="$1"
spaces_per_tab="${2:-4}"  # Default to 4 spaces if not provided

# Validate that the file exists
if [ ! -f "$file_path" ]; then
  echo "Error: File '$file_path' not found."
  exit 1
fi

# Create the string of spaces to replace tabs
spaces=$(printf '%*s' "$spaces_per_tab")

# Replace tabs with spaces and overwrite the file
sed -i "s/\t/$spaces/g" "$file_path"

echo "Successfully converted tabs to $spaces_per_tab spaces in '$file_path'."

