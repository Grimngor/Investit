# GitHub Copilot Instructions for the InvestIt Project

## Python

- Write **clean, minimal, and consistent** code that matches existing naming conventions and project structure.
- Follow **PEP 8** for formatting and style.
- Use **type hints** for all function signatures and class attributes.
- Keep code **self-explanatory**; use comments only where intent isn’t obvious.
- Add a **one-line docstring** to every public function, method, and class.
- Name **local variables short** and **module-level variables descriptive**.
- Include **unit tests** for all new features and major changes.
- If you create new terminals make sure to activate the **virtual environment** before installing anything, and don't create a new one if an existing one is already active.
- Respect my preference for **Black formatter** and **140 character line length** in Python.

## Frontend Best Practices (Vue + CSS)

### Styling Principles
- Keep **component styles co-located**: use `<style scoped>` or CSS Modules inside each `.vue`.
- Extract only **shared or global elements**:
  - Design tokens (colors, spacing, typography)
  - Mixins / utilities
  - Reset / base styles
- Avoid large global CSS files or deep selectors.

### Scaling & Performance
- Utility-first frameworks (Tailwind, UnoCSS) reduce manual CSS.
- Use CSS variables for theming; toggle with root or body classes.
- Vite extracts CSS automatically; no performance penalty for scoped styles.
- Purge or tree-shake unused styles in production.
