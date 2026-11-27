"""Usage: python main.py "your topic""""
import os
import re
import sys

from agents import build_graph


def main():
    topic = " ".join(sys.argv[1:]) or input("Research topic: ").strip()
    if not topic:
        print("Please give a topic.")
        return

    graph = build_graph()
    result = graph.invoke({"topic": topic})

    report = result["draft"]
    if result.get("sources"):
        report += "\n\n## Sources\n" + "\n".join(f"- {u}" for u in result["sources"])

    os.makedirs("reports", exist_ok=True)
    slug = re.sub(r"[^a-z0-9]+", "-", topic.lower()).strip("-")[:50] or "report"
    path = os.path.join("reports", f"{slug}.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(report)

    print("\n" + "=" * 60)
    print(report)
    print("=" * 60)
    print(f"Final score: {result.get('score')}/10 after {result.get('revisions')} draft(s)")
    print(f"Saved to {path}")


if __name__ == "__main__":
    main()
