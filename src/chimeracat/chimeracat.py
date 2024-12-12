"""
### TODO:
# cli
#   srcdir args
#   summarization level
#   colab
#   exclusions
#   other patterns

ChimeraCat emerged as an ancillary utility for some larger work I was 
doing with the help of Claude 3.5 Sonnet (New) in October 2024.
It has grown and evolved quite a bit in the short time since it was born.

This utility:

Analyzes Python files for imports and definitions
Builds a dependency graph
Generates both a single .py file and a Colab notebook
Handles internal vs external imports
Avoids duplicate definitions
Creates a clean, organized output

QuickStart:

```python
from ChimeraCat import ChimeraCat

# Generate both notebook and Python file
concat = ChimeraCat("src")
notebook_file = concat.generate_colab_notebook()
py_file = concat.generate_concat_file()
```

Features Claude is particularly proud of:
- Dependency ordering using NetworkX
- Duplicate prevention
- Clean handling of internal vs external imports
- Automatic notebook generation
- Maintains code readability with section headers

Advanced Usage:

You can pass to the ChimeraCat constructor any of the following:

    src_dir: str = "src",  

# defaults to a "./src" directory in the cwd. 
# this is how you'd override that.

    summary_level: SummaryLevel = SummaryLevel.NONE, 

# how hard, if at all, do you want ccat to try 
# to strip the code it finds down to its essentials? 
# valid options are explicit in the SmarryLevel enum.

    exclude_patterns: List[str] = None, 

# this is a list of strings that each file in the 
# src_dir directory will be checked against; 
# if there is a full or partial match, the file will 
# not be scanned. ccat will not scan itself, 
# (that is, the currently executing script filename)
# owing to its origins residing in a tools/ directory 
# of a larger project and tending to clutter up 
# the summary cats.

    rules: Optional[SummaryRules] = None, 

# you can construct a SummaryRules class instance 
# and pass it here if you want to expand on ccat's 
# basic functionality. For applications in a specific 
# domain for example, perhaps you want to remove a 
# rule from the defaults, or there is code that would 
# be considered boilerplate in this domain, but ccat 
# might think it looks interesting. Override the builtins here.

    remove_disconnected_deps: bool = False, 

# if the app has many imports, but the dependency graph 
# finds to relations between them, by default they are 
# visualized as disconnected nodes. To save space, you 
# may want to omit them from ccat's output by setting 
# this True

    debug: bool = False, 

# if this is False, _debug_print() messages are elided

    debug_str = "" 

# if debug is True, if debug_str is set, messages printed 
# will be prefaced with this string to aid in eyeballing 
# or grepping program stdout/stderr output.


"""

import re
from pathlib import Path
import networkx as nx

from enum import Enum
from typing import Dict, List, Set, Optional, Pattern
from dataclasses import dataclass, field
from datetime import datetime
from phart import ASCIIRenderer, LayoutOptions, NodeStyle    

import argparse
import sys

ccat_version = "1.0.2"
class SummaryLevel(Enum):
    INTERFACE = "interface"     # Just interfaces/types/docstrings
    CORE = "core"              # + Core logic, skip standard patterns
    NONE = "none"      # Full code

@dataclass
class SummaryPattern:
    """Pattern for code summarization with explanation"""
    pattern: str
    replacement: str
    explanation: str
    flags: re.RegexFlag = re.MULTILINE

    def apply(self, content: str) -> str:
        return re.sub(self.pattern, f"{self.replacement} # {self.explanation}\n", 
                     content, flags=self.flags)

