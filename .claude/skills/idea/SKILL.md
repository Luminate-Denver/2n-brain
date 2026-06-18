---
name: idea
description: Capture a raw idea, synthesize it into a concise entry, and append it to ideas.md at the repo root. Use when the user runs /idea followed by any thought, concept, feature idea, or note they want to save.
---

# idea

Capture and distill an idea into `ideas.md`.

## How it works

The user invokes `/idea <raw thought>`. Everything after `/idea` is the raw input. You must:

1. **Synthesize** the raw input — keep the user's meaning and intent, but tighten it. Cut filler, fix grammar, make it scannable.
   - Short ideas (≤1 sentence) → leave mostly as-is, just clean up phrasing.
   - Longer ramblings → distill into 1–3 tight bullet points or a 1–2 sentence summary.
   - Preserve concrete details (names, numbers, references) — do not invent anything the user didn't say.
2. **Generate a short title** — 3–7 words that capture the essence. Title Case.
3. **Append** an entry to `/Users/christopherjames/Code/2n/2n-brain/2n-brain/ideas.md` in the following format:

```markdown
## {Title}
*{YYYY-MM-DD}*

{Synthesized body}

---
```

Use the Edit tool to append the new entry before the final state of the file, or use Read + Write to preserve existing content. Do NOT overwrite existing entries.

## Output to user

After writing, respond in ONE line: `Saved: {Title}`. Nothing else.

## Rules

- Never expand, embellish, or add ideas the user didn't state.
- Never ask clarifying questions — just capture what was given.
- If the input is empty, respond `No idea provided.` and do nothing else.
- Use today's date from the session context.
