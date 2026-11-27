# 🧠 LEARN: Multi-Agent Research Team, explained simply

---

## 1. What is an "agent"?
An **agent** is an LLM that does a job inside a bigger program: it can decide things, use tools (like web search), and pass work to others.
A **multi-agent system** splits a big task among specialised agents, like a real team. Each one has a small, clear job, so each prompt is simpler and the results are better.

## 2. Why LangGraph?
A normal LangChain chain goes in a **straight line** (A → B → C).
Real workflows need **loops and decisions** ("if the report is bad, rewrite it").
**LangGraph** lets you build the workflow as a **graph**:

| LangGraph word | Meaning | In this project |
|---|---|---|
| **State** | Shared data every node can read/update (a whiteboard) | `ResearchState` (topic, questions, notes, draft, score...) |
| **Node** | A step, i.e. a Python function `state -> updates` | `planner`, `researcher`, `writer`, `critic` |
| **Edge** | "after this node, go to that node" | `planner → researcher` |
| **Conditional edge** | A function decides where to go next | `after_critic` → `"revise"` or `"done"` |
| **compile()** | Turns the graph into a runnable app | `build_graph()` |

## 3. Walk through one run
1. `graph.invoke({"topic": "..."})` puts the topic in the state.
2. **planner** asks the LLM for a `Plan` (Pydantic), so we get a clean `list[str]` of questions.
3. **researcher** loops over the questions → `web_search()` → LLM summarises each into notes, and saves URLs as sources.
4. **writer** writes a markdown report using *only* the notes.
5. **critic** returns a `Review(score, approved, feedback)`.
6. `after_critic()` checks: approved or too many revisions? → **END**. Otherwise → back to **writer**, which now also gets the feedback.

Each node returns **only the keys it changes**. LangGraph merges them into the state.

## 4. Why Pydantic between agents?
Agents talk to each other. If the planner returned messy text, the researcher would break.
`with_structured_output(Plan)` guarantees a list of questions, and `Review` guarantees a number score and a true/false approval, so the routing code can trust them.

## 5. Safety: avoiding infinite loops
An LLM critic might never be satisfied. `MAX_REVISIONS` caps the loop. Always put a limit on agent loops; this is a common interview point.

## 6. Graceful failure
`web_search()` catches errors and returns `[]`, so one failed search doesn't crash the whole team.

---

## 🎤 Interview questions: practise these out loud

1. **Explain your project in 30 seconds.**
   *"It's a multi-agent system built with LangGraph. A planner agent splits a topic into research questions, a researcher searches the web and summarises findings, a writer drafts a report, and a critic scores it. If the score is below 8, a conditional edge sends it back to the writer with feedback, up to two revisions. Agents hand off structured data using Pydantic schemas, and the LLM provider is configurable."*

2. **LangChain vs LangGraph?** LangChain gives the building blocks (models, prompts, tools) and linear chains. LangGraph adds stateful graphs with cycles, branching, persistence and human-in-the-loop, which you need for agents.

3. **What is state in LangGraph?** A typed dict shared across nodes; each node returns partial updates that get merged.

4. **How does the loop work?** `add_conditional_edges("critic", after_critic, {...})`: after the critic runs, `after_critic` returns `"revise"` or `"done"`, mapped to the writer node or END.

5. **How do you stop infinite loops?** A revision counter in state plus a max limit (LangGraph also has a `recursion_limit`).

6. **Why multiple agents instead of one big prompt?** Smaller focused prompts are more reliable, easier to debug and test, can use different models per role, and the critic adds self-correction ("reflection" pattern).

7. **What is the "reflection" / "evaluator-optimizer" pattern?** One LLM generates, another evaluates and gives feedback, loop until good. That's exactly writer ↔ critic.

8. **How would you improve it?** Run research questions **in parallel** (LangGraph `Send` API), add a fact-checker agent, use a better search API (Tavily), add human approval before publishing, cache searches.

## ✅ Exercises
- [ ] Run `python draw_graph.py`, paste the output into mermaid.live, and screenshot it for LinkedIn.
- [ ] Change the critic's pass mark from 8 to 9. Do you get more revisions?
- [ ] Add a 5th agent, **"fact_checker"**, between writer and critic.
- [ ] Make the planner create exactly 3 questions and compare report quality.
