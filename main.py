#!/usr/bin/env python3

"""View a CSV file using a textual interface."""

from __future__ import annotations

import csv
from collections import defaultdict
from datetime import datetime

import click
from textual import on
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
from textual.reactive import reactive
from textual.widgets import Button, DataTable, Footer, Header, Input, RichLog, Static, Tree
from zoneinfo import ZoneInfo

from dsutil.errors import configure_traceback

configure_traceback()


class CSVViewer(App):
    """View a CSV file using a textual interface."""

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

        DataTable > .datatable--cursor {
            background: $accent;
            color: $text;
        }

        #details_header {
            height: 5%;
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

        #log_container {
            height: 15%;
            dock: bottom;
            border: solid $accent;
            border-title-align: center;
        }

        #log {
            height: 100%;
            border: none;
            padding: 0 1;
        }
    """

    data: dict[str, dict[str, int]] = reactive(defaultdict(lambda: defaultdict(int)))
    total_rows: int = reactive(0)
    selected_column: str = reactive("")
    selected_row: int | None = reactive(None)
    global_filter: dict[str, set] = reactive({})
    filtered_data: dict[str, dict[str, int]] = reactive(defaultdict(lambda: defaultdict(int)))
    sort_column: str = reactive("")
    sort_reverse: bool = reactive(False)

    def __init__(self, filename: str):
        super().__init__()
        self.filename: str = filename
        self.all_rows: list = []  # Store all original rows
        self.filtered_rows: list = []

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
            DataTable(id="details_table", show_cursor=True),
            id="main_container",
        )
        yield Container(RichLog(id="log"), id="log_container")
        yield Footer()

    def on_mount(self) -> None:
        """Load the data and populate the tree."""
        self.print_log("Application mounted. Loading data...")
        self.load_data()
        self.populate_tree()
        self.query_one("#column_tree").root.expand()
        self.setup_data_table()
        self.query_one(DataTable).focus()

    def load_data(self) -> None:
        """Load the data from a CSV file."""
        self.print_log(f"Loading data from {self.filename}")
        with open(self.filename) as file:
            reader = csv.DictReader(file)
            self.all_rows = list(reader)  # Store all original rows
            self.filtered_rows = self.all_rows.copy()  # Initialize filtered rows with all rows
            for row in self.all_rows:
                self.total_rows += 1
                for col, value in row.items():
                    self.data[str(col)][str(value)] += 1
        self.print_log(f"Loaded {self.total_rows} rows of data")
        self.print_log(f"Columns found: {', '.join(self.data.keys())}")

    def setup_data_table(self) -> None:
        """Set up the DataTable with sortable headers."""
        table = self.query_one(DataTable)
        table.add_column("Value", key="value")
        table.add_column("Count", key="count")
        table.add_column("Percentage", key="percentage")
        table.cursor_type = "row"

    def populate_tree(self) -> None:
        """Populate the tree with the columns."""
        tree = self.query_one("#column_tree", Tree)
        for column in self.data:
            tree.root.add(str(column))
        tree.root.expand()  # Expand the root node to show all columns
        self.print_log(f"Populated tree with {len(self.data)} columns")

    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        """Update the details when a tree node is selected."""
        self.selected_column = str(event.node.label)
        self.query_one("#filter_input").value = ""
        self.print_log(f"Selected column: {self.selected_column}")
        self.update_details()

    def on_data_table_header_selected(self, event: DataTable.HeaderSelected) -> None:
        """Handle sorting when a column header is clicked."""
        if self.sort_column == event.column_key:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = event.column_key
            self.sort_reverse = False
        self.update_details()

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle row selection in the DataTable."""
        self.selected_row = event.row_key
        table = self.query_one(DataTable)
        row = table.get_row(event.row_key)
        selected_value = row[0] if row else ""
        self.query_one("#filter_input").value = str(selected_value)
        self.print_log(f"Selected row: {selected_value}")

    def apply_filter(self) -> None:
        """Apply the filter to the current column data and update global filter."""
        filter_text = self.query_one("#filter_input").value.strip()
        self.print_log(f"Applying filter - Text: '{filter_text}', Column: {self.selected_column}")

        if filter_text:
            if self.selected_column not in self.global_filter:
                self.global_filter[self.selected_column] = set()
            self.global_filter[self.selected_column].add(filter_text)
            self.print_log(f"Added to global filter: {self.selected_column}: {filter_text}")
        elif self.selected_column in self.global_filter:
            del self.global_filter[self.selected_column]
            self.print_log(f"Removed from global filter: {self.selected_column}")

        self.apply_global_filter()
        self.update_global_filter_info()
        self.update_details()
        self.print_log(f"Global filter after update: {self.global_filter}")
        self.selected_row = None  # Reset selected row after applying filter

    def on_clear_filters(self) -> None:
        """Handle clear filters button press."""
        self.global_filter.clear()
        self.filtered_rows = self.all_rows.copy()  # Reset to original data
        self.query_one("#filter_input").value = ""
        self.update_global_filter_info()
        self.update_details()
        self.print_log("Cleared all filters.")

    def apply_global_filter(self) -> None:
        """Apply global filter to the entire dataset."""
        if not self.global_filter:
            self.filtered_rows = self.all_rows.copy()  # Reset to original data
            self.print_log("No global filter, using all rows")
            return

        self.print_log(f"Applying global filter: {self.global_filter}")
        self.filtered_rows = [
            row
            for row in self.all_rows
            if all(
                any(
                    filter_value.lower() in str(row.get(col, "")).lower() for filter_value in values
                )
                for col, values in self.global_filter.items()
            )
        ]
        self.print_log(f"Filtered rows count: {len(self.filtered_rows)}")

    @on(Button.Pressed, "#apply_filter")
    def on_apply_filter(self) -> None:
        """Handle apply filter button press."""
        self.apply_filter()

    @on(Input.Submitted, "#filter_input")
    def on_filter_submitted(self) -> None:
        """Handle filter input submission (Enter key)."""
        self.apply_filter()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "apply_filter":
            self.apply_filter()
        elif event.button.id == "clear_filters":
            self.on_clear_filters()

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
            # Replace empty or None values with "(no value)"
            value = "(no value)" if value in (None, "") else value
            filtered_data[value] += 1

        sorted_data = list(filtered_data.items())
        total_filtered_count = sum(count for _, count in sorted_data)

        # Prepare data for sorting and calculate max widths
        table_data = []
        max_value_width = len("Value")
        max_count_width = len("Count")
        max_percentage_width = len("Percentage")

        for value, count in sorted_data:
            percentage = (count / total_filtered_count) * 100 if total_filtered_count > 0 else 0
            percentage_str = f"{percentage:.2f}%"
            table_data.append((str(value), count, percentage_str))

            max_value_width = max(max_value_width, len(str(value)))
            max_count_width = max(max_count_width, len(str(count)))
            max_percentage_width = max(max_percentage_width, len(percentage_str))

        # Set default sorting if not specified
        if not self.sort_column:
            self.sort_column = "count"
            self.sort_reverse = True

        # Log sorting information
        self.print_log(f"Sorting by: {self.sort_column}, Reverse: {self.sort_reverse}")

        # Sort the data based on the selected column and direction
        if self.sort_column == "value":
            table_data.sort(key=lambda x: x[0], reverse=self.sort_reverse)
        elif self.sort_column == "count":
            table_data.sort(key=lambda x: x[1], reverse=self.sort_reverse)
        elif self.sort_column == "percentage":
            table_data.sort(key=lambda x: float(x[2][:-1]), reverse=self.sort_reverse)

        # Log first few items after sorting
        self.print_log(f"First few items after sorting: {table_data[:5]}")

        # Add columns with calculated widths
        table.add_column("Value", key="value", width=max_value_width)
        table.add_column("Count", key="count", width=max_count_width)
        table.add_column("Percentage", key="percentage", width=max_percentage_width)

        self.print_log(f"Updating details for column: {self.selected_column}")
        self.print_log(f"Total filtered rows: {len(self.filtered_rows)}")

        # Add rows to the table
        for row in table_data:
            table.add_row(*row)

        if not table_data:
            table.add_row("No data available", "", "")

        self.print_log(f"Updated table with {len(table_data)} rows for {self.selected_column}")
        table.refresh(layout=True)

    def print_log(self, message: str) -> None:
        """Log a message to the RichLog widget and debug file."""
        log_widget = self.query_one(RichLog)
        timestamp = datetime.now(tz=ZoneInfo("America/New_York")).strftime("%I:%M:%S %p")
        log_message = f"[{timestamp}] {message}"
        log_widget.write(log_message)
        self.log_to_file(log_message)

    def log_to_file(self, message: str) -> None:
        """Write a debug message to a file."""
        timestamp = datetime.now(tz=ZoneInfo("America/New_York")).strftime("%Y-%m-%d %H:%M:%S")
        with open("debug_log.txt", "a") as f:
            f.write(f"{timestamp}: {message}\n")


@click.command()
@click.argument("filename", type=click.Path(exists=True))
def main(filename: str) -> None:
    """Run the application."""
    app = CSVViewer(filename)
    app.run()


if __name__ == "__main__":
    main()
