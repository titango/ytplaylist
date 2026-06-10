"""Main file — backward-compatible wrapper.

Delegates to ``cli.main`` so ``python main.py`` still works after the
CLI code was moved into its own package.
"""
from cli.main import main

if __name__ == "__main__":
    main()
