# Wdrożenie na Vercel

Dwa projekty Vercel z jednego repozytorium + baza Neon Postgres.

## 1. Baza
Vercel → Storage / Marketplace → **Neon** → Create. Skopiuj `DATABASE_URL` (wersja *pooled*).
Prefiks `postgres://` jest zamieniany w kodzie na `postgresql+psycopg://`.

## 2. Backend (projekt `parent-guide-api`)
- Import repo, **Root Directory: `backend`**, Framework: Other.
- Zmienne: `DATABASE_URL` (z Neon), `ADMIN_TOKEN` (silne hasło), `SEED_ON_STARTUP=false`.
- Jednorazowy seed z komputera:
  `cd backend && pip install -e . && DATABASE_URL='<neon>' python -m app.seed`
- Test: `https://<api>.vercel.app/api/health` i `/api/docs`.

## 3. Frontend (projekt `parent-guide`)
- Import repo, **Root Directory: `frontend`**, Framework: Next.js.
- Zmienne (Production + Preview): `API_URL=https://<api>.vercel.app`, `INTERNAL_API_URL=https://<api>.vercel.app`.
  `API_URL` jest czytany podczas builda (rewrites `/api/*`), więc po zmianie zrób Redeploy.
- Polskie adresy działają przez `rewrites` w `next.config.ts` (bez nginxa).

## CLI (zamiast klikania)
```
cd backend  && vercel --prod        # zapisz URL
cd ../frontend && vercel env add API_URL production && vercel env add INTERNAL_API_URL production && vercel --prod
```
