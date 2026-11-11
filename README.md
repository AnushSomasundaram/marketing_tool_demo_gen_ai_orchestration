# Campaign Studio

An AI social media campaign generator. Upload a product photo and Campaign Studio
plans a campaign, generates Instagram image posts and a short Reel, writes
captions, lets you refine any of it through a chat interface, and can publish an
approved post to Instagram (or simulate the publish in demo mode).

| Part | Stack | Docs |
| --- | --- | --- |
| [`Frontend/`](Frontend/) | Vue 3, TypeScript, Vite, Pinia, Tailwind CSS | [Frontend/README.md](Frontend/README.md) |
| [`Backend/`](Backend/) | FastAPI, SQLAlchemy, Alembic, SQLite | [Backend/README.md](Backend/README.md) |

## Features

- **Campaign planning:** an OpenAI model builds a structured campaign plan from the
  product photo, separating verified facts from creative copy.
- **Image and video generation:** GPT Image for posts, Runway image-to-video for a
  Reel, and FFmpeg for text overlays and thumbnails.
- **Chat-driven revisions:** ask for changes to the whole campaign, one asset, or
  just a caption. The server validates every action the model proposes before
  running it.
- **Version history:** each revision creates a new version, and you can restore any
  earlier one.
- **Instagram publishing:** real OAuth publishing, or a demo mode that simulates it.
- **Optional access gate:** set `ACCESS_CODE` on a public deployment so only people
  with the code can use the API (and spend AI credits).

## Quick start

Requirements: Python 3.12, Node.js 22.18+ or 24.12+, and FFmpeg.

### Backend

```sh
cd Backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

The API runs at http://localhost:8000. Interactive docs are at `/docs`.

By default `USE_MOCK_PROVIDERS=true` and `INSTAGRAM_DEMO_MODE=true`, so the app runs
without API keys or costs. To use real providers, add your OpenAI, Runway,
Cloudinary and Meta credentials to `Backend/.env` and set those flags to `false`.

### Frontend

```sh
cd Frontend
npm install
npm run dev
```

The app runs at http://localhost:5173. To point it at the backend, create
`Frontend/.env` with:

```sh
VITE_API_BASE_URL=http://localhost:8000/api
VITE_USE_MOCK_API=false
```

## Deployment

The backend includes a [`Dockerfile`](Backend/Dockerfile) suitable for Cloud Run. It
installs FFmpeg, runs migrations on startup, and listens on `$PORT`. SQLite storage
is per-container and resets on each new instance, so use a persistent database for
anything beyond a demo.

```sh
cd Backend
docker build -t campaign-studio-api .
docker run -p 8080:8080 --env-file .env campaign-studio-api
```

The frontend builds to static files with `npm run build` (output in
`Frontend/dist/`) and can be hosted on any static host, such as Vercel.

When `ACCESS_CODE` is set on the backend, the frontend shows an access screen and
sends the code in an `X-Access-Code` header with each request.

## Testing

```sh
cd Backend
pytest -q
ruff check .
```

Tests always use mock providers and Instagram demo mode, so they make no network
calls and cost nothing.

```sh
cd Frontend
npm run type-check
```

## Project structure

```
Backend/
  app/            FastAPI app: routers, services, models, schemas, prompts
  alembic/        database migrations
  tests/          pytest suite
  Dockerfile
Frontend/
  src/
    components/   chat, assets, and shared UI components
    services/     API client and access-code handling
    stores/       Pinia stores for campaigns and chat
```

See [Backend/README.md](Backend/README.md) for the full architecture, API reference,
and known limitations.
