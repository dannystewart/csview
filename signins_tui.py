#!/usr/bin/env python3

"""Analyze user sign-ins based on a CSV audit log export from Microsoft Entra."""

from __future__ import annotations

import csv
import glob
import os
import sys
from collections import defaultdict

from rich import traceback
from textual import on
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
from textual.reactive import reactive
from textual.widgets import Button, DataTable, Footer, Header, Input, RichLog, Static, Tree

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

    #filter_container {
        height: auto;
        padding: 1 2;
    }

    #global_filter_info {
        height: auto;
        padding: 1 2;
        color: $accent;
    }

    #filter_input {
        width: 70%;
    }

    #apply_filter, #clear_filters {
        width: 15%;
    }
    """

    data: dict[str, dict[str, int]] = reactive(defaultdict(lambda: defaultdict(int)))
    total_rows: int = reactive(0)
    selected_column: str = reactive("")
    global_filter: dict[str, set] = reactive({})
    filtered_data: dict[str, dict[str, int]] = reactive(defaultdict(lambda: defaultdict(int)))

    def __init__(self):
        super().__init__()
        self.data = defaultdict(lambda: defaultdict(int))
        self.all_rows = []  # Store all original rows
        self.filtered_rows = []
        self.total_rows = 0
        self.selected_column = ""
        self.global_filter = {}

    def compose(self) -> ComposeResult:
        """Compose the application layout."""
        yield Header()
        yield Tree("Columns", id="column_tree")
        yield Container(
            Static("Global Filter: None", id="global_filter_info"),
            Static("Select a column to view details", id="details_header"),
            Horizontal(
                Input(placeholder="Filter values...", id="filter_input"),
                Button("Apply Filter", id="apply_filter"),
                Button("Clear Filters", id="clear_filters"),
                id="filter_container",
            ),
            DataTable(id="details_table"),
            id="main_container",
        )
        yield RichLog(id="log")
        yield Footer()

    def on_mount(self) -> None:
        """Load the data and populate the tree."""
        self.log_message("Application mounted. Loading data...")
        self.load_data()
        self.filtered_data = self.data.copy()
        self.populate_tree()
        self.query_one("#column_tree").root.expand()  # Expand the root node

    @on(Button.Pressed, "#apply_filter")
    def on_apply_filter(self) -> None:
        """Handle apply filter button press."""
        self.apply_filter()

    def on_clear_filters(self) -> None:
        """Handle clear filters button press."""
        self.global_filter.clear()
        self.filtered_rows = self.all_rows.copy()  # Reset to original data
        self.query_one("#filter_input").value = ""
        self.update_global_filter_info()
        self.update_details()
        self.log_message("Cleared all filters.")

    @on(Input.Submitted, "#filter_input")
    def on_filter_submitted(self) -> None:
        """Handle filter input submission (Enter key)."""
        self.apply_filter()

    def apply_filter(self) -> None:
        """Apply the filter to the current column data and update global filter."""
        filter_text = self.query_one("#filter_input").value.lower()
        if filter_text:
            filtered_values = {
                value
                for value in self.data[self.selected_column]
                if filter_text in str(value).lower()
            }
            self.global_filter[self.selected_column] = filtered_values
        elif self.selected_column in self.global_filter:
            del self.global_filter[self.selected_column]

        self.apply_global_filter()  # Apply the filter to the entire dataset
        self.update_global_filter_info()
        self.update_details()
        self.log_message(f"Applied filter to {self.selected_column}: '{filter_text}'")

    def apply_global_filter(self) -> None:
        """Apply global filter to the entire dataset."""
        if not self.global_filter:
            self.filtered_rows = self.all_rows.copy()  # Reset to original data
            return

        self.filtered_rows = [
            row
            for row in self.all_rows
            if all(row.get(col, "") in values for col, values in self.global_filter.items())
        ]

    def populate_tree(self) -> None:
        """Populate the tree with the columns."""
        tree = self.query_one("#column_tree", Tree)
        for column in self.data:
            tree.root.add(str(column))
        tree.root.expand()  # Expand the root node to show all columns
        self.log_message(f"Populated tree with {len(self.data)} columns")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "apply_filter":
            self.apply_filter()
        elif event.button.id == "clear_filters":
            self.on_clear_filters()

    def load_data(self) -> None:
        """Load the data from the CSV file."""
        log_file = find_log_file()
        self.log_message(f"Loading data from {log_file}")
        with open(log_file) as file:
            reader = csv.DictReader(file)
            self.all_rows = list(reader)  # Store all original rows
            self.filtered_rows = self.all_rows.copy()  # Initialize filtered rows with all rows
            for row in self.all_rows:
                self.total_rows += 1
                for col, value in row.items():
                    self.data[str(col)][str(value)] += 1
        self.log_message(f"Loaded {self.total_rows} rows of data")
        self.log_message(f"Columns found: {', '.join(self.data.keys())}")

    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        """Update the details when a tree node is selected."""
        self.selected_column = str(event.node.label)
        self.query_one("#filter_input").value = ""
        self.log_message(f"Selected column: {self.selected_column}")
        self.update_details()

    def update_details(self) -> None:
        """Update the details table with the selected column data."""
        header = self.query_one("#details_header", Static)
        table = self.query_one("#details_table", DataTable)

        header.update(f"Details for: {self.selected_column}")

        table.clear(columns=True)

        # Count occurrences in filtered rows
        filtered_data = defaultdict(int)
        for row in self.filtered_rows:
            value = row.get(self.selected_column, "")
            filtered_data[value] += 1

        sorted_data = sorted(filtered_data.items(), key=lambda x: x[1], reverse=True)

        if sorted_data:
            # Calculate max widths
            max_value_width = max((len(str(value)) for value, _ in sorted_data), default=10)
            max_count_width = max((len(str(count)) for _, count in sorted_data), default=5)
            max_percentage_width = len("100.00%")  # Fixed width for percentage column

            # Add columns with calculated widths
            table.add_column("Value", width=max(max_value_width, len("Value")))
            table.add_column("Count", width=max(max_count_width, len("Count")))
            table.add_column("Percentage", width=max(max_percentage_width, len("Percentage")))

            total_filtered_count = sum(count for _, count in sorted_data)

            for value, count in sorted_data:
                percentage = (count / total_filtered_count) * 100 if total_filtered_count > 0 else 0
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

    def update_global_filter_info(self) -> None:
        """Update the global filter information display."""
        filter_info = "Global Filter: "
        if self.global_filter:
            filter_info += ", ".join(
                f"{col} ({len(values)} values)" for col, values in self.global_filter.items()
            )
        else:
            filter_info += "None"
        self.query_one("#global_filter_info").update(filter_info)

    def log_message(self, message: str) -> None:
        """Log a message to the RichLog widget."""
        log_widget = self.query_one(RichLog)
        log_widget.write(message)


if __name__ == "__main__":
    app = SignInAnalysisApp()
    app.run()
