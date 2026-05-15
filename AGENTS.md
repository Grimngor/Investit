# Instructions for the InvestIt Project

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