@dataclass
class SummaryRules:
    """Collection of patterns for different summary levels"""
    interface: List[SummaryPattern] = field(default_factory=list)
    core: List[SummaryPattern] = field(default_factory=list)

    @classmethod
    def default_rules(cls) -> 'SummaryRules':
        return cls(
            interface=[
                SummaryPattern(
                    pattern=r'(class\s+\w+(?:\([^)]*\))?):(?:\s*"""[^"]*""")?[^\n]*(?:\n(?!class|def)[^\n]*)*',
                    replacement=r'\1:\n    ... # ',
                    explanation="Class interface preserved",
                    flags=re.MULTILINE
                ),
                SummaryPattern(
                    pattern=r'(def\s+\w+\s*\([^)]*\)):(?:\s*"""[^"]*""")?[^\n]*(?:\n(?!class|def)[^\n]*)*',
                    replacement=r'\1:\n    ... # ',
                    explanation="Function signature preserved",
                    flags=re.MULTILINE
                )
            ],
            core=[
                SummaryPattern(
                    pattern=r'(def\s+get_\w+\([^)]*\)):\s*return[^\n]*\n',
                    replacement=r'\1:\n    ... # ',
                    explanation="Getter method summarized"
                ),
                SummaryPattern(
                    pattern=r'(def\s*__init__\s*\([^)]*\)):[^\n]*(?:\n(?!def|class)[^\n]*)*',
                    replacement=r'\1:\n    ... # ',
                    explanation="Standard initialization summarized"
                )
            ]
        ) 
@dataclass
class ModuleInfo:
    """Information about a Python module"""
    path: Path
    content: str
    imports: Set[str]
    classes: Set[str]
    functions: Set[str]

