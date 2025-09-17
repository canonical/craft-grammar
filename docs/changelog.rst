Changelog
=========

.. changelog template:

  .. _release-X.Y.Z:

  X.Y.Z (YYYY-MM-DD)
  ------------------

  New features:

  Bug fixes:

  Documentation:

  For a complete list of commits, check out the `X.Y.Z`_ release on GitHub.

.. _release 2.3.0:

2.3.0 (2025-09-17)
------------------

New features:

- The ``checker`` option for ``GrammarProcessor`` is now optional.
- Add ``any`` as an always-available platform for ``for`` grammar that is always
  true.
- Add ``valid_platforms`` and ``valid_architectures`` optional arguments to
  ``GrammarProcessor`` to allow validation of platforms and architectures listed in
  the grammar.
- Add a legal ``else`` clause to ``for`` grammar.
- An app using ``GrammarProcessor`` can choose a specific grammar variant.

For a complete list of commits, check out the `2.3.0`_ release on GitHub.

.. _release 2.2.0:

2.2.0 (2025-08-26)
------------------

New features:

- Add a validator for the ``for`` statement in Grammar models.

For a complete list of commits, check out the `2.2.0`_ release on GitHub.

.. _release 2.1.0:

2.1.0 (2025-08-13)
------------------

New features:

- Add a new ``for`` statement to select against a platform.

For a complete list of commits, check out the `2.1.0`_ release on GitHub.

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

.. _2.1.0: https://github.com/canonical/craft-grammar/releases/tag/2.1.0
.. _2.2.0: https://github.com/canonical/craft-grammar/releases/tag/2.2.0
.. _2.3.0: https://github.com/canonical/craft-grammar/releases/tag/2.3.0
