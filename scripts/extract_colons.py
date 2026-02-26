import re
import sys
from collections import defaultdict

input_file = sys.argv[1] if len(sys.argv) > 1 else '/Users/xinatanil/Sources/udahin/sources/corrected_source_dict.xml'


def is_content_line(line):
    """Check if a line has actual content (not just bare XML tags like </card>, <card>, etc.)."""
    stripped = line.strip()
    if not stripped:
        return False
    # Pure opening/closing tags with no text content
    if re.match(r'^</?[a-zA-Z0-9_]+>$', stripped):
        return False
    return True


def gather_context(lines, match_idx, n_before=2, n_after=2):
    """
    Gather n content lines before and after match_idx, skipping bare tag lines.
    Returns a list of lines including the match line.
    """
    # Gather content lines before
    before = []
    j = match_idx - 1
    while len(before) < n_before and j >= 0:
        if is_content_line(lines[j]):
            before.append(lines[j])
        j -= 1
    before.reverse()

    # Gather content lines after
    after = []
    j = match_idx + 1
    while len(after) < n_after and j < len(lines):
        if is_content_line(lines[j]):
            after.append(lines[j])
        j += 1

    return before + [lines[match_idx]] + after


ending_with_colon = []
rest_by_tag = defaultdict(list)

with open(input_file, 'r', encoding='utf-8') as f:
    lines = [line.strip() for line in f]

for i, line in enumerate(lines):
    match = re.match(r'^<([a-zA-Z0-9_]+)>(.*:.*)</\1>$', line)
    if match:
        tag = match.group(1)
        content = match.group(2).strip()

        context_lines = gather_context(lines, i)
        # Format: match line first, then --- separator, then full context
        combined_block = line + "\n---\n" + "\n".join(context_lines)

        if content.endswith(':'):
            ending_with_colon.append(combined_block)
        else:
            rest_by_tag[tag].append(combined_block)
    else:
        if ':' in line and line.startswith('<') and line.endswith('>'):
            closing_match = re.search(r'</([a-zA-Z0-9_]+)>$', line)
            if closing_match:
                tag = closing_match.group(1)
                content_before_closing = line[:-len(closing_match.group(0))].strip()

                context_lines = gather_context(lines, i)
                # Format: match line first, then --- separator, then full context
                combined_block = line + "\n---\n" + "\n".join(context_lines)

                if content_before_closing.endswith(':'):
                    ending_with_colon.append(combined_block)
                else:
                    rest_by_tag[tag].append(combined_block)

with open('/Users/xinatanil/Sources/udahin/chatGPT_exp/tags_ending_with_colon.txt', 'w', encoding='utf-8') as f:
    for block in sorted(ending_with_colon):
        f.write(block + '\n\n')

for tag, blocks_list in rest_by_tag.items():
    with open(f'/Users/xinatanil/Sources/udahin/chatGPT_exp/tags_rest_{tag}.txt', 'w', encoding='utf-8') as f:
        for block in sorted(blocks_list):
            f.write(block + '\n\n')
