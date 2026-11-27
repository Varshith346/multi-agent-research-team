"""The multi-agent research team as a LangGraph state machine.

    START -> planner -> researcher -> writer -> critic --approved?--> END
                                        ^                  |
                                        └──── needs work ──┘   (max MAX_REVISIONS loops)

Each agent is just a Python function (a "node") that reads the shared state
and returns the parts of the state it wants to update.
"""
from typing import TypedDict

from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END

from llm import get_llm
from search import web_search

MAX_REVISIONS = 2


# ---------- Shared state: the "whiteboard" every agent reads and writes ----------

class ResearchState(TypedDict, total=False):
    topic: str
    questions: list[str]   # planner's sub-questions
    notes: str             # researcher's findings
    sources: list[str]     # URLs used
    draft: str             # writer's report
    feedback: str          # critic's comments
    score: int             # critic's score (1-10)
    approved: bool
    revisions: int


# ---------- Pydantic schemas for structured hand-offs ----------

class Plan(BaseModel):
    questions: list[str] = Field(description="3-5 focused research questions that together cover the topic")


class Review(BaseModel):
    score: int = Field(description="Quality score from 1 (bad) to 10 (excellent)")
    approved: bool = Field(description="True if the report is accurate, clear and complete enough to publish")
    feedback: str = Field(description="Specific, actionable improvements. Empty if approved.")


# ---------- Agents (nodes) ----------

def planner(state: ResearchState) -> dict:
    """Breaks the topic into research questions."""
    print("🧭 Planner: breaking the topic into questions...")
    plan = get_llm().with_structured_output(Plan).invoke(
        f"You are a research planner. Topic: '{state['topic']}'.\n"
        "Write 3-5 specific questions that a researcher should answer to write a solid report on it."
    )
    for q in plan.questions:
        print(f"   • {q}")
    return {"questions": plan.questions, "revisions": 0}


def researcher(state: ResearchState) -> dict:
    """Searches the web for every question and summarises what it finds."""
    print("🔎 Researcher: searching the web...")
    llm = get_llm()
    notes, sources = [], []
    for q in state["questions"]:
        results = web_search(q)
        sources += [r["url"] for r in results if r["url"]]
        snippets = "\n".join(f"- {r['title']}: {r['snippet']} ({r['url']})" for r in results) or "No results found."
        summary = llm.invoke(
            f"Question: {q}\nSearch results:\n{snippets}\n\n"
            "Summarise the key facts that answer the question in 3-5 bullet points. "
            "Only use the search results; say if they don't answer it."
        ).content
        notes.append(f"### {q}\n{summary}")
        print(f"   ✓ {q}")
    return {"notes": "\n\n".join(notes), "sources": list(dict.fromkeys(sources))}


def writer(state: ResearchState) -> dict:
    """Writes (or rewrites) the report from the notes and any critic feedback."""
    revision = state.get("revisions", 0)
    print(f"✍️  Writer: {'writing' if revision == 0 else f'revising (round {revision})'} the report...")
    feedback = ""
    if state.get("feedback"):
        feedback = f"\n\nYour previous draft:\n{state['draft']}\n\nEditor feedback to fix:\n{state['feedback']}"
    draft = get_llm(temperature=0.4).invoke(
        f"You are a technical writer. Write a clear markdown report on '{state['topic']}' "
        "for a student audience, with a title, short intro, sections with headings, and a conclusion. "
        "Use ONLY these research notes:\n\n"
        f"{state['notes']}{feedback}"
    ).content
    return {"draft": draft, "revisions": revision + 1}


def critic(state: ResearchState) -> dict:
    """Reviews the draft like a strict editor."""
    print("🧐 Critic: reviewing the draft...")
    review = get_llm().with_structured_output(Review).invoke(
        "You are a strict editor. Review this report against the research notes. "
        "Check accuracy (no claims beyond the notes), structure, clarity and completeness. "
        "Approve only if the score is 8 or higher.\n\n"
        f"NOTES:\n{state['notes']}\n\nREPORT:\n{state['draft']}"
    )
    approved = review.approved and review.score >= 8
    print(f"   score {review.score}/10 → {'approved ✅' if approved else 'needs work 🔁'}")
    return {"score": review.score, "approved": approved, "feedback": review.feedback}


# ---------- Routing: the conditional edge that makes the loop ----------

def after_critic(state: ResearchState) -> str:
    if state["approved"] or state["revisions"] > MAX_REVISIONS:
        return "done"
    return "revise"


def build_graph():
    g = StateGraph(ResearchState)
    g.add_node("planner", planner)
    g.add_node("researcher", researcher)
    g.add_node("writer", writer)
    g.add_node("critic", critic)

    g.add_edge(START, "planner")
    g.add_edge("planner", "researcher")
    g.add_edge("researcher", "writer")
    g.add_edge("writer", "critic")
    g.add_conditional_edges("critic", after_critic, {"revise": "writer", "done": END})
    return g.compile()
