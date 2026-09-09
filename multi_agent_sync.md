1. Hierarchy of Directives
You are operating in a multi-agent environment. Your primary project rules are located in the agents.md file (which you must always respect). THIS current file contains your strict operational boundaries to prevent git merge conflicts and repository corruption.

2. Multi-Agent Context Awareness
You are NOT the only AI working on this repository. Other agents (e.g., Claude Code, Gemini Pro, Cursor) are working simultaneously on different branches with other human developers.

NEVER assume you have sole control over the global architecture.

NEVER rewrite a file just to "clean it up" or "improve readability" unless explicitly requested. Other agents might rely on the exact current structure.

3. Strict Compartmentalization (Zero Merge Conflict Policy)
File Isolation: Only read, write, or modify the specific files the human assigns to you for your current feature. Do not touch app.py or main.py if you are assigned to a side module (e.g., data_utils.py), unless you are specifically doing the final integration.

Surgical Edits: When modifying a file, only change or append the exact function needed. Do not reformat the entire file, do not change global variables, and do not re-sort imports automatically.

Pure Functions: Build your logic as decoupled, pure functions so they can be safely imported across branches by the Human Integrator.

4. Dependency Management Protocol
DO NOT modify requirements.txt or pyproject.toml automatically.

If the code you are writing requires a new Python package, write the code normally but IMMEDIATELY output a warning to the human user in the chat: "WARNING: I used [Library Name]. Please notify the Integrator to add it to requirements.txt". This prevents dependency mismatches between branches.

5. Acknowledgment
Before executing the first prompt in this branch, acknowledge these boundaries by stating: "Multi-Agent Protocol active. I will strictly compartmentalize my edits and respect agents.md. Ready for my assigned module."
