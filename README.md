# ccat
ChimeraCat - summarizing code concatenator
----------------------------------

### What is it?
ChimeraCat emerged as an ancillary utility for some larger work I was 
doing with the help of Claude 3.5 Sonnet (New) in October 2024.
Initially a quick and dirty code concatenator to output ipynb files from multiple py files, it has grown and evolved quite a bit in the short time since it was born.


It now serves the original purpose of concatenation, and another use case that naturally evolved from collaborating with an LLM, that of summarizing to reduce (in some cases drastically) the size of the file, while aiming to retain as much relevant information as possible.  

It does so by analysing the files to determine the best order to concatenate them in, and to eliminated duplicates and perpetual recursive import loops. In addition it can strip boilerplate code and make other intelligent choices about what to leave out, and the heuristics are fully user defineable via custom configuration, also done in Python. 

Incidentally, ChimeraCat's reporting on the dependency graph it creates (using NetworkX) gave rise to the need for a text-based diagrammer for NetworkX Graphs (and GraphViz DOT or GraphML files to boot!), resulting in the birth of  the Python Heirarchical ASCII Rendering Tool. [PHART](https://github.com/scottvr/PHART)

ChimeraCat (ccat for short):

- Facilitates summarizing larger projects for the purpose of providing code to an LLM, sharing  as much information using as few tokens and sparing as much context memory as possible
- Analyzes Python files for imports and definitions
- Builds a dependency graph
- Generates both a single .py file and a Colab notebook
- Handles internal vs external imports
- Avoids duplicate definitions
- Creates a clean, organized output

### How to use it

# CLI Usage:

If installed via pip, a script in your venv's bin (or .exe in Scripts under Windows) will be generated allowing you to call chimeracat from the command-line as "ccat"

Example usage:
```bash
# Basic usage
ccat src/

# Generate only Python file with interface-level summary
ccat src/ -s interface -t py

# Generate notebook with debugging
ccat src/ -t ipynb -d

# Exclude patterns and specify output
ccat src/ -e "test" "temp" -o combined_output.py
```

## dev QuickStart:

```python
from chimeracat import ChimeraCat

# Generate both notebook and Python file
concat = ChimeraCat("src")
notebook_file = concat.generate_colab_notebook()
py_file = concat.generate_concat_file()
```

## Features Claude is particularly proud of:

- Dependency ordering using NetworkX
- Duplicate prevention
- Clean handling of internal vs external imports
- Automatic notebook generation
- Maintains code readability with section headers

### Additional Developer Info

You can pass to the ChimeraCat constructor any of the following:

   **src_dir: str = "src"**

      defaults to a "./src" directory in the cwd. 
      this is how you'd override that.

   **summary_level: SummaryLevel = SummaryLevel.NONE**

      how hard, if at all, do you want ccat to try 
      to strip the code it finds down to its essentials? 
      valid options are explicit in the SmarryLevel enum.

   **exclude_patterns: List[str] = None**

      this is a list of strings that each file in the 
      src_dir directory will be checked against; 
      if there is a full or partial match, the file will 
      not be scanned. ccat will not scan itself, 
      (that is, the currently executing script filename)
      owing to its origins residing in a tools/ directory 
      of a larger project and tending to clutter up 
      the summary cats.

   **rules: Optional[SummaryRules] = None**

      you can construct a SummaryRules class instance 
      and pass it here if you want to expand on ccat's 
      basic functionality. For applications in a specific 
      domain for example, perhaps you want to remove a 
      rule from the defaults, or there is code that would 
      be considered boilerplate in this domain, but ccat 
      might think it looks interesting. Override the builtins here. 

   **remove_disconnected_deps: bool = False**

      if the app has many imports, but the dependency graph 
      finds to relations between them, by default they are 
      visualized as disconnected nodes. To save space, you 
      may want to omit them from ccat's output by setting 
      this True
 
   **generate_report**

      ChimeraCat tries to take care of this sensibly for you,
      by not cluttering a notebook with report info, but if you
      are using summarization, it includes the report info, 
      assuming your use case is to feed as meaningful code using 
      as little context and as few tokens as possible. But, if you
      are some sort of madman, you can override this behavior

   **debug: bool = False**

      if this is False, _debug_print() messages are elided

   **debug_str = ""**

      if debug is True, if debug_str is set, messages printed 
      will be prefaced with this string to aid in eyeballing 
      or grepping program stdout/stderr output.

### TBD
