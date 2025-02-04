# for sphinx-revealjs
# uvx --from sphinx --with sphinx-revealjs,myst-parser sphinx-build -M revealjs . _build

project = "slide"
copyright = "2025, shimizukawa"
author = "shimizukawa"
release = "2025.02.08"
language = "ja"
root_doc = "slide"

extensions = [
    "myst_parser",
    "sphinx_revealjs",
]
source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}
myst_enable_extensions = ["deflist"]

exclude_patterns = ["assets", ".venv", "_build", "README.md"]

html_theme = "alabaster"
