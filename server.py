import os
from fastmcp import FastMCP
from kaggle.api.kaggle_api_extended import KaggleApi

# Configure KAGGLE_USERNAME and KAGGLE_KEY in Render environment variables.
api = KaggleApi()
api.authenticate()

mcp = FastMCP("kaggle")


@mcp.tool
def search_datasets(query: str) -> list:
    """Search Kaggle datasets and return the top 10 matches."""
    return [{"ref": d.ref, "title": d.title} for d in api.dataset_list(search=query)[:10]]


@mcp.tool
def list_dataset_files(ref: str) -> list:
    """List files in a Kaggle dataset (owner/dataset-slug)."""
    return [f.name for f in api.dataset_list_files(ref).files]


@mcp.tool
def list_competitions(search: str = "") -> list:
    """Search Kaggle competitions and return the top 10 matches."""
    return [{"ref": c.ref, "title": c.title} for c in api.competitions_list(search=search)[:10]]


@mcp.tool
def search_notebooks(query: str) -> list:
    """Search Kaggle notebooks and return the top 10 matches."""
    return [{"ref": k.ref, "title": k.title} for k in api.kernels_list(search=query)[:10]]


SECRET_PATH = os.environ.get("MCP_PATH", "/mcp-change-me-8431")
if not SECRET_PATH.startswith("/"):
    SECRET_PATH = "/" + SECRET_PATH

mcp.run(
    transport="http",
    host="0.0.0.0",
    port=int(os.environ.get("PORT", "10000")),
    path=SECRET_PATH,
)
