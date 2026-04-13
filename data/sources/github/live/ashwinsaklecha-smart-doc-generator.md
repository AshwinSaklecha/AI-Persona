# AshwinSaklecha/smart-doc-generator

Source URL: https://github.com/AshwinSaklecha/smart-doc-generator
Default branch: main
Visibility: public
Stars: 0
Forks: 0
Primary language summary: Python

## Repository Description

No description provided.

## README Snapshot

# 📚 Smart Code Documentation Generator

A powerful Python-based tool that automatically generates well-structured markdown documentation for your codebases. This tool intelligently traverses through directories containing Python files, extracts functions, classes, and other relevant details to produce comprehensive documentation.

## ✨ Features

- 🔍 **Automatic Parsing**
  - Scans directories and extracts information about functions, classes, and imports
  - Intelligent recognition of code structure and relationships

- 📖 **Comprehensive Documentation**
  - Supports both detailed and brief documentation styles
  - Generates an organized Table of Contents for easy navigation
  - Clean and readable markdown output

- 📁 **Multi-File Support**
  - Seamlessly handles codebases with multiple Python files
  - Maintains proper structure and relationships between files

- ⚠️ **Error Handling**
  - Gracefully manages exceptions during parsing
  - Provides detailed reports for problematic files
  - Ensures documentation completion even with partial failures

## 🛠️ How It Works

### Directory Parsing
1. Recursively scans the specified directory for Python files
2. Extracts essential information including:
   - Module-level docstrings
   - Function definitions and signatures
   - Class hierarchies and methods
   - Import statements and dependencies
   - Additional metadata

### Documentation Generation
- Creates structured markdown files with organized sections
- Supports multiple documentation styles:
  - Detailed: Complete information including imports, decorators, and docstrings
  - Brief: Essential information for quick reference

## 📥 Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/AshwinSaklecha/smart-doc-generator.git
   ```

2. Navigate to the project directory:
   ```bash
   cd smart-doc-generator
   ```

3. Install required dependencies:
   - os
   - ast
   - inspect
   - typing

## 🚀 Usage

1. Update the `directory_path` in your script:
   ```python
   directory_path = "path_to_your_codebase"
   ```

2. Run the script:
   ```bash
   python main.py
   ```

3. Access your documentation:
   - Find the generated `documentation.md` in the project directory

## ⚙️ Configuration Options

### Documentation Styles

- `brief`: Concise documentation with essential information (default)
- `detailed`: Comprehensive documentation including all available information

To switch styles, modify the `generate_documentation` function call:

```python
directory_path = r"D:\megaProject\codeFiles"  # Use raw string
functions_and_classes = parse_code_from_directory(directory_path)
generate_documentation(functions_and_classes, style="detailed")  # or "brief"
```

## 👥 Contributing

We welcome contributions! Feel free to:
- Open issues for bugs or feature requests
- Submit pull requests with improvements
- Share ideas for enhancing the tool

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgements

- Python **AST module** for robust code parsing and analysis
- The amazing open-source community for inspiration and tools
- All contributors who help improve this project

---
Created with ❤️ by [Ashwin Saklecha](https://github.com/AshwinSaklecha)

