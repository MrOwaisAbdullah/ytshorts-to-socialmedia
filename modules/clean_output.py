import re

def clean_output(text):
    lines = text.split('\n')
    clean_lines = []
    for line in lines:
        if re.match(r'^\s*\d+[\.\)]\s*', line.lower()) or re.match(r'^\s*thread', line.lower()):
            continue
        clean_lines.append(line.strip())
    return "\n".join(clean_lines)
