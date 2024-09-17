#!/usr/bin/env python3

"""Analyze user sign-ins based on a CSV audit log export from Microsoft Entra."""

from __future__ import annotations

import csv
import glob
import os
import sys
from collections import defaultdict

from rich import traceback
from textual.app import App, ComposeResult
from textual.containers import Container
from textual.reactive import reactive
from textual.widgets import DataTable, Footer, Header, RichLog, Static, Tree

from dsutil.text import print_colored

traceback.install()


def find_log_file() -> str:
    """Find the most recent CSV file with 'SignIns' in the name or use command-line argument."""
    if len(sys.argv) > 1:
        return sys.argv[1]

    csv_files = glob.glob("*SignIns*.csv")
    if not csv_files:
        print_colored("No CSV files with 'SignIns' in the name found.", "red")
        sys.exit(1)

    newest_file = max(csv_files, key=os.path.getctime)
    print_colored(f"Using file: {newest_file}", "green")
    return newest_file


class SignInAnalysisApp(App):
    """Analyze user sign-ins based on a CSV audit log export from Microsoft Entra."""

    CSS = """
    #column_tree {
        width: 25%;
        height: 100%;
        dock: left;
    }

    #main_container {
        width: 1fr;
        height: 100%;
    }

    DataTable {
        height: 1fr;
    }

    #details_header {
        height: auto;
        padding: 1 2;
    }
    """

    data: dict[str, dict[str, int]] = reactive(defaultdict(lambda: defaultdict(int)))
    total_rows: int = reactive(0)
    selected_column: str = reactive("")

    def compose(self) -> ComposeResult:
        """Compose the application layout."""
        yield Header()
        yield Tree("Columns", id="column_tree")
        yield Container(
            Static("Select a column to view details", id="details_header"),
            DataTable(id="details_table"),
            id="main_container",
        )
        yield RichLog(id="log")
        yield Footer()

    def on_mount(self) -> None:
        """Load the data and populate the tree."""
        self.log_message("Application mounted. Loading data...")
        self.load_data()
        self.populate_tree()

    def load_data(self) -> None:
        """Load the data from the CSV file."""
        log_file = find_log_file()
        self.log_message(f"Loading data from {log_file}")
        with open(log_file) as file:
            reader = csv.DictReader(file)
            for row in reader:
                self.total_rows += 1
                for col, value in row.items():
                    self.data[str(col)][str(value)] += 1
        self.log_message(f"Loaded {self.total_rows} rows of data")
        self.log_message(f"Columns found: {', '.join(self.data.keys())}")

    def populate_tree(self) -> None:
        """Populate the tree with the columns."""
        tree = self.query_one("#column_tree", Tree)
        for column in self.data:
            tree.root.add(str(column))
        self.log_message(f"Populated tree with {len(self.data)} columns")

    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        """Update the details when a tree node is selected."""
        self.selected_column = str(event.node.label)
        self.log_message(f"Selected column: {self.selected_column}")
        self.update_details()

    def update_details(self) -> None:
        """Update the details table with the selected column data."""
        header = self.query_one("#details_header", Static)
        table = self.query_one("#details_table", DataTable)

        header.update(f"Details for: {self.selected_column}")

        table.clear(columns=True)

        if self.selected_column in self.data:
            sorted_data = sorted(
                self.data[self.selected_column].items(), key=lambda x: x[1], reverse=True
            )

            # Calculate max widths
            max_value_width = max(len(str(value)) for value, _ in sorted_data)
            max_count_width = max(len(str(count)) for _, count in sorted_data)
            max_percentage_width = len("100.00%")  # Fixed width for percentage column

            # Add columns with calculated widths
            table.add_column("Value", width=max(max_value_width, len("Value")))
            table.add_column("Count", width=max(max_count_width, len("Count")))
            table.add_column("Percentage", width=max(max_percentage_width, len("Percentage")))

            for value, count in sorted_data:
                percentage = (count / self.total_rows) * 100
                table.add_row(str(value), str(count), f"{percentage:.2f}%")
            self.log_message(
                f"Updated table with {len(sorted_data)} rows for {self.selected_column}"
            )
        else:
            table.add_column("Value", width=len("No data available"))
            table.add_column("Count", width=len("Count"))
            table.add_column("Percentage", width=len("Percentage"))
            table.add_row("No data available", "", "")
            self.log_message(f"No data available for {self.selected_column}")

        table.refresh(layout=True)

    def log_message(self, message: str) -> None:
        """Log a message to the RichLog widget."""
        log_widget = self.query_one(RichLog)
        log_widget.write(message)


if __name__ == "__main__":
    app = SignInAnalysisApp()
    app.run()
