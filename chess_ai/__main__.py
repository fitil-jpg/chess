from vendors import setup_path  # noqa: F401


def main() -> None:
    """Package entry point used with ``python -m chess_ai``.

    Importing :mod:`vendors.setup_path` ensures vendored third-party
    dependencies are available on ``sys.path`` before other imports occur.
    """
    print("Chess AI package does not define a CLI by default.")


if __name__ == "__main__":
    main()
