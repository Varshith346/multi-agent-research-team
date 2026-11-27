"""Prints the graph as a Mermaid diagram. Paste the output into https://mermaid.live
to see a picture of your agent workflow (great for your README / LinkedIn post)."""
from agents import build_graph

print(build_graph().get_graph().draw_mermaid())
