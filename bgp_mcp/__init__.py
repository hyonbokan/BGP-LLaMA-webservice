"""Thin MCP server exposing BGP update data via pybgpstream.

Launched by the agent pod as a local stdio MCP server (declared in AGENT_MCP_SERVERS).
It fetches BGP updates from public collectors and returns plain records; the agent does
the analysis. This isolates the pybgpstream dependency to one tested process and keeps
LLM-generated code from having to speak pybgpstream directly.
"""
