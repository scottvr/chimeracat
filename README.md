# ccat
ccat - ChimeraCat smart code concatenator
----------------------------------

### What is it?
ChimeraCat emerged as an ancillary utility for some larger work I was 
doing with the help of Claude 3.5 Sonnet (New) in October 2024.
It has grown and evolved quite a bit in the short time since it was born.
It gave birth to offspring too: (PHART)[https://github.com/scottvr/PHART]

ChimeraCat (ccat for short):

- Analyzes Python files for imports and definitions
- Builds a dependency graph
- Generates both a single .py file and a Colab notebook
- Handles internal vs external imports
- Avoids duplicate definitions
- Creates a clean, organized output

### How to use it

QuickStart:

```python
from ChimeraCat import ChimeraCat

# Generate both notebook and Python file
concat = ChimeraCat("src")
notebook_file = concat.generate_colab_notebook()
py_file = concat.generate_concat_file()
```

### Features Claude is particularly proud of:

- Dependency ordering using NetworkX
- Duplicate prevention
- Clean handling of internal vs external imports
- Automatic notebook generation
- Maintains code readability with section headers

### Advanced Usage:

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

**debug: bool = False**

    if this is False, _debug_print() messages are elided

**debug_str = ""**

   if debug is True, if debug_str is set, messages printed 
   will be prefaced with this string to aid in eyeballing 
   or grepping program stdout/stderr output.
