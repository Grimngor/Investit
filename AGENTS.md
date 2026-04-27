# Instructions for the InvestIt Project

## Python

- Write clean, minimal, and consistent code that matches existing naming conventions and project structure.
- Follow PEP 8 for formatting and style.
- Use type hints for all function signatures and class attributes.
- Keep code self-explanatory; use comments only where intent is not obvious.
- Add a one-line docstring to every public function, method, and class.
- Name local variables short and module-level variables descriptive.
- Include unit tests for all new features and major changes.
- If you create new terminals, activate the existing virtual environment before installing anything and do not create a new one if one is already active.
- Respect the project preference for Ruff formatter, tabs for indentation, and 140 character line length in Python.

## Frontend Best Practices (Vue + CSS)

### Styling Principles

- Keep component styles co-located with `<style scoped>` or CSS Modules inside each `.vue`.
- Extract only shared or global elements:
  - Design tokens
  - Mixins and utilities
  - Reset and base styles
- Avoid large global CSS files or deep selectors.

### Scaling And Performance

- Utility-first frameworks such as Tailwind or UnoCSS can reduce manual CSS.
- Use CSS variables for theming and toggle with root or body classes.
- Vite extracts CSS automatically; scoped styles do not add a production performance penalty.
- Purge or tree-shake unused styles in production.
