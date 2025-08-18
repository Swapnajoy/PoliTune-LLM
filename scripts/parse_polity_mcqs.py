import os
import re
import json
import pdfplumber

chapter_dir = "assets/chapters/"
solution_dir = "assets/solutions/"
output_dir = "data/train/"

os.makedirs(output_dir, exist_ok=True)

def extract_lines(pdf_path):
    lines = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            for line in text.splitlines():
                line = line.strip()
                if not line or line.lower().startswith("join telegram"):
                    continue
                line = re.sub(r'\[[^\]]*\]', '', line).strip()
                if line:
                    lines.append(line)

    return lines

def extract_chapter_id_title(filename):
    basename = filename.replace(".pdf", "")
    parts = basename.split("_")
    chapter_id = int(parts[1])
    chapter_title = " ".join(parts[2:]).replace("-", " ").strip()
    return chapter_id, chapter_title

def split_into_qna_blocks(q_lines, a_lines):
    qblocks = {}
    ablocks = {}

    qnum = 1
    qblock = []
    ablock = []
    q_started = False
    a_started = False

    for line in q_lines:
        match = re.match(rf'^{qnum}\.\s*(.*)', line)
        if match:
            if q_started:
                qblocks[qnum] = qblock
                qnum += 1
                qblock = []
            q_started = True
            qblock.append(match.group(1).strip())
        elif q_started:
            next_q_match = re.match(rf'^{qnum + 1}\.\s*(.*)', line)
            if next_q_match:
                qblocks[qnum] = qblock
                qnum += 1
                qblock = [next_q_match.group(1).strip()]
            else:
                qblock.append(line.strip())
    if qblock:
        qblocks[qnum] = qblock

    qnum = 1
    ablock = []
    a_started = False
    for line in a_lines:
        match = re.match(rf'^{qnum}\.\s*(.*)', line)
        if match:
            if a_started:
                ablocks[qnum] = ablock
                qnum += 1
                ablock = []
            a_started = True
            ablock.append(match.group(1).strip())
        elif a_started:
            next_q_match = re.match(rf'^{qnum + 1}\.\s*(.*)', line)
            if next_q_match:
                ablocks[qnum] = ablock
                qnum += 1
                ablock = [next_q_match.group(1).strip()]
            else:
                ablock.append(line.strip())
    if ablock:
        ablocks[qnum] = ablock

    return qblocks, ablocks

def detect_question_type(block_lines):
    joined = " ".join(block_lines).lower()
    if "match " in joined:
        return "match"
    elif "assertion" in joined and "reason" in joined:
        return "assertion_reason"
    elif any(re.match(r'^\s*\d[\.\)]', ln) for ln in block_lines):
        return "statements_correctness"
    else:
        return "mcq_single"

def extract_input_options_answer_explanation(qblock, ablock, qtype):
    input_lines = []
    options = {}
    current_opt = None

    # For relabeling statements
    statement_map = {
        "1": "P", "2": "Q", "3": "R", "4": "S", "5": "T", "6": "U", "7": "V", "8": "W"
    }

    # Clean question block
    for i, line in enumerate(qblock):
        line = line.strip()

        if qtype == "assertion_reason":
            if "assertion" in line.lower():
                line = re.sub(r'\(\s*[aA]\s*\)', '(Q)', line)

        if qtype == "statements_correctness":
            stmt_match = re.match(r'^(\d)[\.\)]\s*(.+)', line)
            if stmt_match:
                num = stmt_match.group(1)
                rest = stmt_match.group(2)
                if num in statement_map:
                    line = f"{statement_map[num]}. {rest}"

        qblock[i] = line

    for line in qblock:
        opt_match = re.match(r'^\(([a-d])\)\s*(.*)', line)
        if opt_match:
            current_opt = opt_match.group(1).upper()
            options[current_opt] = opt_match.group(2).strip()
        elif current_opt:
            options[current_opt] += " " + line.strip()
        else:
            input_lines.append(line.strip())

    if qtype == "statements_correctness":
        for key in options:
            text = options[key]
            for num, label in statement_map.items():
                text = re.sub(rf'\b{num}\b', label, text)
            options[key] = text.strip()

    if qtype == "assertion_reason":
        for key in options:
            options[key] = re.sub(r'\bA\b', 'Q', options[key])

    input_text = " ".join(input_lines).strip()

    # Process answer block
    answer = ""
    explanation_lines = []
    if ablock:
        amatch = re.match(r'^\(?([a-dA-D])\)?\s*(.*)', ablock[0])
        if amatch:
            answer = amatch.group(1).upper()
            explanation_lines.append(amatch.group(2).strip())
        for line in ablock[1:]:
            explanation_lines.append(line.strip())

    explanation = " ".join(explanation_lines).strip()

    return input_text, options, answer, explanation

def make_filename(chapter_id, qnum):
    return f"{chapter_id:03d}_{qnum:03d}.json"

def process_chapter(chapter_dir, solution_dir):
    for filename in sorted(os.listdir(chapter_dir)):
        if not filename.endswith(".pdf"):
            continue

        chapter_path = os.path.join(chapter_dir, filename)
        chapter_id, chapter_title = extract_chapter_id_title(filename)

        solution_file = f"solution_{chapter_id:03d}.pdf"
        solution_path = os.path.join(solution_dir, solution_file)
        if not os.path.exists(solution_path):
            print(f"Solution file not found: {solution_path}")
            continue

        q_lines = extract_lines(chapter_path)
        a_lines = extract_lines(solution_path)

        qblocks, ablocks = split_into_qna_blocks(q_lines, a_lines)

        skipped_qnums = []

        for qnum in qblocks:
            qblock = qblocks[qnum]
            qtype = detect_question_type(qblock)

            # Skip match type questions
            if qtype == "match":
                skipped_qnums.append(qnum)
                continue

            ablock = ablocks.get(qnum, [])
            input_text, options, answer, explanation = extract_input_options_answer_explanation(qblock, ablock, qtype)

            qjson = {
                "chapter_id": chapter_id,
                "chapter_title": chapter_title,
                "qnum": qnum,
                "type": qtype,
                "input": input_text,
                "options": options,
                "choices": list(options.keys()),
                "answer": answer,
                "explanation": explanation
            }

            out_path = os.path.join(output_dir, make_filename(chapter_id, qnum))
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(qjson, f, indent=2, ensure_ascii=False)

        print(f"Extracted {len(qblocks) - len(skipped_qnums)} questions from {filename}")
        if skipped_qnums:
            print(f"Skipped match-type questions: {skipped_qnums} from {filename}")

if __name__ == "__main__":
    process_chapter(chapter_dir, solution_dir)