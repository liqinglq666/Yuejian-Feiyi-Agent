# Yuejian Next.js / FastAPI Migration

## Migration strategy

The existing Streamlit app remains at `app.py` for backward compatibility. Production web entry is `web/`. The model, retrieval, prompts, validation, revision planner and exporters remain Python modules called from `api/main.py`.

## UI / UX system

- Visual narrative: archive-inspired museum site with mineral green, warm paper surfaces, cinnabar accent, elegant serif headings and generous whitespace.
- Brand landing page: immersive hero, five discovery experiences, city index, three-step process, conversion to studio.
- Studio: five scene categories in a dedicated sidebar, textarea and guided sample prompts, city/time/identity/style/interest controls, SSE-generation status, markdown report tabs, historical plans, revision actions, export.
- Mobile: collapsible sidebar, stacked composer, sticky-free compact navigation, scrollable results tabs, 390px layout breakpoint.
- Accessibility: keyboard focus outlines, labelled form fields, semantic sections, aria live progress, alt description, reduced motion preferences.

## Security and behavior

- Request-specific BYOK secrets are never returned in responses, persisted in server/session storage or included in exports.
- API payloads use Pydantic constraints; the established model gateway validates service URL to protect against local/private network SSRF.
- SSE streams use same-origin Next rewrite, no browser cross-origin dependency.
- Basic per-process rate limiting is deliberately scoped to preview use; use gateway-level/shared controls at scale.
- React Markdown is rendered with default HTML escaping (`skipHtml`), not raw unsafe HTML rendering.
- Existing source citations and factual safeguards remain within the Python prompt builder.

## Operations

Vercel/Next app root: `web`. Python API deploy root: repository root. Static visual asset is copied at git-object level from existing `assets/readme_hero_lingnan.png`.

For public production deployment, further recommended: identity, quotas, request-size gateway limits, shared rate limiting, observability, security headers and end-to-end tests against a staging AI gateway.
