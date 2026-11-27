"""Print the graph as Mermaid."""
from agents import build_graph

print(build_graph().get_graph().draw_mermaid())
