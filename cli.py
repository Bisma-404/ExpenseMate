from datetime import datetime

try:
    import tkinter as tk
    from tkinter import ttk, messagebox, filedialog
except ImportError:
    tk = None

from .database import DatabaseManager
from .services import ExpenseService
from .analytics import AnalyticsEngine
from .importer_exporter import DataPortabilityManager


class ExpenseMateCLI:
    def __init__(self, db_path: str = "expense_mate.db"):
        self.db = DatabaseManager(db_path)
        self.services = ExpenseService(self.db)
        self.analytics = AnalyticsEngine(self.db)
        self.portability = DataPortabilityManager(self.db)

    def print_header(self, text: str) -> None:
        print("\n" + "=" * 60)
        print(f"   {text}")
        print("=" * 60)

    def show_error(self, message: str) -> None:
        print(f"\n[!] Error: {message}")

    def prompt_float(self, prompt: str) -> float:
        while True:
            try:
                value = input(prompt).strip()
                if not value:
                    raise ValueError("Value cannot be empty.")
                return float(value)
            except ValueError as exc:
                self.show_error(f"Please enter a valid number. {exc}")

    def validate_transaction_data(self, trans_type: str, amount_text: str, category: str, date_str: str) -> float:
        errors = []
        normalized_type = trans_type.strip().lower()

        if normalized_type not in ("income", "expense"):
            errors.append("Transaction type must be 'income' or 'expense'.")

        try:
            amount = float(amount_text)
            if amount <= 0:
                errors.append("Amount must be strictly positive.")
        except (TypeError, ValueError):
            errors.append("Amount must be a valid number.")
            amount = 0.0

        if not category or not category.strip():
            errors.append("Category cannot be empty.")

        try:
            parsed_date = datetime.strptime(date_str, "%Y-%m-%d")
            if parsed_date.strftime("%Y-%m-%d") != date_str:
                raise ValueError
        except ValueError:
            errors.append("Date must follow format YYYY-MM-DD.")

        if errors:
            raise ValueError("; ".join(errors))

        return amount

    def validate_currency_data(self, amount_text: str, from_curr: str, to_curr: str) -> float:
        errors = []

        try:
            amount = float(amount_text)
            if amount < 0:
                errors.append("Amount cannot be negative.")
        except (TypeError, ValueError):
            errors.append("Amount must be a valid number.")
            amount = 0.0

        if not from_curr or not from_curr.strip():
            errors.append("From currency cannot be empty.")

        if not to_curr or not to_curr.strip():
            errors.append("To currency cannot be empty.")

        if errors:
            raise ValueError("; ".join(errors))

        return amount

    def run(self) -> None:
        while True:
            try:
                self.print_header("EXPENSEMATE - PERSONAL EXPENSE MANAGER")
                print(" 1. Add Transaction (Income / Expense)")
                print(" 2. View All Transactions")
                print(" 3. View Financial Summary & Net Balance")
                print(" 4. Manage Monthly Budgets & View Alerts")
                print(" 5. Visual Analytics & Category Breakdown")
                print(" 6. Monthly Spending & Savings Trends")
                print(" 7. Export Transactions to CSV")
                print(" 8. Import Transactions from CSV")
                print(" 9. Multi-Currency Converter")
                print("10. Backup Database")
                print(" 0. Exit")
                print("-" * 60)

                choice = input("Enter option [0-10]: ").strip()

                if choice == "1":
                    try:
                        while True:
                            trans_type = input("Type (income / expense): ").strip().lower()

                            if trans_type in ("income", "expense"):
                                break

                            self.show_error(
                                "Invalid type. Please enter exactly 'income' or 'expense'."
                            )

                        while True:
                            amount_text = input("Amount: ").strip()

                            try:
                                amount = float(amount_text)

                                if amount <= 0:
                                    raise ValueError

                                break

                            except ValueError:
                                self.show_error(
                                    "Invalid amount. Please enter a positive number greater than 0."
                                )

                        while True:
                            category = input(
                                "Category (e.g., Food, Salary, Rent): "
                            ).strip()

                            if category:
                                break

                            self.show_error(
                                "Category cannot be empty. Please enter a category."
                            )

                        while True:
                            date_str = input(
                                f"Date (YYYY-MM-DD, Enter for {datetime.today().strftime('%Y-%m-%d')}): "
                            ).strip()

                            if not date_str:
                                date_str = datetime.today().strftime("%Y-%m-%d")

                            try:
                                parsed_date = datetime.strptime(
                                    date_str, "%Y-%m-%d"
                                )

                                if parsed_date.strftime("%Y-%m-%d") != date_str:
                                    raise ValueError

                                break

                            except ValueError:
                                self.show_error(
                                    "Invalid date format. Please use YYYY-MM-DD."
                                )

                        desc = input("Description: ").strip()

                        tid = self.services.add_transaction(
                            amount,
                            category,
                            trans_type,
                            date_str,
                            desc
                        )

                        print(
                            f"\n[+] Successfully recorded transaction #{tid}!"
                        )

                        if trans_type == "expense":
                            status = self.services.check_budget_status(
                                category,
                                date_str[:7]
                            )

                            if status and status.level in ("WARNING", "CRITICAL"):
                                print(f"\n[ALERT] {status.message}")

                    except Exception as e:
                        self.show_error(e)

                elif choice == "2":
                    try:
                        transactions = self.services.list_transactions()

                        print(
                            f"\n{'ID':<5} | {'Date':<10} | {'Type':<8} | "
                            f"{'Category':<15} | {'Amount':>10} | {'Description'}"
                        )

                        print("-" * 75)

                        for t in transactions:
                            print(
                                f"{t.id:<5} | {t.date:<10} | {t.trans_type:<8} | "
                                f"{t.category:<15} | {t.amount:>10.2f} | "
                                f"{t.description}"
                            )

                    except Exception as e:
                        self.show_error(e)

                elif choice == "3":
                    try:
                        summary = self.services.get_net_summary()

                        print(
                            f"\nTotal Income : {summary['total_income']:>12.2f}"
                        )
                        print(
                            f"Total Expense: {summary['total_expense']:>12.2f}"
                        )
                        print(
                            f"Net Balance  : {summary['net_savings']:>12.2f}"
                        )

                    except Exception as e:
                        self.show_error(e)

                elif choice == "4":
                    try:
                        my = input(
                            f"Month (YYYY-MM, Enter for {datetime.today().strftime('%Y-%m')}): "
                        ).strip()

                        if not my:
                            my = datetime.today().strftime("%Y-%m")

                        try:
                            parsed_month = datetime.strptime(my, "%Y-%m")

                            if parsed_month.strftime("%Y-%m") != my:
                                raise ValueError

                        except ValueError:
                            self.show_error(
                                "Invalid month format. Please use YYYY-MM."
                            )
                            continue

                        statuses = self.services.get_all_budget_statuses(my)

                        if not statuses:
                            print(f"\nNo budgets found for {my}.")

                            add_budget = input(
                                "Add a budget for this month? (y/n): "
                            ).strip().lower()

                            if add_budget == "y":
                                while True:
                                    category = input(
                                        "Budget category: "
                                    ).strip()

                                    if category:
                                        break

                                    self.show_error(
                                        "Category cannot be empty."
                                    )

                                while True:
                                    try:
                                        limit = float(
                                            input("Monthly limit: ").strip()
                                        )

                                        if limit <= 0:
                                            raise ValueError

                                        break

                                    except ValueError:
                                        self.show_error(
                                            "Budget limit must be a positive number."
                                        )

                                self.services.set_budget(
                                    category,
                                    limit,
                                    my
                                )

                                print(
                                    f"\n[+] Budget added for {category} in {my}."
                                )

                                statuses = self.services.get_all_budget_statuses(my)

                        if statuses:
                            for st in statuses:
                                print(
                                    f"[{st.level}] {st.category}: "
                                    f"Spent {st.spent:.2f}/{st.limit:.2f} "
                                    f"({st.percentage:.1f}%)"
                                )

                    except Exception as e:
                        self.show_error(e)

                elif choice == "5":
                    try:
                        month_filter = input(
                            "Month filter (YYYY-MM, press Enter for all): "
                        ).strip()

                        if month_filter:
                            try:
                                parsed_month = datetime.strptime(
                                    month_filter,
                                    "%Y-%m"
                                )

                                if parsed_month.strftime("%Y-%m") != month_filter:
                                    raise ValueError

                            except ValueError:
                                self.show_error(
                                    "Invalid month format. Please use YYYY-MM."
                                )
                                continue

                        breakdown = self.analytics.get_category_breakdown(
                            "expense",
                            month_filter or None
                        )

                        print(
                            self.analytics.generate_ascii_bar_chart(
                                breakdown,
                                title="Expense Category Breakdown"
                            )
                        )

                    except Exception as e:
                        self.show_error(e)

                elif choice == "6":
                    try:
                        trends = self.analytics.get_monthly_trends()

                        print(
                            f"\n{'Month':<10} | {'Income':>10} | "
                            f"{'Expense':>10} | {'Savings':>10}"
                        )

                        print("-" * 50)

                        for my, val in trends.items():
                            print(
                                f"{my:<10} | {val['income']:>10.2f} | "
                                f"{val['expense']:>10.2f} | "
                                f"{val['savings']:>10.2f}"
                            )

                    except Exception as e:
                        self.show_error(e)

                elif choice == "7":
                    try:
                        count = self.portability.export_to_csv(
                            "expenses_export.csv"
                        )

                        print(
                            f"\n[+] Exported {count} transactions "
                            f"to 'expenses_export.csv'."
                        )

                    except Exception as e:
                        self.show_error(e)

                elif choice == "8":
                    try:
                        fn = input("CSV Path: ").strip()

                        if not fn:
                            raise ValueError("CSV path cannot be empty.")

                        s, e, _ = self.portability.import_from_csv(fn)

                        print(
                            f"\n[+] Imported: {s} success, {e} errors."
                        )

                    except Exception as e:
                        self.show_error(e)

                elif choice == "9":
                    try:
                        amount_text = input("Amount: ").strip()
                        f_c = input("From Currency: ").strip().upper()
                        t_c = input("To Currency: ").strip().upper()

                        amt = self.validate_currency_data(
                            amount_text,
                            f_c,
                            t_c
                        )

                        print(
                            f"\n[+] Converted: "
                            f"{self.services.convert_amount(amt, f_c, t_c)}"
                        )

                    except Exception as e:
                        self.show_error(e)

                elif choice == "10":
                    try:
                        backup_path = self.services.create_database_backup()

                        print(
                            f"\n[+] Backup saved to: {backup_path}"
                        )

                    except Exception as e:
                        self.show_error(e)

                elif choice == "0":
                    print("\nGoodbye!\n")
                    break

                else:
                    self.show_error(
                        "Invalid option selected. Please choose from 0 to 10."
                    )

            except KeyboardInterrupt:
                print(
                    "\nProgram interrupted. Exiting gracefully.\n"
                )
                break

            except Exception as e:
                self.show_error(
                    f"Unexpected problem: {e}"
                )


