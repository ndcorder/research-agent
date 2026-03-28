#!/usr/bin/env bash
# pdf-cache.sh — Shared PDF cache for cross-project paper reuse
#
# Usage:
#   pdf-cache.sh lookup <doi> <title>
#   pdf-cache.sh store  <bibtexkey> <pdf_path> <title> [<doi> <resolver> <source_url> <authors>]
#   pdf-cache.sh link   <cache_key> <project_dir> <local_bibtexkey>
#   pdf-cache.sh list
#   pdf-cache.sh info   <cache_key>

set -euo pipefail

CACHE_DIR="${HOME}/.research-agent/pdf-cache"

# --- Helpers ---

normalize_title() {
    # Lowercase, strip punctuation, collapse whitespace, trim
    echo "$1" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9 ]//g' | tr -s ' ' | sed 's/^ *//;s/ *$//'
}

sha256_of() {
    shasum -a 256 "$1" | cut -d' ' -f1
}

json_get() {
    # Extract a simple string value from JSON. $1=file, $2=key
    python3 -c "import json,sys; d=json.load(open(sys.argv[1])); v=d.get(sys.argv[2],''); print(v if isinstance(v,str) else json.dumps(v))" "$1" "$2" 2>/dev/null || echo ""
}

ensure_cache_dir() {
    mkdir -p "$CACHE_DIR"
}

