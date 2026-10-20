import sys

from .cli import ExpenseMateCLI, ExpenseMateGUI


if __name__ == "__main__":
    app = None

    if "--cli" not in sys.argv:
        try:
            app = ExpenseMateGUI()
        except RuntimeError as exc:
            print(f"GUI not available ({exc}). Starting console mode.")

    if app is None:
        app = ExpenseMateCLI()

    app.run()