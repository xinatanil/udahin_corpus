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
	new_counts=$(mktemp)
	old_counts=$(mktemp)
	diff_output=$(mktemp)
	
	# Get raw counts (count tag_name)
	grep -oE '<[a-zA-Z0-9_:-]+' "$processed_file" | sed 's/^<//' | sort | uniq -c | sort -nr > "$raw_counts"
	
	# Prioritize specific tags and format as "tag count"
	for tag in card trn meaning meta origin wordLink blockquote; do
	    line=$(awk -v t="$tag" '$2==t {print $0}' "$raw_counts")
	    if [ -n "$line" ]; then
	        count=$(echo "$line" | awk '{print $1}')
	        echo "$tag $count" >> "$new_counts"
	    else
	        echo "$tag 0" >> "$new_counts"
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
	            echo "$tag $count" >> "$new_counts"
	            ;;
	    esac
	done < "$raw_counts"

	# Extract old counts from the previous run
	if [ -f "${dir}/tag_counts.txt" ]; then
	    old_file="${dir}/tag_counts.txt"
	elif [ -f "tag_counts.txt" ]; then
	    old_file="tag_counts.txt"
	else
	    old_file=""
	fi

	if [ -n "$old_file" ]; then
	    awk '
	    /^--- Tag counts/ {
	        if (found) exit
	        found=1
	        next
	    }
	    found && NF==2 && $1 ~ /^[a-zA-Z0-9_:-]+$/ && $2 ~ /^[0-9]+$/ {
	        print $1, $2
	    }
	    ' "$old_file" > "$old_counts"
	fi

	# Compare old and new counts
	if [ -s "$old_counts" ]; then
	    awk '
	    NR==FNR { old[$1] = $2; next }
	    {
	        new_tag = $1
	        new_count = $2
	        old_count = old[new_tag]
	        if (old_count == "") {
	            old_count = 0
	        }
	        
	        diff = new_count - old_count
	        if (diff > 0) {
	            print diff " more <" new_tag "> since last count"
	        } else if (diff < 0) {
	            print (-diff) " less <" new_tag "> since last count"
	        }
	        delete old[new_tag]
	    }
	    END {
	        for (old_tag in old) {
	            if (old[old_tag] > 0) {
	                print old[old_tag] " less <" old_tag "> since last count"
	            }
	        }
	    }
	    ' "$old_counts" "$new_counts" > "$diff_output"
	fi

	# Assemble the final temp_counts
	echo "--- Tag counts for $filename ($(date)) ---" > "$temp_counts"

	if [ -s "$diff_output" ]; then
	    cat "$diff_output"
	    echo ""
	    cat "$diff_output" >> "$temp_counts"
	    echo "" >> "$temp_counts"
	fi

	cat "$new_counts" >> "$temp_counts"
	echo "" >> "$temp_counts"

	if [ -n "$old_file" ]; then
	    cat "$old_file" >> "$temp_counts"
	fi
	
	mv "$temp_counts" "${dir}/tag_counts.txt"
	rm -f "$raw_counts" "$new_counts" "$old_counts" "$diff_output"