class ExpenseMateGUI(ExpenseMateCLI):
    CURRENCIES = list(ExpenseService.EXCHANGE_RATES.keys())

    COLORS = {
        "bg": "#eef1f6",
        "card": "#ffffff",
        "border": "#dde3ec",
        "header": "#1f3a5f",
        "accent": "#2f6fed",
        "accent_dark": "#1f55c4",
        "text": "#1e2a3a",
        "muted": "#6b7a90",
        "income": "#1e8e5a",
        "expense": "#d64545",
        "warning": "#c98a00",
    }

    BAR_COLORS = [
        "#2f6fed", "#1e8e5a", "#e08a1e", "#8e5bd6",
        "#d64545", "#1aa5b8", "#7a8aa0", "#c2578a",
    ]

    FONT = "Segoe UI"

    def __init__(self, db_path: str = "expense_mate.db"):
        if tk is None:
            raise RuntimeError("Tkinter is not available on this system.")

        super().__init__(db_path)

        try:
            self.root = tk.Tk()
        except tk.TclError as exc:
            raise RuntimeError(f"Unable to open a window: {exc}") from exc

        self.root.title("ExpenseMate - Personal Expense Manager")
        self.root.minsize(860, 580)
        self.root.configure(bg=self.COLORS["bg"])
        self.center_window(980, 680)

        self.status_var = tk.StringVar(value="Ready")
        self.chart_data = {}

        self.setup_styles()
        self.build_header()
        self.build_status_bar()

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=14, pady=(12, 6))

        self.build_add_tab()
        self.build_list_tab()
        self.build_budget_tab()
        self.build_analytics_tab()
        self.build_csv_tab()
        self.build_tools_tab()

        self.notebook.bind("<<NotebookTabChanged>>", lambda event: self.refresh_all())
        self.refresh_all()

    def center_window(self, width: int, height: int) -> None:
        self.root.update_idletasks()
        x = max((self.root.winfo_screenwidth() - width) // 2, 0)
        y = max((self.root.winfo_screenheight() - height) // 3, 0)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def setup_styles(self) -> None:
        c = self.COLORS
        f = self.FONT
        style = ttk.Style(self.root)
        style.theme_use("clam")

        style.configure(".", background=c["card"], foreground=c["text"], font=(f, 10))
        style.configure("TNotebook", background=c["bg"], borderwidth=0)
        style.configure("TNotebook.Tab", padding=(12, 9), font=(f, 10, "bold"),
                        background="#dbe2ee", foreground=c["muted"], borderwidth=0)
        style.map("TNotebook.Tab",
                  background=[("selected", c["card"])],
                  foreground=[("selected", c["accent"])])

        style.configure("Card.TFrame", background=c["card"])
        style.configure("Title.TLabel", font=(f, 14, "bold"), foreground=c["header"])
        style.configure("Muted.TLabel", foreground=c["muted"])
        style.configure("Card.TLabelframe", background=c["card"], bordercolor=c["border"])
        style.configure("Card.TLabelframe.Label", background=c["card"],
                        foreground=c["header"], font=(f, 10, "bold"))

        style.configure("TEntry", padding=6, fieldbackground="white", bordercolor=c["border"])
        style.configure("TCombobox", padding=6, fieldbackground="white")
        style.map("TCombobox", fieldbackground=[("readonly", "white")], selectbackground=[("readonly", "white")], selectforeground=[("readonly", c["text"])])
        style.configure("TRadiobutton", background=c["card"])

        style.configure("Accent.TButton", background=c["accent"], foreground="white",
                        padding=(18, 9), font=(f, 10, "bold"), borderwidth=0)
        style.map("Accent.TButton",
                  background=[("active", c["accent_dark"]), ("pressed", c["accent_dark"])])
        style.configure("Soft.TButton", padding=(14, 8), background="#e6ebf4", borderwidth=0)
        style.map("Soft.TButton", background=[("active", "#d5ddec")])

        style.configure("Treeview", rowheight=28, background="white",
                        fieldbackground="white", borderwidth=0)
        style.configure("Treeview.Heading", background=c["header"], foreground="white",
                        font=(f, 10, "bold"), padding=8, borderwidth=0)
        style.map("Treeview.Heading", background=[("active", c["header"])])
        style.map("Treeview",
                  background=[("selected", "#d6e4ff")],
                  foreground=[("selected", c["text"])])

    def build_header(self) -> None:
        c = self.COLORS
        bar = tk.Frame(self.root, bg=c["header"])
        bar.pack(fill="x")
        tk.Label(bar, text="ExpenseMate", bg=c["header"], fg="white",
                 font=(self.FONT, 19, "bold")).pack(side="left", padx=(22, 10), pady=14)
        tk.Label(bar, text="Personal Expense Manager", bg=c["header"], fg="#b9c7e0",
                 font=(self.FONT, 11)).pack(side="left", pady=(9, 0))

    def build_status_bar(self) -> None:
        c = self.COLORS
        bar = tk.Frame(self.root, bg="#dfe5ef")
        bar.pack(side="bottom", fill="x")
        tk.Label(bar, textvariable=self.status_var, bg="#dfe5ef", fg=c["muted"],
                 anchor="w", padx=16, pady=6, font=(self.FONT, 9)).pack(fill="x")

    def set_status(self, text: str) -> None:
        self.status_var.set(text)

    def new_page(self, title: str):
        frame = ttk.Frame(self.notebook, style="Card.TFrame", padding=22)
        self.notebook.add(frame, text=title)
        return frame

    def form_row(self, parent, row: int, label: str, widget) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=(0, 18), pady=7)
        widget.grid(row=row, column=1, sticky="w", pady=7)

    def is_valid_month(self, text: str) -> bool:
        try:
            return datetime.strptime(text, "%Y-%m").strftime("%Y-%m") == text
        except ValueError:
            return False

    def safe_month(self, text: str, fallback):
        text = text.strip()
        return text if self.is_valid_month(text) else fallback

    def build_add_tab(self) -> None:
        page = self.new_page("Add Transaction")

        self.type_var = tk.StringVar(value="expense")
        self.amount_var = tk.StringVar()
        self.category_var = tk.StringVar()
        self.date_var = tk.StringVar(value=datetime.today().strftime("%Y-%m-%d"))
        self.desc_var = tk.StringVar()

        ttk.Label(page, text="New Transaction", style="Title.TLabel").grid(
            row=0, column=0, columnspan=2, sticky="w")
        ttk.Label(page, text="Record an income or an expense. Press Enter to save.",
                  style="Muted.TLabel").grid(row=1, column=0, columnspan=2, sticky="w", pady=(2, 16))

        kind = ttk.Frame(page, style="Card.TFrame")
        ttk.Radiobutton(kind, text="Income", variable=self.type_var, value="income").pack(
            side="left", padx=(0, 20))
        ttk.Radiobutton(kind, text="Expense", variable=self.type_var, value="expense").pack(side="left")
        self.form_row(page, 2, "Type", kind)

        self.amount_entry = ttk.Entry(page, textvariable=self.amount_var, width=34)
        self.form_row(page, 3, "Amount", self.amount_entry)
        self.form_row(page, 4, "Category", ttk.Entry(page, textvariable=self.category_var, width=34))
        self.form_row(page, 5, "Date (YYYY-MM-DD)", ttk.Entry(page, textvariable=self.date_var, width=34))
        self.form_row(page, 6, "Description", ttk.Entry(page, textvariable=self.desc_var, width=34))

        buttons = ttk.Frame(page, style="Card.TFrame")
        ttk.Button(buttons, text="Add Transaction", style="Accent.TButton",
                   command=self.on_add_transaction).pack(side="left", padx=(0, 10))
        ttk.Button(buttons, text="Clear", style="Soft.TButton",
                   command=self.on_clear_form).pack(side="left")
        buttons.grid(row=7, column=1, sticky="w", pady=(16, 6))

        self.add_msg = ttk.Label(page, text="", foreground=self.COLORS["income"])
        self.add_msg.grid(row=8, column=1, sticky="w", pady=4)

        self.root.bind("<Return>", self.on_enter_key)
        self.amount_entry.focus_set()

    def on_enter_key(self, event=None) -> None:
        if self.notebook.index(self.notebook.select()) == 0:
            self.on_add_transaction()

    def on_clear_form(self) -> None:
        self.amount_var.set("")
        self.category_var.set("")
        self.desc_var.set("")
        self.add_msg.config(text="")
        self.amount_entry.focus_set()

    def on_add_transaction(self) -> None:
        trans_type = self.type_var.get().strip().lower()
        category = self.category_var.get().strip()
        date_str = self.date_var.get().strip()

        try:
            amount = self.validate_transaction_data(
                trans_type, self.amount_var.get().strip(), category, date_str)
            tid = self.services.add_transaction(
                amount, category, trans_type, date_str, self.desc_var.get().strip())
        except Exception as exc:
            messagebox.showerror("Could not save", str(exc))
            return

        self.add_msg.config(text=f"Saved transaction #{tid}.")
        self.set_status(f"Recorded {trans_type} of {amount:,.2f} in {category}.")
        self.amount_var.set("")
        self.category_var.set("")
        self.desc_var.set("")
        self.amount_entry.focus_set()

        if trans_type == "expense":
            status = self.services.check_budget_status(category, date_str[:7])
            if status and status.level in ("WARNING", "CRITICAL"):
                messagebox.showwarning("Budget Alert", status.message)

        self.refresh_all()

    def build_list_tab(self) -> None:
        page = self.new_page("Transactions")

        top = ttk.Frame(page, style="Card.TFrame")
        top.pack(fill="x", pady=(0, 12))

        self.filter_type = tk.StringVar(value="all")
        self.filter_cat = tk.StringVar()

        ttk.Label(top, text="Type").pack(side="left")
        ttk.Combobox(top, textvariable=self.filter_type, values=["all", "income", "expense"],
                     state="readonly", width=10).pack(side="left", padx=(6, 16))
        ttk.Label(top, text="Category").pack(side="left")
        ttk.Entry(top, textvariable=self.filter_cat, width=18).pack(side="left", padx=(6, 14))
        ttk.Button(top, text="Apply Filter", style="Accent.TButton",
                   command=self.refresh_list).pack(side="left")
        self.count_label = ttk.Label(top, text="", style="Muted.TLabel")
        self.count_label.pack(side="right")

        body = ttk.Frame(page, style="Card.TFrame")
        body.pack(fill="both", expand=True)

        columns = ("ID", "Date", "Type", "Category", "Amount", "Description")
        widths = (50, 100, 90, 150, 120, 340)
        self.tree = ttk.Treeview(body, columns=columns, show="headings")
        for name, width in zip(columns, widths):
            self.tree.heading(name, text=name, anchor="e" if name == "Amount" else "w")
            self.tree.column(name, width=width, anchor="e" if name == "Amount" else "w")

        self.tree.tag_configure("income", foreground=self.COLORS["income"])
        self.tree.tag_configure("expense", foreground=self.COLORS["expense"])

        scroll = ttk.Scrollbar(body, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

    def refresh_list(self) -> None:
        chosen = self.filter_type.get()
        rows = self.services.list_transactions(
            None if chosen == "all" else chosen,
            self.filter_cat.get().strip() or None)

        self.tree.delete(*self.tree.get_children())
        for t in rows:
            sign = "+" if t.trans_type == "income" else "-"
            self.tree.insert("", "end", tags=(t.trans_type,), values=(
                t.id, t.date, t.trans_type.capitalize(), t.category,
                f"{sign}{t.amount:,.2f}", t.description))

        self.count_label.config(text=f"{len(rows)} transactions")

    def make_card(self, parent, title: str, color: str, column: int):
        c = self.COLORS
        card = tk.Frame(parent, bg=c["card"], highlightthickness=1, highlightbackground=c["border"])
        card.grid(row=0, column=column, sticky="ew", padx=6)
        parent.columnconfigure(column, weight=1)
        tk.Frame(card, bg=color, height=4).pack(fill="x")
        tk.Label(card, text=title, bg=c["card"], fg=c["muted"],
                 font=(self.FONT, 10)).pack(anchor="w", padx=18, pady=(12, 0))
        value = tk.Label(card, text="0.00", bg=c["card"], fg=color, font=(self.FONT, 21, "bold"))
        value.pack(anchor="w", padx=18, pady=(2, 14))
        return value

    def build_budget_tab(self) -> None:
        c = self.COLORS
        page = self.new_page("Dashboard")

        cards = ttk.Frame(page, style="Card.TFrame")
        cards.pack(fill="x", pady=(0, 18))
        self.income_label = self.make_card(cards, "Total Income", c["income"], 0)
        self.expense_label = self.make_card(cards, "Total Expense", c["expense"], 1)
        self.net_label = self.make_card(cards, "Net Balance", c["accent"], 2)

        form = ttk.LabelFrame(page, text="Set a monthly budget", style="Card.TLabelframe", padding=12)
        form.pack(fill="x", pady=(0, 14))

        self.budget_cat = tk.StringVar()
        self.budget_limit = tk.StringVar()
        self.budget_month = tk.StringVar(value=datetime.today().strftime("%Y-%m"))

        ttk.Label(form, text="Category").pack(side="left")
        ttk.Entry(form, textvariable=self.budget_cat, width=13).pack(side="left", padx=(6, 14))
        ttk.Label(form, text="Limit").pack(side="left")
        ttk.Entry(form, textvariable=self.budget_limit, width=10).pack(side="left", padx=(6, 14))
        ttk.Label(form, text="Month (YYYY-MM)").pack(side="left")
        month_entry = ttk.Entry(form, textvariable=self.budget_month, width=10)
        month_entry.pack(side="left", padx=(6, 14))
        month_entry.bind("<Return>", lambda event: self.on_show_budgets())
        ttk.Button(form, text="Set Budget", style="Accent.TButton",
                   command=self.on_set_budget).pack(side="left")

        columns = ("Category", "Spent", "Limit", "Used", "Status")
        self.budget_tree = ttk.Treeview(page, columns=columns, show="headings")
        for name in columns:
            self.budget_tree.heading(name, text=name, anchor="w")
            self.budget_tree.column(name, width=140, anchor="w")
        self.budget_tree.tag_configure("NORMAL", foreground=c["income"])
        self.budget_tree.tag_configure("WARNING", foreground=c["warning"])
        self.budget_tree.tag_configure("CRITICAL", foreground=c["expense"])
        self.budget_tree.pack(fill="both", expand=True)

    def on_set_budget(self) -> None:
        month = self.budget_month.get().strip()

        try:
            if not self.is_valid_month(month):
                raise ValueError("Month must follow format YYYY-MM.")
            limit = float(self.budget_limit.get().strip())
            category = self.budget_cat.get().strip()
            self.services.set_budget(category, limit, month)
        except Exception as exc:
            messagebox.showerror("Could not save budget", str(exc))
            return

        self.set_status(f"Budget of {limit:,.2f} set for {category} in {month}.")
        self.budget_cat.set("")
        self.budget_limit.set("")
        self.refresh_budgets()

    def on_show_budgets(self) -> None:
        if not self.is_valid_month(self.budget_month.get().strip()):
            messagebox.showerror("Error", "Month must follow format YYYY-MM.")
            return
        self.refresh_budgets()

    def refresh_budgets(self) -> None:
        summary = self.services.get_net_summary()
        net = summary["net_savings"]
        self.income_label.config(text=f"{summary['total_income']:,.2f}")
        self.expense_label.config(text=f"{summary['total_expense']:,.2f}")
        self.net_label.config(
            text=f"{net:,.2f}",
            fg=self.COLORS["accent"] if net >= 0 else self.COLORS["expense"])

        month = self.safe_month(self.budget_month.get(), datetime.today().strftime("%Y-%m"))

        self.budget_tree.delete(*self.budget_tree.get_children())
        for st in self.services.get_all_budget_statuses(month):
            self.budget_tree.insert("", "end", tags=(st.level,), values=(
                st.category, f"{st.spent:,.2f}", f"{st.limit:,.2f}",
                f"{st.percentage:.1f}%", st.level))

    def build_analytics_tab(self) -> None:
        c = self.COLORS
        page = self.new_page("Analytics")

        top = ttk.Frame(page, style="Card.TFrame")
        top.pack(fill="x", pady=(0, 10))

        self.analytics_month = tk.StringVar()

        ttk.Label(top, text="Expenses by category", style="Title.TLabel").pack(side="left")
        ttk.Button(top, text="Show Charts", style="Accent.TButton",
                   command=self.on_show_analytics).pack(side="right")
        ttk.Entry(top, textvariable=self.analytics_month, width=10).pack(side="right", padx=(6, 12))
        ttk.Label(top, text="Month (YYYY-MM, blank for all)", style="Muted.TLabel").pack(side="right")

        self.canvas = tk.Canvas(page, height=282, bg="white", highlightthickness=1,
                                highlightbackground=c["border"])
        self.canvas.pack(fill="x", pady=(0, 14))
        self.canvas.bind("<Configure>", lambda event: self.draw_chart())

        ttk.Label(page, text="Monthly trends", style="Title.TLabel").pack(anchor="w", pady=(0, 6))

        columns = ("Month", "Income", "Expense", "Savings")
        self.trend_tree = ttk.Treeview(page, columns=columns, show="headings", height=6)
        for name in columns:
            self.trend_tree.heading(name, text=name, anchor="w" if name == "Month" else "e")
            self.trend_tree.column(name, width=150, anchor="w" if name == "Month" else "e")
        self.trend_tree.tag_configure("loss", foreground=c["expense"])
        self.trend_tree.tag_configure("gain", foreground=c["income"])
        self.trend_tree.pack(fill="both", expand=True)

    def on_show_analytics(self) -> None:
        month = self.analytics_month.get().strip()
        if month and not self.is_valid_month(month):
            messagebox.showerror("Error", "Month must follow format YYYY-MM.")
            return
        self.refresh_analytics()

    def draw_chart(self) -> None:
        c = self.COLORS
        self.canvas.delete("all")
        width = max(self.canvas.winfo_width(), 640)

        if not self.chart_data:
            self.canvas.create_text(width / 2, 140, text="No expense data to display yet.",
                                    fill=c["muted"], font=(self.FONT, 11))
            return

        total = sum(self.chart_data.values())
        largest = max(self.chart_data.values())
        ranked = sorted(self.chart_data.items(), key=lambda x: x[1], reverse=True)[:8]
        room = width - 130 - 210

        y = 16
        for i, (label, value) in enumerate(ranked):
            bar = max(int(value / largest * room), 4)
            self.canvas.create_text(16, y + 12, anchor="w", text=label,
                                    fill=c["text"], font=(self.FONT, 10))
            self.canvas.create_rectangle(130, y, 130 + bar, y + 24, fill=self.BAR_COLORS[i % 8], outline="")
            self.canvas.create_text(140 + bar, y + 12, anchor="w",
                                    text=f"{value:,.2f}  ({value / total * 100:.1f}%)",
                                    fill=c["muted"], font=(self.FONT, 9))
            y += 32

    def refresh_analytics(self) -> None:
        month = self.safe_month(self.analytics_month.get(), None)
        self.chart_data = self.analytics.get_category_breakdown("expense", month)
        self.draw_chart()

        self.trend_tree.delete(*self.trend_tree.get_children())
        for my, val in self.analytics.get_monthly_trends().items():
            tag = "gain" if val["savings"] >= 0 else "loss"
            self.trend_tree.insert("", "end", tags=(tag,), values=(
                my, f"{val['income']:,.2f}", f"{val['expense']:,.2f}", f"{val['savings']:,.2f}"))

    def build_csv_tab(self) -> None:
        c = self.COLORS
        page = self.new_page("CSV")

        ttk.Label(page, text="Move data in and out with CSV", style="Title.TLabel").pack(anchor="w")
        ttk.Label(page, text="Export every transaction, or import rows from a spreadsheet file.",
                  style="Muted.TLabel").pack(anchor="w", pady=(2, 16))

        buttons = ttk.Frame(page, style="Card.TFrame")
        buttons.pack(anchor="w")
        ttk.Button(buttons, text="Export Transactions", style="Accent.TButton",
                   command=self.on_export).pack(side="left", padx=(0, 10))
        ttk.Button(buttons, text="Import Transactions", style="Soft.TButton",
                   command=self.on_import).pack(side="left")

        self.csv_msg = ttk.Label(page, text="", foreground=c["income"])
        self.csv_msg.pack(anchor="w", pady=(14, 6))

        ttk.Label(page, text="Rows that were skipped", style="Muted.TLabel").pack(anchor="w")
        self.csv_errors = tk.Text(page, height=10, relief="flat", bg="#f8f9fc",
                                  highlightthickness=1, highlightbackground=c["border"],
                                  font=(self.FONT, 10), padx=8, pady=8)
        self.csv_errors.pack(fill="both", expand=True, pady=(4, 0))

    def on_export(self) -> None:
        path = filedialog.asksaveasfilename(
            defaultextension=".csv", initialfile="expenses_export.csv",
            filetypes=[("CSV files", "*.csv")])
        if not path:
            return

        try:
            count = self.portability.export_to_csv(path)
        except Exception as exc:
            messagebox.showerror("Export failed", str(exc))
            return

        self.csv_msg.config(text=f"Exported {count} transactions to {path}")
        self.set_status(f"Exported {count} transactions.")

    def on_import(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if not path:
            return

        try:
            success, failed, errors = self.portability.import_from_csv(path)
        except Exception as exc:
            messagebox.showerror("Import failed", str(exc))
            return

        self.csv_msg.config(text=f"Imported: {success} success, {failed} errors.")
        self.csv_errors.delete("1.0", "end")
        self.csv_errors.insert("1.0", "\n".join(errors))
        self.set_status(f"Imported {success} transactions, {failed} rows skipped.")
        self.refresh_all()

    def build_tools_tab(self) -> None:
        c = self.COLORS
        page = self.new_page("Currency & Backup")

        self.conv_amount = tk.StringVar()
        self.conv_from = tk.StringVar(value="PKR")
        self.conv_to = tk.StringVar(value="USD")

        conv = ttk.LabelFrame(page, text="Currency converter", style="Card.TLabelframe", padding=16)
        conv.pack(fill="x", pady=(0, 18))

        self.form_row(conv, 0, "Amount", ttk.Entry(conv, textvariable=self.conv_amount, width=22))
        self.form_row(conv, 1, "From", ttk.Combobox(
            conv, textvariable=self.conv_from, values=self.CURRENCIES, state="readonly", width=19))
        self.form_row(conv, 2, "To", ttk.Combobox(
            conv, textvariable=self.conv_to, values=self.CURRENCIES, state="readonly", width=19))
        ttk.Button(conv, text="Convert", style="Accent.TButton",
                   command=self.on_convert).grid(row=3, column=1, sticky="w", pady=(10, 4))
        self.conv_result = ttk.Label(conv, text="", font=(self.FONT, 12, "bold"),
                                     foreground=c["accent"])
        self.conv_result.grid(row=4, column=1, sticky="w", pady=4)

        backup = ttk.LabelFrame(page, text="Database backup", style="Card.TLabelframe", padding=16)
        backup.pack(fill="x")

        ttk.Button(backup, text="Backup Database", style="Soft.TButton",
                   command=self.on_backup).pack(anchor="w")
        self.backup_msg = ttk.Label(backup, text="", foreground=c["income"])
        self.backup_msg.pack(anchor="w", pady=(10, 0))

    def on_convert(self) -> None:
        try:
            amount = self.validate_currency_data(
                self.conv_amount.get().strip(), self.conv_from.get(), self.conv_to.get())
            result = self.services.convert_amount(amount, self.conv_from.get(), self.conv_to.get())
        except Exception as exc:
            messagebox.showerror("Could not convert", str(exc))
            return

        self.conv_result.config(
            text=f"{amount:,.2f} {self.conv_from.get()} = {result:,.2f} {self.conv_to.get()}")

    def on_backup(self) -> None:
        try:
            path = self.services.create_database_backup()
        except Exception as exc:
            messagebox.showerror("Backup failed", str(exc))
            return

        self.backup_msg.config(text=f"Backup saved to: {path}")
        self.set_status("Database backup created.")

    def refresh_all(self) -> None:
        self.refresh_list()
        self.refresh_budgets()
        self.refresh_analytics()

    def run(self) -> None:
        self.root.mainloop()
