# deepchem/deepchem Contributions

Source URL: https://github.com/deepchem/deepchem
Contributor: AshwinSaklecha

## PR #4803 - Add Symbolic Regression Model

Pull request URL: https://github.com/deepchem/deepchem/pull/4803
State: open
Merged at: None

## Description

<!-- Please include a summary of the change and which issue is fixed.
Please also include relevant motivation and context.
List any dependencies that are required for this change. -->
Adds a symbolic regression engine to DeepChem as `SymbolicRegressionModel`, a new `dc.models.Model` subclass.
The engine uses island-model evolutionary search with tournament selection, subtree mutation/crossover, gradient-based constant optimization, algebraic simplification, and Pareto-based model selection to discover interpretable mathematical expressions from data.


## Type of change

Please check the option that is related to your PR.

- [ ] Bug fix (non-breaking change which fixes an issue)
- [x] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
  - In this case, we recommend to discuss your modification on GitHub issues before creating the PR
- [ ] Documentations (modification for documents)

## Checklist

- [x] My code follows [the style guidelines of this project](https://deepchem.readthedocs.io/en/latest/development_guide/coding.html)
  - [x] Run `yapf -i <modified file>` and check no errors (**yapf version must be  0.32.0**)
  - [ ] Run `mypy -p deepchem` and check no errors
  - [x] Run `flake8 <modified file> --count` and check no errors
  - [ ] Run `python -m doctest <modified file>` and check no errors
- [x] I have performed a self-review of my own code
- [x] I have commented my code, particularly in hard-to-understand areas
- [x] I have made corresponding changes to the documentation
- [x] I have added tests that prove my fix is effective or that my feature works
- [x] New unit tests pass locally with my changes
- [x] I have checked my code and corrected any misspellings

## PR #4661 - Implement DeepONet Architecture

Pull request URL: https://github.com/deepchem/deepchem/pull/4661
State: open
Merged at: None

## Description


<!-- Please include a summary of the change and which issue is fixed.
Please also include relevant motivation and context.
List any dependencies that are required for this change. -->

This PR adds DeepONet, a neural network architecture for learning operators that map between input and output functions. The implementation includes the base model, a DeepChem wrapper, and unit tests.


## Type of change

Please check the option that is related to your PR.

- [ ] Bug fix (non-breaking change which fixes an issue)
- [x] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
  - In this case, we recommend to discuss your modification on GitHub issues before creating the PR
- [ ] Documentations (modification for documents)

## Checklist

- [x] My code follows [the style guidelines of this project](https://deepchem.readthedocs.io/en/latest/development_guide/coding.html)
  - [x] Run `yapf -i <modified file>` and check no errors (**yapf version must be  0.32.0**)
  - [x] Run `mypy -p deepchem` and check no errors
  - [x] Run `flake8 <modified file> --count` and check no errors
  - [x] Run `python -m doctest <modified file>` and check no errors
- [x] I have performed a self-review of my own code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [x] I have made corresponding changes to the documentation
- [x] I have added tests that prove my fix is effective or that my feature works
- [x] New unit tests pass locally with my changes
- [x] I have checked my code and corrected any misspellings

## PR #4576 - Add DataLoader tutorial

Pull request URL: https://github.com/deepchem/deepchem/pull/4576
State: open
Merged at: None

## Description

This PR adds a new DataLoader tutorial notebook. It covers CSVLoader, SDFLoader, featurization, multitask loading, and dataset sharding, starting from a simple example and moving to real datasets. This tutorial fills a gap mentioned in the DeepChem tutorial wishlist, since DeepChem does not currently have a DataLoader-focused tutorial.

There is no linked issue for this PR.


## Type of change

Please check the option that is related to your PR.

- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
  - In this case, we recommend to discuss your modification on GitHub issues before creating the PR
- [x] Documentations (modification for documents)

## Checklist

- [ ] My code follows [the style guidelines of this project](https://deepchem.readthedocs.io/en/latest/development_guide/coding.html)
  - [ ] Run `yapf -i <modified file>` and check no errors (**yapf version must be  0.32.0**)
  - [ ] Run `mypy -p deepchem` and check no errors
  - [ ] Run `flake8 <modified file> --count` and check no errors
  - [ ] Run `python -m doctest <modified file>` and check no errors
- [x] I have performed a self-review of my own code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New unit tests pass locally with my changes
- [ ] I have checked my code and corrected any misspellings

## PR #4560 - fix: Correct spelling 'vectures' to 'vectors' throughout codebase

Pull request URL: https://github.com/deepchem/deepchem/pull/4560
State: open
Merged at: None

## Description

Fix typo “vectures” → “vectors” in docstrings and documentation.  
No related issue.

## Type of change

- [x] Documentations (modification for documents)

## Checklist

- [x] My code follows [the style guidelines of this project](https://deepchem.readthedocs.io/en/latest/development_guide/coding.html)
- [x] I have performed a self-review of my own code
- [x] I have checked my code and corrected any misspellings
