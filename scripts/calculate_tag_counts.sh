#!/bin/bash

if [ -z "$1" ]; then
    echo "Usage: $0 <xml_file>"
    exit 1
fi

processed_file="$1"
dir=$(dirname "$processed_file")
filename=$(basename "$processed_file" .xml)

	temp_counts=$(mktemp)
	raw_counts=$(mktemp)
	
	echo "--- Tag counts for $filename ($(date)) ---" > "$temp_counts"
	
	# Get raw counts (count tag_name)
	grep -oE '<[a-zA-Z0-9_:-]+' "$processed_file" | sed 's/^<//' | sort | uniq -c | sort -nr > "$raw_counts"
	
	# Prioritize specific tags and format as "tag count"
	for tag in card trn meaning meta origin wordLink blockquote; do
	    line=$(awk -v t="$tag" '$2==t {print $0}' "$raw_counts")
	    if [ -n "$line" ]; then
	        count=$(echo "$line" | awk '{print $1}')
	        echo "$tag $count" >> "$temp_counts"
	    else
	        echo "$tag 0" >> "$temp_counts"
	    fi
	done
	
	# Output the remaining tags
	while read count tag; do
	    if [ -z "$tag" ]; then continue; fi
	    case "$tag" in
	        card|trn|meaning|meta|origin|wordLink|blockquote)
	            # Skip prioritized tags as they are already output
	            ;;
	        *)
	            echo "$tag $count" >> "$temp_counts"
	            ;;
	    esac
	done < "$raw_counts"
	
	echo "" >> "$temp_counts"

if [ -f "${dir}/tag_counts.txt" ]; then
    cat "${dir}/tag_counts.txt" >> "$temp_counts"
elif [ -f "tag_counts.txt" ]; then
    cat "tag_counts.txt" >> "$temp_counts"
fi

mv "$temp_counts" "${dir}/tag_counts.txt"
rm -f "$raw_counts"