class ChimeraCat:
    """Utility to concatenate modular code into Colab-friendly single files"""
    def __init__(self, 
             src_dir: str = "src", 
             summary_level: SummaryLevel = SummaryLevel.NONE,
             exclude_patterns: List[str] = None,
             rules: Optional[SummaryRules] = None,
             remove_disconnected_deps: bool = False,
             generate_report: Optional[bool] = None,
             debug: bool = False,
             debug_str = ""):

        self.src_dir = Path(src_dir)
        self.summary_level = summary_level
        self.rules = rules or SummaryRules.default_rules()
        self.modules: Dict[Path, ModuleInfo] = {}
        self.dep_graph = nx.DiGraph()
        self.self_path = Path(__file__).resolve()
        self.exclude_patterns = exclude_patterns or []
        self.debug = debug
        self.remove_disconnected_deps = remove_disconnected_deps
        self.debug_str = debug_str

        if generate_report is None:
            self.generate_report = summary_level in (SummaryLevel.INTERFACE, SummaryLevel.CORE)
        else:
            self.generate_report = generate_report

    def _debug_print(self, *args, **kwargs):
        """Helper for debug output"""
        if self.debug:
            print(f"{self.debug_str}: {args} {list(kwargs.items())}")

    def should_exclude(self, file_path: Path) -> bool:
        """Check if a file should be excluded from processing"""
        # Always exclude self
        self._debug_print(file_path.resolve(), self.self_path)
        if file_path.resolve() == self.self_path:
            if self.debug:
                self._debug_print(f"excluding self {self.self_path}")
            return True
            
        # Check against exclude patterns
        str_path = str(file_path)
        self._debug_print("str_path",str_path)
        for pattern in self.exclude_patterns:
            self._debug_print("comparing", pattern, str_path)
        return any(pattern in str_path for pattern in self.exclude_patterns)

    def analyze_file(self, file_path: Path) -> Optional[ModuleInfo]:
        """Analyze a Python file for imports and definitions"""
        if self.should_exclude(file_path):
            self._debug_print(f'excluding {file_path}')
            return None

        with open(file_path, 'r') as f:
            content = f.read()
            
        # Find imports
        import_pattern = r'^(?:from\s+(\S+)\s+)?import\s+([^#\n]+)'
        imports = set()
        for match in re.finditer(import_pattern, content, re.MULTILINE):
            if match.group(1):  # from X import Y
                imports.add(match.group(1))
            else:  # import X
                imports.add(match.group(2).split(',')[0].strip())
                
        # Find class definitions
        class_pattern = r'class\s+(\w+)'
        classes = set(re.findall(class_pattern, content))
        
        # Find function definitions
        func_pattern = r'def\s+(\w+)'
        functions = set(re.findall(func_pattern, content))
        
        return ModuleInfo(
            path=file_path,
            content=content,
            imports=imports,
            classes=classes,
            functions=functions
        )

    def _summarize_content(self, content: str) -> str:
        """Apply summary patterns based on current level"""
        if not isinstance(content, str):
            raise TypeError(f"Expected string content but got {type(content)}: {content}")
            
        if self.summary_level == SummaryLevel.NONE:
            return content
            
        result = content
        rules = self.rules or SummaryRules.default_rules()
        
        # Apply patterns based on level
        if self.summary_level == SummaryLevel.INTERFACE:
            for pattern in rules.interface:
                result = pattern.apply(result)
        elif self.summary_level == SummaryLevel.CORE:
            # Apply both interface and core patterns
            for pattern in rules.interface + rules.core:
                result = pattern.apply(result)
                
        return result

    def _process_imports(self, content: str, module_path: Path) -> str:
        """Process and adjust imports for concatenated context"""
        if not isinstance(content, str):
            raise TypeError(f"Expected string content but got {type(content)}: {content}")

        def replace_relative_import(match: re.Match) -> str:
            indent = len(match.group()) - len(match.group().lstrip())
            spaces = ' ' * indent
            original_line = match.group()
            return f'{spaces}"""RELATIVE_IMPORT: \n{original_line}\n{spaces}"""'
        
        pattern = r'^\s*from\s+\..*$'
        return re.sub(pattern, replace_relative_import, content, flags=re.MULTILINE)

    def build_dependency_graph(self):
        """Build a dependency graph with proper relative import resolution"""
        self._debug_print("\nBuilding dependency graph...")
        
        # First pass: Create nodes
        for file_path in self.src_dir.rglob("*.py"):
            module_info = self.analyze_file(file_path)
            if module_info is not None:
                self.modules[file_path] = module_info
                self.dep_graph.add_node(file_path)
                self._debug_print(f"Added node: {file_path.relative_to(self.src_dir)}")
                if module_info.imports:
                    self._debug_print(f"  Found imports: {', '.join(module_info.imports)}")
        
        # Second pass: Add edges
        for file_path, module in self.modules.items():
            current_module = str(file_path.relative_to(self.src_dir)).replace('\\', '/')
            module_dir = str(file_path.parent.relative_to(self.src_dir)).replace('\\', '/')
            
            for imp in module.imports:
                if imp.startswith('.'):
                    # Handle relative imports
                    dots = imp.count('.')
                    parts = module_dir.split('/')
                    
                    # Go up directory tree based on dot count
                    if dots > len(parts):
                        continue  # Invalid relative import
                        
                    base_path = '/'.join(parts[:-dots] if dots > 0 else parts)
                    target_module = imp.lstrip('.')
                    
                    if target_module:
                        full_target = f"{base_path}/{target_module.replace('.', '/')}.py"
                    else:
                        full_target = f"{base_path}/__init__.py"
                    
                    # Find matching module
                    for other_path in self.modules:
                        other_rel = str(other_path.relative_to(self.src_dir)).replace('\\', '/')
                        if other_rel == full_target:
                            self._debug_print(f"  Adding edge: {other_rel} -> {current_module}")
                            self.dep_graph.add_edge(file_path, other_path)
                else:
                    # Handle absolute imports within our project
                    potential_path = imp.replace('.', '/') + '.py'
                    for other_path in self.modules:
                        other_rel = str(other_path.relative_to(self.src_dir)).replace('\\', '/')
                        if other_rel.endswith(potential_path):
                            self._debug_print(f"  Adding edge: {other_rel} -> {current_module}")
                            self.dep_graph.add_edge(file_path, other_path)

    def generate_concat_file(self, output_file: str = "colab_combined.py") -> str:
        """Generate a single file combining all modules in dependency order"""
        self.build_dependency_graph()
        
        header = f"""{self._get_header_content()}
Summary Level: {self.summary_level.value}
        """
        
        # Start with external imports
        output = [
            header,
            '"""',
            self.generate_dependency_ascii(),
            "# External imports",'"""',
            *self._get_external_imports(),
            "\n# Combined module code\n"
        ]
        
        # Get files in dependency order
        sorted_files = self._get_sorted_files()
        
        # Create a map of original module paths to their contents
        module_contents = {}
        
        # First pass: collect and process all module contents
        for file_path in sorted_files:
            if file_path in self.modules:
                module = self.modules[file_path]
                rel_path = file_path.relative_to(self.src_dir)
                
                # Process imports and summarize content
                processed_content = self._process_imports(
                    self._summarize_content(module.content),
                    file_path
                )
                
                module_contents[file_path] = {
                    'content': processed_content,
                    'rel_path': rel_path
                }
        
        # Second pass: output in correct order with headers
        for file_path in sorted_files:
            if file_path in module_contents:
                info = module_contents[file_path]
                output.extend([
                    f"\n# From {info['rel_path']}",
                    info['content']
                ])
        
        with open(output_file, 'w') as f:
            f.write('\n'.join(output))
            
        return output_file
    
    def _get_external_imports(self) -> List[str]:
      """Get sorted list of external imports from all modules"""
      external_imports = set()
      for module in self.modules.values():
          external_imports.update(
              imp for imp in module.imports 
              if not any(str(imp).startswith(str(p.relative_to(self.src_dir).parent)) 
                        for p in self.modules)
              and not imp.startswith('.')
          )
      
      # Format and sort the import statements
      return sorted(f"import {imp}" for imp in external_imports)

    def _paths_match(self, path: Path, import_parts: List[str]) -> bool:
        """Check if a path matches an import statement"""
        path_parts = list(path.parts)
        return len(path_parts) == len(import_parts) and \
               all(p == i for p, i in zip(path_parts, import_parts))

    def _get_sorted_files(self) -> List[Path]:
        """Get files sorted by dependencies"""
        try:
            # Topological sort ensures dependencies come before dependents
            sorted_files = list(nx.topological_sort(self.dep_graph))
            
            # Debug info
            print("\nDependency Resolution:")
            for idx, file in enumerate(sorted_files):
                deps = list(self.dep_graph.predecessors(file))
                print(f"{idx+1}. {file.name}")
                if deps:
                    print(f"   Depends on: {', '.join(d.name for d in deps)}")
            
            return sorted_files

        except nx.NetworkXUnfeasible as e:
            # If we detect a cycle, identify and report it
            cycles = list(nx.simple_cycles(self.dep_graph))
            print("Warning: Circular dependencies detected:")
            for cycle in cycles:
                cycle_path = ' -> '.join(p.name for p in cycle)
                print(f"  {cycle_path}")
            
            # Fall back to simple ordering but warn user
            print("Using simple ordering instead.")
            return list(self.modules.keys())

    def visualize_dependencies(self, output_file: str = "dependencies.png"):
        """Optional: Visualize the dependency graph"""
        try:
            import matplotlib.pyplot as plt
            pos = nx.spring_layout(self.dep_graph)
            plt.figure(figsize=(12, 8))
            nx.draw(self.dep_graph, pos, with_labels=True, 
                   labels={p: p.name for p in self.dep_graph.nodes()},
                   node_color='lightblue',
                   node_size=2000,
                   font_size=8)
            plt.savefig(output_file)
            plt.close()
            return output_file
        except ImportError:
            print("matplotlib not available for visualization")
            return None

    def get_dependency_report(self) -> str:
        """Generate a detailed dependency report"""
        report = ["Dependency Analysis Report", "=" * 25, ""]
        report.append(self.generate_dependency_ascii()) 
        # Module statistics
        report.extend([
            "Module Statistics:",
            f"Total modules: {len(self.modules)}",
            f"Total dependencies: {self.dep_graph.number_of_edges()}",
            ""
        ])
        
        # Dependency chains
        report.extend(["Dependency Chains:", "-" * 17])
        try:
            sorted_files = list(nx.topological_sort(self.dep_graph))
            for idx, file in enumerate(sorted_files):
                deps = list(self.dep_graph.predecessors(file))
                report.append(f"{idx+1}. {file.relative_to(self.src_dir)}")
                if deps:
                    report.append(f" Depends on: {', '.join(str(d.relative_to(self.src_dir)) for d in deps)}")
            report.append("")
        except nx.NetworkXUnfeasible:
            report.extend([
                "Warning: Circular dependencies detected!",
                "Cycles found:",
                *[f"  {' -> '.join(str(p.relative_to(self.src_dir)) for p in cycle)}"
                  for cycle in nx.simple_cycles(self.dep_graph)],
                ""
            ])
        
        # Module details
        report.extend(["Module Details:", "-" * 13])
        for path, module in self.modules.items():
            report.extend([
                f"\n{path.relative_to(self.src_dir)}:",
                f"Classes: {', '.join(module.classes) if module.classes else 'None'}",
                f"Functions: {', '.join(module.functions) if module.functions else 'None'}",
                f"Imports: {', '.join(module.imports) if module.imports else 'None'}"
            ])
        
        return '\n'.join(report)

    def _get_header_content(self):
        return  f"""
##Notebook Generated by ChimeraCat\n
# Generated by ChimeraCat
#  /\\___/\\   ChimeraCat
# ( o   o )  smart code concatenator/summarizer
# (  =^=  )  ccat {ccat_version} https:?/github.com/scottvr/chimeracat
#  (______)  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
        
    def generate_colab_notebook(self, output_file: str = "colab_combined.ipynb"):
        """Generate a Jupyter notebook with the combined code"""
        py_file = self.generate_concat_file("temp_combined.py")
        
        with open(py_file, 'r') as f:
            code = f.read()
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S") 
        notebook = {
            "cells": [
                {
                    "cell_type": "markdown",
                    "metadata": {},
                    "source": [
                        "##Notebook Generated by ChimeraCat\n"
                    ],
                },
                {
                    "cell_type": "code",
                    "metadata": {},
                    "source": code.splitlines(keepends=True),
                    "execution_count": None,
                    "outputs": []
                },
                {
                    "cell_type": "markdown",
                    "metadata": {},
                    "source": [
                        "```\n",
                        f"{self._get_header_content()}".splitlines(keepends=True),
                        "```\n"
                    ]
                }

            ],
            "metadata": {
                "kernelspec": {
                    "display_name": "Python 3",
                    "language": "python",
                    "name": "python3"
                }
            },
            "nbformat": 4,
            "nbformat_minor": 4
        }
        
        import json
        with open(output_file, 'w') as f:
            json.dump(notebook, f, indent=2)
        
        Path("temp_combined.py").unlink()  # Clean up temporary file
        return output_file
    
    def generate_dependency_ascii(self) -> str:
        """Generate ASCII representation of dependency graph"""
        
        display_graph = nx.DiGraph()
        
         # Mapping of short labels to original node names
        label_mapping = {}
        label_index = 0

        def get_short_label(index):
            """Generate a short label (e.g., A, B, ..., AA, AB)."""
            label = ""
            while index >= 0:
                label = chr(65 + index % 26) + label
                index = index // 26 - 1
            return label

        # Add nodes and edges with relative path names
        for node in self.dep_graph.nodes():
            short_label = get_short_label(label_index)
            label_mapping[short_label] = node
            display_graph.add_node(short_label)
            label_index += 1
        
        # Add edges using new node names
        for src, dst in self.dep_graph.edges():
            src_label = [k for k, v in label_mapping.items() if v == src][0]
            dst_label = [k for k, v in label_mapping.items() if v == dst][0]
            display_graph.add_edge(src_label, dst_label)
        
        if self.remove_disconnected_deps:
            self._debug_print("removing disconnected imports (no dependent relationship)")
            self._debug_print(display_graph)
            display_graph.remove_nodes_from(list(nx.isolates(display_graph)))
            self._debug_print(display_graph)

        options = LayoutOptions(
            node_style=NodeStyle.MINIMAL,
            node_spacing=4,
            layer_spacing=3
        )

        # Generate the legend
        legend_lines = ["Legend:"]
        for short_label, original_node in label_mapping.items():
            legend_lines.append(f"{short_label}: {original_node}")
        legend = "\n".join(legend_lines)

        renderer = ASCIIRenderer(display_graph, options=options)
        ascii_art = f"""
