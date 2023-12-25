import argparse
from pathlib import Path


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("pyproject")
    args = parser.parse_args(argv)
    pyproject = Path(args.pyproject)
    with open(pyproject.parent / "somenewfile-sdist.txt", "w") as out:
        out.write("some content sdist")


if __name__ == "__main__":
    main()
