# Final Schema Reference – Indian Polity MCQ Dataset

## Uniform JSON Schema
Every question (regardless of type) must follow:

```
{
  "chapter_id": <int>,
  "chapter_title": "<string>",
  "qnum": <int>,
  "type": "mcq_single | match | statements_correctness | assertion_reason",
  "input": "<stem + context>",
  "options": { "A": "...", "B": "...", "C": "...", "D": "..." },
  "choices": ["A","B","C","D"],
  "answer": "<A|B|C|D>",
  "explanation": "<string or empty>",
  "metadata": { "schema": "mcq_uniform_v1", "extra": { ...type-specific... } }
}
```

5 core fields are mandatory for model training:
- `inputs`
- `options`
- `choices`
- `answer`
- `explanation`

Everything else is auxiliary for parsing or analysis.

## Question Types

### 1) Standard MCQ (single-correct) → `"type": "mcq_single"`

```
{
  "chapter_id": 1,
  "chapter_title": "Constitutional Provisions",
  "qnum": 1,
  "type": "mcq_single",
  "input": "Who was the chairman of the drafting committee of the Constituent Assembly?",
  "options": {
    "A": "J.L. Nehru",
    "B": "Sardar Vallabhbhai Patel",
    "C": "B.R. Ambedkar",
    "D": "K.M. Munshi"
  },
  "choices": ["A","B","C","D"],
  "answer": "C",
  "explanation": "B.R. Ambedkar chaired the Drafting Committee.",
  "metadata": { "schema": "mcq_uniform_v1" }
}
```

### 2) Match-the-Following → `"type": "match"`

```
{
  "chapter_id": 1,
  "chapter_title": "Constitutional Provisions",
  "qnum": 19,
  "type": "match",
  "input": "Match List-I with List-II and select the correct answer using the codes given below.\n\nList-I (P–S):\nP. First Vice-President of Constituent Assembly\nQ. Originally the only Congress Member of Draft Committee\nR. Member of Constituent Assembly representing Rajasthan’s Princely States\nS. Chairman of Union Constitution Committee\n\nList-II (1–4):\n1. V.T. Krishnamachari\n2. Jawaharlal Nehru\n3. K.M. Munshi\n4. H.C. Mukherjee",
  "options": {
    "A": "P-1, Q-4, R-2, S-3",
    "B": "P-4, Q-3, R-1, S-2",
    "C": "P-1, Q-2, R-3, S-4",
    "D": "P-3, Q-4, R-1, S-2"
  },
  "choices": ["A","B","C","D"],
  "answer": "B",
  "explanation": "…from key…",
  "metadata": {
    "schema": "mcq_uniform_v1",
    "extra": {
      "left_labels": ["P","Q","R","S"],
      "right_labels": ["1","2","3","4"]
    }
  }
}
```

### 3) Statement correctness (identify correct/incorrect) → `"type": "statements_correctness"`

```
{
  "chapter_id": 1,
  "chapter_title": "Constitutional Provisions",
  "qnum": 51,
  "type": "statements_correctness",
  "input": "Which of the following federal principles are not found in Indian federation?\n\nStatements (P–S):\nP. Bifurcation of the judiciary between the Federal and State Governments\nQ. Equality of representation of the states in the upper house of the Federal Legislature\nR. The Union cannot be destroyed by any state seceding from the Union at its will\nS. Federal Government can redraw the map of the Indian Union by forming new States",
  "options": {
    "A": "P, Q and R",
    "B": "Q, R and S",
    "C": "P and Q",
    "D": "R and S"
  },
  "choices": ["A","B","C","D"],
  "answer": "B",
  "explanation": "…from key…",
  "metadata": {
    "schema": "mcq_uniform_v1",
    "extra": {
      "statement_mode": "identify_incorrect",
      "original_statement_labels": ["1","2","3","4"],
      "normalized_labels": ["P","Q","R","S"]
    }
  }
}
```

### 4) Assertion–Reason → `"type": "assertion_reason"`

```
{
  "chapter_id": 1,
  "chapter_title": "Constitutional Provisions",
  "qnum": 29,
  "type": "assertion_reason",
  "input": "Assertion (Q): The Constitution of India has become the longest one.\nReason (R): The Chapter on Fundamental Rights has been borrowed from the model of American Constitution.\nChoose the correct answer using the code given below:",
  "options": {
    "A": "Both (Q) and (R) are correct and (R) is the correct explanation of (Q)",
    "B": "Both (Q) and (R) are correct, but (R) is not the correct explanation of (Q)",
    "C": "(Q) is true, but (R) is false",
    "D": "(Q) is false, but (R) is true"
  },
  "choices": ["A","B","C","D"],
  "answer": "A",
  "explanation": "…from key…",
  "metadata": {
    "schema": "mcq_uniform_v1",
    "extra": { "assertion_label": "Q", "reason_label": "R" }
  }
}
```