Directory Structure:
{self._get_tree_output()}
   
Module Dependencies:

{legend}
{"non-dependent modules elided from visualization" if self.remove_disconnected_deps else "node names detached from the network and printed in isolation are non-connected/likely unused."}
{renderer.render()}
     
Import Summary:
{self._generate_import_summary()}
"""
        return ascii_art

    def _get_tree_output(self) -> str:
        """Get tree command output"""
        try:
            import subprocess
            result = subprocess.run(
                ['tree', str(self.src_dir)],
                capture_output=True,
                text=True
            )
            return result.stdout
        except FileNotFoundError:
            # Fallback to simple directory listing if tree not available
            return '\n'.join(str(p.relative_to(self.src_dir)) 
                            for p in self.src_dir.rglob('*.py'))
    
    def _generate_import_summary(self) -> str:
        """Generate summary of imports"""
        external_imports = set()
        internal_deps = set()
        
        for module in self.modules.values():
            for imp in module.imports:
                if not imp.startswith('.'):
                    external_imports.add(imp)
                else:
                    internal_deps.add(imp)
        
        return f"""
    External Dependencies:
    {', '.join(sorted(external_imports))}
    
    Internal Dependencies:
    {', '.join(sorted(internal_deps))}
    """
    
def get_default_filename(summary_level: SummaryLevel, is_notebook: bool = False) -> str:
    """Get the default base filename based on output type and summary level"""
    if is_notebook:
        return "colab_ready"  # Always full code for notebooks
        
    summary_level_names = {
        SummaryLevel.INTERFACE: "signatures_only",
        SummaryLevel.CORE: "essential_code",
        SummaryLevel.NONE: "complete_code"
    }
    return summary_level_names[summary_level]

def process_cli_args(args: Optional[List[str]] = None) -> dict:
    """Process command line arguments and return a config dict for ChimeraCat"""
    parser = create_cli_parser()
    parsed_args = parser.parse_args(args)

    # Convert summary level string to enum
    summary_level = getattr(SummaryLevel, parsed_args.summary_level.upper())

    # Build config dict
    config = {
        'src_dir': parsed_args.src_dir,
        'summary_level': summary_level,
        'exclude_patterns': parsed_args.exclude,
        'remove_disconnected_deps': parsed_args.remove_disconnected,
        'generate_report': parsed_args.report,
        'debug': parsed_args.debug,
        'debug_str': parsed_args.debug_prefix if parsed_args.debug else ""
    }

    return config, parsed_args

def cli_main(args: Optional[List[str]] = None) -> int:
    """Main CLI entry point for ChimeraCat"""
    try:
        config, args = process_cli_args(args)
        
        # Create ChimeraCat instance for Python output (with summarization)
        cat = ChimeraCat(**config)
        
        # Get base filename from argument or generate default
        base_filename = args.output
        
        # Handle output based on type
        if args.output_type in ('py', 'both'):
            py_filename = f"{base_filename or get_default_filename(config['summary_level'])}.py"
            py_file = cat.generate_concat_file(py_filename)
            print(f"Generated Python file: {py_file}")
            
        if args.output_type in ('ipynb', 'both'):
            # Create new instance with NONE summary level for notebook
            # Maintain report setting from CLI args
            notebook_cat = ChimeraCat(
                **{**config, 'summary_level': SummaryLevel.NONE}
            )
            nb_filename = f"{base_filename or get_default_filename(summary_level=SummaryLevel.NONE, is_notebook=True)}.ipynb"
            nb_file = notebook_cat.generate_colab_notebook(nb_filename)
            print(f"Generated Jupyter notebook (complete code): {nb_file}")
            
        # If debug is enabled, show additional information regardless of report setting
        if args.debug:
            print("\nDebug Report:")
            print(cat.get_dependency_report())
            
        return 0
        
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        if args.debug:
            import traceback
            traceback.print_exc()
        return 1

def create_cli_parser() -> argparse.ArgumentParser:
    """Create the command-line argument parser for ChimeraCat"""
    parser = argparse.ArgumentParser(
        prog='ccat',
        description="""
    ChimeraCat (ccat) - The smart code concatenator
     /\\___/\\   
    ( o   o )  Intelligently combines Python source files
    (  =^=  )  while maintaining dependencies and readability
     (______)  
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        'src_dir',
        type=str,
        nargs='?',
        default='src',
        help='Source directory containing Python files (default: src)'
    )

    parser.add_argument(
        '-s', '--summary-level',
        type=str,
        choices=['interface', 'core', 'none'],
        default='none',
        help='Code summarization level (for .py output only, default: none)'
    )

    parser.add_argument(
        '-e', '--exclude',
        type=str,
        nargs='+',
        help='Patterns to exclude from processing (e.g., "test" "temp")'
    )

    parser.add_argument(
        '-o', '--output',
        type=str,
        help='Output file name (without extension, default: based on output type and summary level)'
    )

    parser.add_argument(
        '-t', '--output-type',
        type=str,
        choices=['py', 'ipynb', 'both'],
        default='both',
        help='Output file type (default: both)'
    )

    parser.add_argument(
        '-r', '--report',
        action='store_true',
        default=None,
        help='Generate dependency report and ASCII visualization. By default, reports are '
            'included for interface/core summary levels and excluded for complete code '
            'and notebooks. This flag overrides that behavior.'
    )

    # Add a no-report option for when you want to suppress reports in INTERFACE/CORE
    parser.add_argument(
        '--no-report',
        action='store_false',
        dest='report',
        help='Suppress dependency report generation even for interface/core summary levels'
    )

    parser.add_argument(
        '--remove-disconnected',
        action='store_true',
        help='Remove modules with no dependencies from visualization'
    )

    parser.add_argument(
        '-d', '--debug',
        action='store_true',
        help='Enable debug output'
    )

    parser.add_argument(
        '--debug-prefix',
        type=str,
        default='CCAT:',
        help='Prefix for debug messages (default: CCAT:)'
    )

    parser.add_argument(
        '--version',
        action='version',
        version=f'%(prog)s {ccat_version}'
    )

    return parser


if __name__ == "__main__":
    debug = True
    generate_report = True
    # Example with different summary levels for Python output
    examples = {
        SummaryLevel.INTERFACE: "signatures_only.py",
        SummaryLevel.CORE: "essential_code.py",
        SummaryLevel.NONE: "complete_code.py",
    }
    
    for level, filename in examples.items():
        cat = ChimeraCat(
            "src", 
            exclude_patterns=["tools\\", ".ipynb", "cats\\"], 
            summary_level=level, 
            debug=debug, 
            debug_str="DBG: ", 
            remove_disconnected_deps=True,
            generate_report=generate_report
        )
        output_file = cat.generate_concat_file(filename)
        print(f"Generated {level.value} version: {output_file}")
    
    # Generate notebook with complete code
    cat = ChimeraCat(
        "src", 
        exclude_patterns=["tools\\", ".ipynb", "cats\\"], 
        remove_disconnected_deps=True,
    )
    output_file = cat.generate_colab_notebook("colab_ready.ipynb")
    print(f"Generated notebook version: {output_file}")

    if debug:
        cat.visualize_dependencies("module_deps.png")
        if generate_report:
            report = cat.get_dependency_report()
            print(report)