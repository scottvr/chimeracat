"""
### TODO:
# cli
#   srcdir args
#   summarization level
#   colab
#   exclusions
#   other patterns

ChimeraCat arose as an ancillary utility for some larger work I was 
doing with the help of Claude 3.5 Sonnet (New) in October 2024 

This utility:

Analyzes Python files for imports and definitions
Builds a dependency graph
Generates both a single .py file and a Colab notebook
Handles internal vs external imports
Avoids duplicate definitions
Creates a clean, organized output

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
"""

import re
from pathlib import Path
from typing import List, Set, Dict
import networkx as nx
from dataclasses import dataclass
from datetime import datetime

from enum import Enum
from typing import Dict, List, Set, Optional, Pattern
import re
from dataclasses import dataclass, field
from datetime import datetime
from phart import ASCIIRenderer, LayoutOptions, NodeStyle    

from enum import Enum
from typing import Dict, List, Set, Optional, Pattern
import re
from dataclasses import dataclass, field
from datetime import datetime

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
             debug: bool = False,
             remove_disconnected_deps: bool = False,
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

    def _debug_print(self, *args, **kwargs):
        """Helper for debug output"""
        if self.debug:
            print(f"{self.debug_str}: {args} {list(kwargs.items())}")

    def should_exclude(self, file_path: Path) -> bool:
        """Check if a file should be excluded from processing"""
        # Always exclude self
        if file_path.resolve() == self.self_path:
            return True
            
        # Check against exclude patterns
        str_path = str(file_path)
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
            print("removing disconnected imports (no dependent relationship)")
            print(display_graph)
            display_graph.remove_nodes_from(list(nx.isolates(display_graph)))
            print(display_graph)

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
{"non-dependent modules elided" if self.remove_disconnected_deps else "node names detached from the network and printed in isolation are non-connected/likely unused."}
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
    
def main():
    debug = True
    # Example with different summary levels
    examples = {
        SummaryLevel.INTERFACE: "signatures_only.py",
        SummaryLevel.CORE: "essential_code.py",
        SummaryLevel.NONE: "complete_code.py",
    }
    
    for level, filename in examples.items():
        cat = ChimeraCat("src", exclude_patterns=["tools/", "*.ipynb", "cats/"], summary_level=level, debug=debug)
        output_file = cat.generate_concat_file(filename)
        print(f"Generated {level.value} version: {output_file}")
    
    cat = ChimeraCat("src", exclude_patterns=["tools/", "*.ipynb", "cats/"], summary_level=SummaryLevel.NONE, debug=debug)
    output_file = cat.generate_colab_notebook()
    print(f"Generated colab notebook  version: {output_file}")

    if debug:
        cat.visualize_dependencies("module_deps.png")
        # Get detailed report
        #report = cat.generate_dependency_ascii()
        #print(report)
        report = cat.get_dependency_report()
        print(report)
        # Generate visualization


if __name__ == "__main__":
    main()
