# CSView

A powerful terminal-based CSV file viewer with an interactive interface built with Textual.

## Features

- **Interactive Column Browser**: Navigate through your CSV columns in a tree view
- **Data Analysis**: View value distributions, counts, and percentages for each column
- **Filtering**: Apply filters to narrow down your data exploration
- **Sorting**: Sort data by value, count, or percentage
- **Responsive UI**: Clean interface that adapts to your terminal size

## Installation

Install the usual way:

```bash
pip install csview
```

## Usage

```bash
# Basic usage
csview path/to/your/file.csv

# Show debug log in the application
csview path/to/your/file.csv --show-log
```

## How to Use

1. **Navigate Columns**: Use the arrow keys to move through the column list.
2. **View Column Details**: Select a column to see its value distribution.
3. **Filter Data**:
   - Select a value in the details table.
   - Press Enter or click "Apply Filter" to filter the dataset.
4. **Clear Filters**: Click the "Clear Filters" button to reset.
5. **Sort Data**: Click on column headers in the details table to sort.

## License

This project is licensed under the [MIT](LICENSE) license. Contributions are welcome! Please feel free to submit a PR.
