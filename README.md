# ChimeraCat: Intelligent code concatenator and summarizer for LLM analysis.

Analyzes Python codebases to generate consolidated files optimized for LLM processing,
with configurable summarization to reduce token usage while preserving key information.

Now includes cli `ccat` with all configuration exposed as command-line arguments.

## Key Features:
- Analyzes Python files for imports and definitions
- Builds dependency graphs using NetworkX
- Generates both .py files and Colab notebooks
- Smart handling of internal/external imports
- Configurable code summarization

## General Dependency and Interface mapping

If you aren't trying to save on token and conserve context memory when pairing with an LLM, you may still find ChimeraCat's reporting functionality useful.

### CLI report generation example:
```bash

```

## Configuration Details:
- src_dir: Source directory to analyze. Defaults to "./src" in cwd.
    
- summary_level: Controls summarization aggressiveness:
  - NONE: Full code output
  - INTERFACE: Preserve signatures/types/docstrings only
  - CORE: Include core logic, skip standard patterns
    
- exclude_patterns: Files matching these patterns are skipped.
  - Note: ChimeraCat always excludes itself to avoid recursion.
    
- rules: Override default summarization rules with custom SummaryRules.
  - Useful for domain-specific boilerplate detection.
    
- remove_disconnected_deps: When True, omit modules with no dependencies
  from visualization.
  - Useful for cleaner dependency graphs.
    
- generate_report: Controls inclusion of dependency analysis.
  - Defaults to True for INTERFACE/CORE summaries.
    
- report_only: Generate only dependency report without code output.
    
- use_numeric: Use numbers instead of letters for node labels.

## API Example:
    ```python
    # Generate both notebook and summarized Python file
    cat = ChimeraCat(
        "src",
        summary_level=SummaryLevel.INTERFACE,
        exclude_patterns=["tests"],
        remove_disconnected_deps=True
    )
    notebook = cat.generate_colab_notebook()
    py_file = cat.generate_concat_file()
    ```

Though for most cases, what you probably want is the CLI:

## CLI Usage
ChimeraCat installs with a cli tool `ccat`. The configuration dictionary can be manipulated via command-line arguments.

```bash
usage: ccat [-h] [-s {interface,core,none}] [-e EXCLUDE [EXCLUDE ...]] [-o OUTPUT]
            [-t {py,ipynb,both}] [-r] [--report-only] [--numeric-labels] [--no-report]       
            [--remove-disconnected] [-d] [--debug-prefix DEBUG_PREFIX] [--version]
            [src_dir]

    ChimeraCat (ccat) - The smart code concatenator
     /\___/\
    ( o   o )  Intelligently combines Python source files
    (  =^=  )  while maintaining dependencies and readability
     (______)


positional arguments:
  src_dir               Source directory containing Python files (default: src)

options:
  -h, --help            show this help message and exit
  -s {interface,core,none}, --summary-level {interface,core,none}
                        Code summarization level (for .py output only, default: none)        
  -e EXCLUDE [EXCLUDE ...], --exclude EXCLUDE [EXCLUDE ...]
                        Patterns to exclude from processing (e.g., "test" "temp")
  -o OUTPUT, --output OUTPUT
                        Output file name (without extension, default: based on output type   
                        and summary level)
  -t {py,ipynb,both}, --output-type {py,ipynb,both}
                        Output file type (default: both)
  -r, --report          Generate dependency report and ASCII visualization. By default,      
                        reports are included for interface/core summary levels and excluded  
                        for complete code and notebooks. This flag overrides that behavior.  
  --report-only         Suppress code summarization or notebook cocatenization
  --numeric-labels      Use numbers instead of letters for node labels
  --no-report           Suppress dependency report generation even for interface/core        
                        summary levels
  --remove-disconnected
                        Remove modules with no dependencies from visualization
  -d, --debug           Enable debug output
  --debug-prefix DEBUG_PREFIX
                        Prefix for debug messages (default: CCAT:)
  --version             show program's version number and exit
```

"""
