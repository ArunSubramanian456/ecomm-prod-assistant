import importlib.metadata
packages = [
    "langchain",
    "langchain_core",
    "python-dotenv",
    "streamlit",
    "ipykernel",
    "langgraph"
]
for pkg in packages:
    try:
        version = importlib.metadata.version(pkg)
        print(f"{pkg}=={version}")
    except importlib.metadata.PackageNotFoundError:
        print(f"{pkg} (not installed)")