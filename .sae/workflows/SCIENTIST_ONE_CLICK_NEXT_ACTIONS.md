# Scientist one-click next actions (optional UI convention)

**Status:** interface implementation guidance for the binding GPT Native Next Action Contract in `AGENTS.md` and the [Next-Action Completion Gate](NEXT_ACTION.md). This is a UI convenience, **not** a new agent, scientific approval gate, orchestrator, tool entitlement, or change to standing authorization.

## Goal
After each completed GPT Architect/Mentor cycle, help the Scientist continue work in the **same ChatGPT conversation** by clicking an available next-action choice instead of copying an instruction. Keep existing GitHub Issue/PR handoff for Codex.

## ChatGPT final-response contract (when the client supports interactions)
- Complete the task first: state the factual outcome, evidence links, source SHA and limitations. **Never make the scientific decision depend on pressing a button.**
- Where there are useful distinct next actions, add a small **SAE · Next Action** section with **one to three concise, clickable choices**. The first should be the recommended next logical bounded task. Typical options: **Continue architect work** (inspect/accept/dispatch the next real task), **Read-only progress check**, and **Review/replan**. Avoid three choices when only one sensible action exists.
- Each clickable choice submits a **complete, self-contained, explicit instruction** into the **current ChatGPT conversation**. Capture the target repository, Issue/PR, exact relevant SHA and safety/scope boundaries when necessary. Use an available client-native interaction action; never invent an executable Markdown link or pretend repository Markdown renders ChatGPT controls.
- If interactive actions are unavailable, offer short numbered choices that the Scientist can answer with a number; provide full copyable commands only on request. A copy button is useful but **does not count as one-click continuation**. Do not force the user to select from a form or copy boilerplate where an actual click is available.
- **In Codex:** provide similarly short next-step suggestions only if its *actual client* supports native in-window submission. No assumption that ChatGPT buttons can click Codex or transfer commands between windows. Otherwise use Codex-native prompt conventions or the existing explicit GitHub Issue handoff.
- The Scientist remains free to type another instruction or stop; suggestions do not schedule background work, authorize new billing or trigger a cross-window automation.

## Interaction safety and scientific gates
- A click is a **new bounded user-invoked turn**, not blanket approval of future work.
- GPT's existing delegated authority for eligible PR reviews/merges remains unchanged; Codex cannot self-merge. New spending, publication of sensitive data or other separately gated actions retain their existing rules.
- Present actual OPEN/READY/PASS/BLOCKED state honestly. Do not offer `merge PR` for a merged PR, and do not silently invent a current SHA. If live GitHub state is not checked, use an appropriately conditional next-step request.
- Where multiple existing Issues cover the same experiment, prefer one canonical target; a click should not spawn duplicate allocations. Exact source, scientific oracle, session cleanup and evidence still govern compute.

## Example (conceptual text; actual UI is supplied by the ChatGPT client, not GitHub)
- **A · Continue:** `推进架构师工作：核查当前 SAE 项目 GitHub 状态，在已授权范围内推进下一项合格科研任务；如需派单，提供固定 SHA、Issue 和验收边界。`
- **B · Progress:** `推进架构师工作：只读检查 SAE-Framework 和正在研究的算法项目，报告当前 PR/Issue、已验证证据、阻塞项，不修改仓库。`
- **C · Replan:** `推进导师工作：根据已有科学证据评估下一研究方向，先分析数值/计算价值，不启动实验。`

## Verification
This feature is **documentation for response UX**, not a GitHub-site button implementation. Success is observed when a user clicks a native control in an eligible ChatGPT response and a new turn is submitted in that **same** conversation. Codex interoperability is **not verified**. No MCP server, desktop automation, daemon, GitHub Action, subscription or tool code is required.
