# 粤见非遗 · 2026 Editorial UI

This branch refreshes the Streamlit user experience without changing retrieval, model routing, generation, revision, session-state or export logic.

## Visual concept

A modern digital Lingnan cultural atelier: paper-white surfaces, mineral green, cinnabar accents, restrained typography and museum-inspired editorial composition.

- **Palette:** ink `#202d29`, forest `#24493d`, ivory `#f7f5ef`, cinnabar `#a84937`, ochre `#bb9861`.
- **Typography:** a Chinese serif heading stack, accessible system sans-serif body.
- **Layout:** immersive local-art hero, five scene selectors, guided prompt composition, context panel, result tabs, download and revision panels.
- **Motion & accessibility:** keyboard focus outlines, semantic hero/empty-state sections, image alt text, responsive breakpoints and reduced-motion fallback.
- **Assets:** reuse `assets/readme_hero_lingnan.png` rather than introducing external image requests.

## Architecture

- `ui/editorial_styles.py`: isolated design tokens and responsive override CSS, applied after the existing styles.
- `ui/components.py`: header, hero, shared headings, and empty-result canvas.
- `ui/workspace.py`: scene selection and guided request composition.
- `ui/sidebar.py`: cultural atelier identity and clearer sidebar labels.
- `ui/results.py`: editorial copy for result, revisions and downloads.
- `.streamlit/config.toml`: matching Streamlit base theme.
- `app.py`: stylesheet registration and product footer.

All original widget keys and task objects remain intact. Navigation still triggers Streamlit state updates. Existing endpoints and config remain unchanged.

## Preview & QA

Run `streamlit run app.py` and inspect 1440px, 1024px, 768px and 390px widths. Check switching all five scenes, loading example prompts, changing city/time/identity, result tab views, revision history, downloads and personal API setup.

Automated checks: `ruff check .`, `python -m compileall -q .`, `pytest`.

This is a styling and information-architecture update, not a migration from Streamlit to React.
