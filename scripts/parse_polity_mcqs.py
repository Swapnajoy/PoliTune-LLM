import os
import re
import json
import pdfplumber

pdf_path = "assets/polity_chapters/chapter_008_political_parties_and_pressure_groups.pdf"
output_dir = "data/train/"

os.makedirs(output_dir, exist_ok=True)

def extract_lines(pdf_path):
    import re
    lines = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            for line in text.splitlines():
                line = line.strip()

                # Skip empty or noisy lines
                if not line:
                    continue
                if line.lower().startswith("join telegram"):
                    continue

                # Remove text like [2012-I], [UPSC 2020] etc.
                line = re.sub(r'\[[^\]]*\]', '', line).strip()

                # Skip if becomes empty after removing brackets
                if not line:
                    continue

                lines.append(line)
    print(lines)
    return lines

def extract_chapter_id_title(filename):
    basename = filename.replace(".pdf", "")
    parts = basename.split("_")
    chapter_id = int(parts[1])
    chapter_title = " ".join(parts[2:]).replace("-", " ").strip()
    return chapter_id, chapter_title

def split_into_question_blocks(lines):
    qblocks = {}
    qnum = 1
    current_block = []
    inside_block = False

    for line in lines:
        q_match = re.match(rf'^{qnum}\.\s*(.*)', line)
        if q_match:
            if inside_block:
                qblocks[qnum] = current_block
                qnum += 1
                current_block = []

            inside_block = True
            current_block.append(q_match.group(1).strip())

        elif inside_block:
            next_q_match = re.match(rf'^{qnum + 1}\.\s*(.*)', line)
            if next_q_match:
                qblocks[qnum] = current_block
                qnum += 1
                current_block = [next_q_match.group(1).strip()]
            else:
                current_block.append(line.strip())

    if current_block and inside_block:
        qblocks[qnum] = current_block
    print(qblocks)
    return qblocks

def detect_question_type(block_lines):
    joined = " ".join(block_lines).lower()
    if "list-i" in joined and "list-ii" in joined:
        return "match"
    elif "assertion" in joined and "reason" in joined:
        return "assertion_reason"
    elif any(re.match(r'^\s*\d[\.\)]', ln) for ln in block_lines):
        return "statements_correctness"
    else:
        return "mcq_single"

def extract_input_and_options(block_lines):
    input_lines = []
    options = {}
    current_opt = None

    for line in block_lines:
        # Match strictly lowercase (a)-(d) only, with or without spaces
        opt_match = re.match(r'^\(([a-d])\)\s*(.*)', line)
        if opt_match:
            current_opt = opt_match.group(1).upper()
            options[current_opt] = opt_match.group(2).strip()
        elif current_opt:
            # Append wrapped line to current option
            options[current_opt] += " " + line.strip()
        else:
            # Before first option starts → part of stem
            input_lines.append(line.strip())

    input_text = " ".join(input_lines).strip()
    return input_text, options

def make_filename(chapter_id, qnum):
    return f"{chapter_id:03d}_{qnum:03d}.json"

def process_chapter(pdf_path, output_dir):
    filename = os.path.basename(pdf_path)
    lines = extract_lines(pdf_path)
    chapter_id, chapter_title = extract_chapter_id_title(filename)
    question_blocks = split_into_question_blocks(lines)

    for qnum, block in question_blocks.items():
        qtype = detect_question_type(block)
        input_text, options = extract_input_and_options(block)

        qjson = {
            "chapter_id": chapter_id,
            "chapter_title": chapter_title,
            "qnum": qnum,
            "type": qtype,
            "input": input_text,
            "options": options,
            "choices": ["A", "B", "C", "D"],
            "answer": "",
            "explanation": "",
            "metadata": {
                "schema": "mcq_uniform_v1",
                "extra": {}
            }
        }

        out_path = os.path.join(output_dir, make_filename(chapter_id, qnum))
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(qjson, f, indent=2, ensure_ascii=False)

    print(f"Extracted {len(question_blocks)} questions from {filename}")

if __name__ == "__main__":
    process_chapter(pdf_path, output_dir)

