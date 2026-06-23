import sys
import os

from app import run_app


def main():
    demo_file = ""
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if os.path.isfile(arg) and arg.lower().endswith(".dem"):
            demo_file = os.path.abspath(arg)

    sys.exit(run_app(demo_file))


if __name__ == "__main__":
    main()
