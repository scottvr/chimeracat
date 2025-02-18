# ChimeraCat: 
Intelligent code concatenator and summarizer

----
## What does it do?
ChimeraCat (ccat) analyzes Python codebases to generate consolidated files optimized for LLM processing,
with configurable summarization to reduce token usage while preserving key information in the code. It was originally to smartly concatenate multiple files from a python lib in development into a single notebook for testing in Colab, then I realized its fitness to the sharing-code-with-an-LLM purpose. 

Now includes cli `ccat` with all configuration exposed as command-line arguments, so it's ready to use without any development on your part. Just `pip install git+https://github.com/scottvr/chimeracat` into your venv.

## Key Features:
- Analyzes Python files for imports and definitions
- Builds dependency graphs using NetworkX
- Displays graph visually as a DAG using ASCII via [PHART](https://github.com/scottvr/PHART)
- Generates both .py files and Colab notebooks
- Smart handling of internal/external imports
- Configurable code summarization

## General Dependency and Interface mapping

If you aren't trying to save on token and conserve context memory when pairing with an LLM, you may still find ChimeraCat's reporting functionality useful.

### CLI report generation example:
```bash
ccat --report-only --elide-disconnected --numeric-labels ..\ASSET\stemprover\src > ccat-report.stemprover.txt
```
<details>
<summary>Example output from above command</summary>

```
Dependency Analysis Report
=========================

Directory Structure:
stemprover\__init__.py
stemprover\analysis\base.py
stemprover\analysis\spectral.py
stemprover\analysis\artifacts\base.py
stemprover\analysis\artifacts\high_freq.py
stemprover\analysis\artifacts\preprocessor.py
stemprover\analysis\selection\metrics.py
stemprover\analysis\selection\segment_finder.py
stemprover\analysis\selection\__init__.py
stemprover\common\audio_utils.py
stemprover\common\math_utils.py
stemprover\common\spectral_utils.py
stemprover\common\types.py
stemprover\common\__init__.py
stemprover\core\audio.py
stemprover\core\config.py
stemprover\core\types.py
stemprover\enhancement\base.py
stemprover\enhancement\controlnet.py
stemprover\enhancement\training.py
stemprover\io\audio.py
stemprover\preparation\base.py
stemprover\preparation\segments\generator.py
stemprover\preparation\segments\__init__.py
stemprover\separation\base.py
stemprover\separation\spleeter.py
stemprover\training\dataset.py
stemprover\training\pairs.py

Import Summary:

    External Dependencies:
    abc, common.audio_utils, common.types, core.audio, core.types, dataclasses, datetime, enum, json, librosa, matplotlib.pyplot as plt, numpy as np, pathlib, soundfile as sf, spleeter.separator, stemprover.common.audio_utils, stemprover.common.spectral_utils, stemprover.common.types, stemprover.core.audio, stemprover.core.config, stemprover.core.types, stemprover.enhancement.controlnet, tensorflow as tf, torch, torch.nn as nn, torch.nn.functional as F, torch.utils.data, typing
    
    Internal Dependencies:
    ...common.audio_utils, ...common.types, ...core.audio, ...core.types, ..analysis.spectral, ..common.audio_utils, ..common.math_utils, ..common.types, ..core.audio, ..core.types, ..io.audio, .analysis.base, .analysis.spectral, .audio, .audio_utils, .base, .core.types, .math_utils, .metrics, .preparation.segments, .separation.base, .separation.spleeter, .spectral_utils, .types
    

Module Statistics:
Total modules: 28
Total dependencies: 19

Module Dependencies:
-------------------

PHART Module Dependency Graph Visualization (see legend below):

            [1]    [23]    [25]    [7]    [8]    [9]
             |      |       |       |      |      |
             v      v       v       v      v      v
      [10]<---[12]--+-[13]--+-[15]--->[16]--->[17]+-->[19]






Legend:
1: ..\ASSET\stemprover\src\stemprover\__init__.py
2: ..\ASSET\stemprover\src\stemprover\analysis\base.py
3: ..\ASSET\stemprover\src\stemprover\analysis\spectral.py
4: ..\ASSET\stemprover\src\stemprover\analysis\artifacts\base.py
5: ..\ASSET\stemprover\src\stemprover\analysis\artifacts\high_freq.py
6: ..\ASSET\stemprover\src\stemprover\analysis\artifacts\preprocessor.py
7: ..\ASSET\stemprover\src\stemprover\analysis\selection\metrics.py
8: ..\ASSET\stemprover\src\stemprover\analysis\selection\segment_finder.py
9: ..\ASSET\stemprover\src\stemprover\analysis\selection\__init__.py
10: ..\ASSET\stemprover\src\stemprover\common\audio_utils.py
11: ..\ASSET\stemprover\src\stemprover\common\math_utils.py
12: ..\ASSET\stemprover\src\stemprover\common\spectral_utils.py
13: ..\ASSET\stemprover\src\stemprover\common\types.py
14: ..\ASSET\stemprover\src\stemprover\common\__init__.py
15: ..\ASSET\stemprover\src\stemprover\core\audio.py
16: ..\ASSET\stemprover\src\stemprover\core\config.py
17: ..\ASSET\stemprover\src\stemprover\core\types.py
18: ..\ASSET\stemprover\src\stemprover\enhancement\base.py
19: ..\ASSET\stemprover\src\stemprover\enhancement\controlnet.py
20: ..\ASSET\stemprover\src\stemprover\enhancement\training.py
21: ..\ASSET\stemprover\src\stemprover\io\audio.py
22: ..\ASSET\stemprover\src\stemprover\preparation\base.py
23: ..\ASSET\stemprover\src\stemprover\preparation\segments\generator.py
24: ..\ASSET\stemprover\src\stemprover\preparation\segments\__init__.py
25: ..\ASSET\stemprover\src\stemprover\separation\base.py
26: ..\ASSET\stemprover\src\stemprover\separation\spleeter.py
27: ..\ASSET\stemprover\src\stemprover\training\dataset.py
28: ..\ASSET\stemprover\src\stemprover\training\pairs.py
(non-dependent modules elided from visualization)



Dependency Chains:
-----------------
1. stemprover\__init__.py
2. stemprover\analysis\base.py
3. stemprover\analysis\spectral.py
4. stemprover\analysis\artifacts\base.py
5. stemprover\analysis\artifacts\high_freq.py
6. stemprover\analysis\artifacts\preprocessor.py
7. stemprover\analysis\selection\metrics.py
8. stemprover\analysis\selection\segment_finder.py
9. stemprover\analysis\selection\__init__.py
10. stemprover\common\math_utils.py
11. stemprover\common\__init__.py
12. stemprover\enhancement\base.py
13. stemprover\enhancement\training.py
14. stemprover\io\audio.py
15. stemprover\preparation\base.py
16. stemprover\preparation\segments\generator.py
17. stemprover\preparation\segments\__init__.py
18. stemprover\separation\base.py
19. stemprover\separation\spleeter.py
20. stemprover\training\dataset.py
21. stemprover\training\pairs.py
22. stemprover\enhancement\controlnet.py
 Depends on: stemprover\__init__.py
23. stemprover\common\spectral_utils.py
 Depends on: stemprover\analysis\selection\segment_finder.py
24. stemprover\core\audio.py
 Depends on: stemprover\__init__.py, stemprover\analysis\selection\metrics.py, stemprover\analysis\selection\segment_finder.py, stemprover\analysis\selection\__init__.py, stemprover\preparation\segments\generator.py
25. stemprover\common\types.py
 Depends on: stemprover\analysis\selection\segment_finder.py, stemprover\preparation\segments\generator.py
26. stemprover\common\audio_utils.py
 Depends on: stemprover\analysis\selection\segment_finder.py, stemprover\preparation\segments\generator.py
27. stemprover\core\config.py
 Depends on: stemprover\separation\base.py
28. stemprover\core\types.py
 Depends on: stemprover\__init__.py, stemprover\analysis\selection\metrics.py, stemprover\analysis\selection\segment_finder.py, stemprover\analysis\selection\__init__.py, stemprover\core\config.py, stemprover\preparation\segments\generator.py, stemprover\separation\base.py

Module Details:
-------------

stemprover\__init__.py:
Classes: None
Functions: None
Imports: stemprover.core.types, .separation.base, .analysis.base, .separation.spleeter, stemprover.core.audio, .analysis.spectral, stemprover.enhancement.controlnet

stemprover\analysis\base.py:
Classes: VocalAnalyzer, for
Functions: __init__, analyze, _create_spectrograms
Imports: abc, numpy as np, pathlib, ..core.audio

stemprover\analysis\spectral.py:
Classes: SpectralAnalyzer
Functions: __init__, _create_spectrogram, _analyze_differences, analyze, _save_comparison, _plot_spectrogram, _save_analysis
Imports: ..common.types, typing, ..common.math_utils, json, ..core.audio, datetime, pathlib, ..core.types, matplotlib.pyplot as plt, ..common.audio_utils

stemprover\analysis\artifacts\base.py:
Classes: SignalProcessor, class, from, HybridProcessor, for, ArtifactProcessor, ControlNetProcessor
Functions: __init__, validate, run_validation, as_dict, _calculate_snr, _analyze_frequency_response, _measure_phase_coherence, process, _bandpass_filter
Imports: typing, torch.nn as nn, abc, torch, ...common.audio_utils, pathlib, ...common.types, numpy as np, dataclasses

stemprover\analysis\artifacts\high_freq.py:
Classes: HighFrequencyArtifactPreprocessor
Functions: forward, __init__, generate_training_pair
Imports: None

stemprover\analysis\artifacts\preprocessor.py:
Classes: HighFrequencyArtifactPreprocessor
Functions: forward, __init__, generate_training_pair
Imports: None

stemprover\analysis\selection\metrics.py:
Classes: from, class, MetricsCalculator
Functions: __init__, _calculate_detailed_score, calculate_sdr, calculate_metrics, calculate_band_sdrs
Imports: stemprover.core.types, typing, stemprover.core.audio, numpy as np, dataclasses

stemprover\analysis\selection\segment_finder.py:
Classes: from, TestSegmentFinder
Functions: __init__, find_best_segments, _compute_score, analyze_segment, _calculate_transitions, _calculate_high_freq_content, _calculate_vocal_clarity
Imports: stemprover.core.types, typing, stemprover.common.types, stemprover.core.audio, numpy as np, stemprover.common.audio_utils, stemprover.common.spectral_utils, .metrics, librosa, dataclasses

stemprover\analysis\selection\__init__.py:
Classes: None
Functions: None
Imports: stemprover.core.types, stemprover.core.audio

stemprover\common\audio_utils.py:
Classes: None
Functions: get_frequency_bins, get_band_mask, calculate_phase_complexity, calculate_dynamic_range, to_mono, create_spectrogram, calculate_onset_variation
Imports: .math_utils, numpy as np, .types, soundfile as sf, librosa

stemprover\common\math_utils.py:
Classes: None
Functions: magnitude, db_scale, phase_difference, phase_coherence, rms, angle
Imports: .types, numpy as np

stemprover\common\spectral_utils.py:
Classes: None
Functions: calculate_band_energy
Imports: typing, .audio_utils, numpy as np, .types, soundfile as sf, librosa

stemprover\common\types.py:
Classes: None
Functions: None
Imports: librosa, typing, numpy as np, torch

stemprover\common\__init__.py:
Classes: None
Functions: None
Imports: .math_utils, .spectral_utils, .types, .audio_utils

stemprover\core\audio.py:
Classes: import, class, for
Functions: is_mono, to_mono, duration_seconds, is_stereo
Imports: librosa, typing, numpy as np, dataclasses

stemprover\core\config.py:
Classes: from, SeparatorBackend, class
Functions: None
Imports: stemprover.core.types, enum, typing, pathlib, dataclasses

stemprover\core\types.py:
Classes: from, for, class
Functions: hop_samples, segment_samples
Imports: typing, pathlib, matplotlib.pyplot as plt, .audio, dataclasses

stemprover\enhancement\base.py:
Classes: for, EnhancementProcessor
Functions: __init__, enhance, validate
Imports: abc, typing, ...core.types, ...core.audio

stemprover\enhancement\controlnet.py:
Classes: PhaseAwareControlNet, PhaseAwareZeroConv, ArtifactDetector
Functions: forward, __init__
Imports: torch.nn as nn, typing, torch

stemprover\enhancement\training.py:
Classes: ArtifactDataset, ControlNetTrainer
Functions: __init__, validate, load_checkpoint, train, train_step, __len__, save_checkpoint, frequency_loss, prepare_training, __getitem__
Imports: torch.nn.functional as F, torch.utils.data

stemprover\io\audio.py:
Classes: None
Functions: save_audio_file, load_audio_file
Imports: librosa, typing, ..core.audio, pathlib, soundfile as sf, numpy as np

stemprover\preparation\base.py:
Classes: None
Functions: None
Imports: None

stemprover\preparation\segments\generator.py:
Classes: from, TrainingSegmentGenerator
Functions: _create_backing_combinations, __init__, generate_segments, _has_vocal_content
Imports: typing, core.audio, common.types, torch.utils.data, common.audio_utils, core.types, pathlib, numpy as np, dataclasses

stemprover\preparation\segments\__init__.py:
Classes: None
Functions: None
Imports: None

stemprover\separation\base.py:
Classes: class, from, VocalSeparator, StemProcessor, for
Functions: cleanup, __init__, process_stems, _separate_vocals, __enter__, _apply_controlnet_enhancement, _load_stereo_pair, __exit__, separate_and_analyze, _save_audio_files
Imports: stemprover.core.types, enum, typing, stemprover.core.config, abc, ..core.audio, pathlib, ..core.types, dataclasses

stemprover\separation\spleeter.py:
Classes: from, class, SpleeterSeparator
Functions: cleanup, __init__, capabilities, separate, _load_mono, _separate_vocals, _load_stereo_pair, _setup_tensorflow, separate_and_analyze, separate_file, _save_audio_files
Imports: typing, .base, ..analysis.spectral, spleeter.separator, ..core.audio, datetime, pathlib, ..core.types, ..io.audio, numpy as np, dataclasses, tensorflow as tf

stemprover\training\dataset.py:
Classes: TrainingDataset
Functions: __getitem__, __init__, __len__
Imports: typing, torch.utils.data, .preparation.segments, .core.types

stemprover\training\pairs.py:
Classes: None
Functions: None
Imports: None
```
</details>

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
    
- elide_disconnected_deps: When True, omit modules with no dependencies
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
        elide_disconnected_deps=True
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
            [--elide-disconnected] [-d] [--debug-prefix DEBUG_PREFIX] [--version]
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
  --elide-disconnected
                        Remove modules with no dependencies from visualization
  -d, --debug           Enable debug output
  --debug-prefix DEBUG_PREFIX
                        Prefix for debug messages (default: CCAT:)
  --version             show program's version number and exit
```

"""
