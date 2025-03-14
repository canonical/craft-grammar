*********
Changelog
*********

2.0.3 (2024-03-14)
------------------

- Fix grammar validation to ensure compatibility with python 3.13

2.0.2 (2024-03-07)
------------------

- Fix handling of multi-entry dictionaries after a grammar statement

2.0.1 (2024-08-18)
------------------

- Fix cases where models were not correctly coercing numbers to strings.

2.0.0 (2024-08-08)
------------------

Breaking changes:

- Migrate to Pydantic 2
- Generic grammar types
- Make minimum Python version 3.10

Features:
- Add create_grammar_model() function to make a pydantic model grammar-aware

1.2.0 (2024-04-05)
------------------

- Add more grammar types

1.1.2 (2023-11-30)
------------------

- Include type information

1.1.1 (2022-02-28)
------------------

- Fix models for grammar validation

1.1.0 (2022-02-24)
------------------

- Introduce grammar aware Pydantic Models that deprecate the use of try

1.0.0 (2022-02-16)
------------------

- Initial import from Snapcraft
- Initial packaging
- Code updated to follow latest development practices