# Find a cache entry by DOI (exact) or title (normalized prefix match on first 80 chars)
# Prints the cache key if found, exits 0. Otherwise exits 1.
find_in_cache() {
    local search_doi="$1"
    local search_title="$2"
    local norm_search
    norm_search="$(normalize_title "$search_title")"
    # Truncate to first 80 chars for comparison
    norm_search="${norm_search:0:80}"

    if [ ! -d "$CACHE_DIR" ]; then
        return 1
    fi

    for meta in "$CACHE_DIR"/*.json; do
        [ -f "$meta" ] || continue

        # DOI match (exact, case-insensitive)
        if [ -n "$search_doi" ] && [ "$search_doi" != "-" ]; then
            local cached_doi
            cached_doi="$(json_get "$meta" doi)"
            if [ -n "$cached_doi" ]; then
                local lower_search lower_cached
                lower_search="$(echo "$search_doi" | tr '[:upper:]' '[:lower:]')"
                lower_cached="$(echo "$cached_doi" | tr '[:upper:]' '[:lower:]')"
                if [ "$lower_search" = "$lower_cached" ]; then
                    json_get "$meta" cache_key
                    return 0
                fi
            fi
        fi

        # SHA256 match skipped here (no file to hash during lookup)

        # Title match (normalized, first 80 chars)
        if [ -n "$norm_search" ]; then
            local cached_title
            cached_title="$(json_get "$meta" title)"
            local norm_cached
            norm_cached="$(normalize_title "$cached_title")"
            norm_cached="${norm_cached:0:80}"
            if [ -n "$norm_cached" ] && [ "$norm_search" = "$norm_cached" ]; then
                json_get "$meta" cache_key
                return 0
            fi
        fi
    done

    return 1
}

# --- Commands ---

cmd_lookup() {
    local doi="${1:--}"
    local title="${2:-}"

    if [ -z "$title" ] && [ "$doi" = "-" ]; then
        echo "Usage: pdf-cache.sh lookup <doi> <title>" >&2
        echo "  Use '-' for doi if unknown" >&2
        exit 1
    fi

    local cache_key
    if cache_key="$(find_in_cache "$doi" "$title")"; then
        echo "$cache_key"
        echo "${CACHE_DIR}/${cache_key}.pdf"
        exit 0
    fi
    exit 1
}

cmd_store() {
    local bibtexkey="${1:-}"
    local pdf_path="${2:-}"
    local title="${3:-}"
    local doi="${4:--}"
    local resolver="${5:-unknown}"
    local source_url="${6:--}"
    local authors="${7:--}"

    if [ -z "$bibtexkey" ] || [ -z "$pdf_path" ] || [ -z "$title" ]; then
        echo "Usage: pdf-cache.sh store <bibtexkey> <pdf_path> <title> [<doi> <resolver> <source_url> <authors>]" >&2
        exit 1
    fi

    if [ ! -f "$pdf_path" ]; then
        echo "Error: PDF not found: $pdf_path" >&2
        exit 1
    fi

    ensure_cache_dir

    local file_hash
    file_hash="$(sha256_of "$pdf_path")"

    # Check if already cached by DOI or title
    local existing_key
    if existing_key="$(find_in_cache "$doi" "$title")"; then
        # Verify it's the same file or a valid match
        local existing_hash
        existing_hash="$(json_get "${CACHE_DIR}/${existing_key}.json" sha256)"
        if [ "$file_hash" = "$existing_hash" ]; then
            echo "$existing_key"
            return 0
        fi
        # DOI/title match but different file — could be updated version
        # Replace with newer version
        cp "$pdf_path" "${CACHE_DIR}/${existing_key}.pdf"
        # Update metadata
        python3 -c "
import json, sys
meta_path = sys.argv[1]
with open(meta_path) as f:
    d = json.load(f)
d['sha256'] = sys.argv[2]
d['file_size_bytes'] = int(sys.argv[3])
d['cached_at'] = sys.argv[4]
with open(meta_path, 'w') as f:
    json.dump(d, f, indent=2)
" "${CACHE_DIR}/${existing_key}.json" "$file_hash" "$(wc -c < "$pdf_path" | tr -d ' ')" "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
        echo "$existing_key"
        return 0
    fi

    # Check for sha256 match across all entries
    for meta in "$CACHE_DIR"/*.json; do
        [ -f "$meta" ] || continue
        local cached_hash
        cached_hash="$(json_get "$meta" sha256)"
        if [ "$file_hash" = "$cached_hash" ]; then
            json_get "$meta" cache_key
            return 0
        fi
    done

    # New entry — resolve key collisions
    local cache_key="$bibtexkey"
    if [ -f "${CACHE_DIR}/${cache_key}.json" ]; then
        # Key collision with a different paper — add suffix
        local suffix_char=97  # 'a'
        while [ -f "${CACHE_DIR}/${cache_key}.json" ]; do
            cache_key="${bibtexkey}$(printf "\\x$(printf '%02x' $suffix_char)")"
            suffix_char=$((suffix_char + 1))
            if [ $suffix_char -gt 122 ]; then
                echo "Error: too many collisions for key $bibtexkey" >&2
                exit 1
            fi
        done
    fi

    # Copy PDF to cache
    cp "$pdf_path" "${CACHE_DIR}/${cache_key}.pdf"

    # Write metadata sidecar
    local file_size
    file_size="$(wc -c < "$pdf_path" | tr -d ' ')"
    local cached_at
    cached_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

    python3 -c "
import json, sys
meta = {
    'cache_key': sys.argv[1],
    'title': sys.argv[2],
    'authors': json.loads(sys.argv[3]) if sys.argv[3] != '-' else [],
    'doi': sys.argv[4] if sys.argv[4] != '-' else '',
    'sha256': sys.argv[5],
    'file_size_bytes': int(sys.argv[6]),
    'resolver': sys.argv[7],
    'source_url': sys.argv[8] if sys.argv[8] != '-' else '',
    'cached_at': sys.argv[9],
    'projects': []
}
with open(sys.argv[10], 'w') as f:
    json.dump(meta, f, indent=2)
" "$cache_key" "$title" "$authors" "$doi" "$file_hash" "$file_size" "$resolver" "$source_url" "$cached_at" "${CACHE_DIR}/${cache_key}.json"

    echo "$cache_key"
}

cmd_link() {
    local cache_key="${1:-}"
    local project_dir="${2:-}"
    local local_key="${3:-}"

    if [ -z "$cache_key" ] || [ -z "$project_dir" ] || [ -z "$local_key" ]; then
        echo "Usage: pdf-cache.sh link <cache_key> <project_dir> <local_bibtexkey>" >&2
        exit 1
    fi

    local cache_pdf="${CACHE_DIR}/${cache_key}.pdf"
    local cache_meta="${CACHE_DIR}/${cache_key}.json"
    local target="${project_dir}/attachments/${local_key}.pdf"

    if [ ! -f "$cache_pdf" ]; then
        echo "Error: cached PDF not found: $cache_pdf" >&2
        exit 1
    fi

    # Ensure attachments directory exists
    mkdir -p "${project_dir}/attachments"

    # Remove existing file/symlink at target
    rm -f "$target"

    # Create symlink for PDF
    ln -s "$cache_pdf" "$target"

    # Also symlink parsed markdown and figures if they exist in the cache
    local cache_md="${CACHE_DIR}/${cache_key}.md"
    local cache_figures="${CACHE_DIR}/${cache_key}_figures"
    local parsed_dir="${project_dir}/attachments/parsed"
    local target_md="${parsed_dir}/${local_key}.md"
    local target_figures="${parsed_dir}/${local_key}_figures"

    if [ -f "$cache_md" ] || [ -d "$cache_figures" ]; then
        mkdir -p "$parsed_dir"
    fi

    if [ -f "$cache_md" ]; then
        rm -f "$target_md"
        ln -s "$cache_md" "$target_md"
    fi

    if [ -d "$cache_figures" ]; then
        rm -f "$target_figures"
        ln -s "$cache_figures" "$target_figures"
    fi

    # Add project to metadata's projects list
    if [ -f "$cache_meta" ]; then
        local project_name
        project_name="$(basename "$project_dir")"
        python3 -c "
import json, sys
meta_path, project = sys.argv[1], sys.argv[2]
with open(meta_path) as f:
    d = json.load(f)
if project not in d.get('projects', []):
    d.setdefault('projects', []).append(project)
    with open(meta_path, 'w') as f:
        json.dump(d, f, indent=2)
" "$cache_meta" "$project_name"
    fi

    echo "Linked: $target -> $cache_pdf"
}

cmd_list() {
    if [ ! -d "$CACHE_DIR" ]; then
        echo "No PDF cache found at $CACHE_DIR"
        exit 0
    fi

    local count=0
    for meta in "$CACHE_DIR"/*.json; do
        [ -f "$meta" ] || continue
        local key title doi projects
        key="$(json_get "$meta" cache_key)"
        title="$(json_get "$meta" title)"
        doi="$(json_get "$meta" doi)"
        projects="$(python3 -c "import json; d=json.load(open('$meta')); print(', '.join(d.get('projects',[])))" 2>/dev/null || echo "")"
        printf "%s  %s" "$key" "$title"
        [ -n "$doi" ] && printf "  (DOI: %s)" "$doi"
        [ -n "$projects" ] && printf "  [%s]" "$projects"
        printf "\n"
        count=$((count + 1))
    done

    echo "---"
    echo "$count cached PDFs in $CACHE_DIR"
}

cmd_info() {
    local cache_key="${1:-}"
    if [ -z "$cache_key" ]; then
        echo "Usage: pdf-cache.sh info <cache_key>" >&2
        exit 1
    fi

    local meta="${CACHE_DIR}/${cache_key}.json"
    if [ ! -f "$meta" ]; then
        echo "Not found: $cache_key" >&2
        exit 1
    fi

    python3 -c "import json; print(json.dumps(json.load(open('$meta')), indent=2))"
}

# --- Main ---

cmd="${1:-}"
shift || true

case "$cmd" in
    lookup) cmd_lookup "$@" ;;
    store)  cmd_store "$@" ;;
    link)   cmd_link "$@" ;;
    list)   cmd_list ;;
    info)   cmd_info "$@" ;;
    *)
        echo "pdf-cache.sh — Shared PDF cache for cross-project paper reuse" >&2
        echo "" >&2
        echo "Commands:" >&2
        echo "  lookup <doi> <title>          Search cache by DOI or title" >&2
        echo "  store  <key> <pdf> <title> [<doi> <resolver> <url> <authors>]" >&2
        echo "  link   <cache_key> <project_dir> <local_key>" >&2
        echo "  list                          List all cached PDFs" >&2
        echo "  info   <cache_key>            Show metadata for a cached PDF" >&2
        exit 1
        ;;
esac
