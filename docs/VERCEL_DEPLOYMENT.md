# Vercel production deployment

The repository root is a Vercel Services project configured by `vercel.json`:

- `frontend` builds `web/` (Next.js).
- `backend` builds `backend/` (FastAPI) with `/api/v1/*` mounted under `/api`.
- Both are exposed under one Vercel URL. No second public API domain is required.

The backend package contains a deployable snapshot of the original `api/`, `core/`, `services/` and `data/` modules. Whenever those canonical modules change, synchronize the backend mirrors in the same commit so web and server stay consistent.

Platform AI is optional. Without `OPENAI_API_KEY`, the website renders and users can choose to supply their own API through the current page's Settings. To offer platform-backed generation, configure `OPENAI_API_KEY` as a **server-side encrypted Vercel environment variable**, together with `OPENAI_BASE_URL` and `MODEL_NAME` if needed. Never store personal keys in `NEXT_PUBLIC_*`.

Public production traffic should have authentication or quota-based protection before funding shared AI usage. The in-process development limiter does not provide distributed protection across serverless instances. Dynamic venue details remain subject to verification.

Check `/`, `/studio`, and `/api/v1/status` after deployment; then run a BYOK or owner-funded test for actual generation, revision, and export.
