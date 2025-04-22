#!/bin/bash

OUTPUT_FILE="merged_codebase.txt"
ROOT_DIR=$(pwd)  # Change this if needed

# Function to read .gitignore and create exclusion patterns
get_gitignore_patterns() {
    local gitignore_file="$1"
    local ignore_patterns=()

    if [[ -f "$gitignore_file" ]]; then
        while IFS= read -r line; do
            [[ -z "$line" || "$line" =~ ^# ]] && continue  # Skip empty lines and comments
            ignore_patterns+=("--exclude=$line")
        done < "$gitignore_file"
    fi

    echo "${ignore_patterns[@]}"
}

# Generate file tree while excluding hidden files and ignored patterns
echo "Generating file tree..."
IGNORE_PATTERNS=$(get_gitignore_patterns "$ROOT_DIR/.gitignore")
FILE_TREE=$(tree -a -I '.*' "${IGNORE_PATTERNS[@]}" "$ROOT_DIR")
echo -e "### FILE TREE ###\n$FILE_TREE\n\n" > "$OUTPUT_FILE"

# Find all relevant files
echo "Merging files..."
find "$ROOT_DIR" -type f ! -path '*/.*' ! -name "*.pyc" | while read -r file; do
    # Check if file is ignored
    relative_path=$(realpath --relative-to="$ROOT_DIR" "$file")
    if grep -qxF "$relative_path" "$ROOT_DIR/.gitignore" 2>/dev/null; then
        continue
    fi

    echo -e "\n### FILE: $relative_path ###\n" >> "$OUTPUT_FILE"
    cat "$file" >> "$OUTPUT_FILE"
done

echo "Merged codebase saved to $OUTPUT_FILE"
