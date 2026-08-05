# Campaign Studio API

An API-ready FastAPI backend for **Campaign Studio**, the AI social media campaign
generator whose Vue 3 frontend lives in `../Frontend`. It plans a campaign from a
product photo, generates Instagram image posts and a short Reel, writes captions,
supports natural-language iteration on any of it, and can publish an approved post
to Instagram (or simulate that publish in demo mode).

This is a one-week portfolio build: the architecture is clean and realistic, but
deliberately skips microservices, Kubernetes, Kafka, Celery, and Redis. Background
work runs as FastAPI `BackgroundTasks` against SQLite.

## 1. Architecture overview

```
app/
  main.py            FastAPI app, CORS, static file mount, startup recovery
  config.py           pydantic-settings, one Settings object for the whole app
  database.py          SQLAlchemy engine/session
  dependencies.py       get_db, get_current_user (dev user), ownership checks
  models/               SQLAlchemy ORM models + enums
  schemas/              Pydantic v2 request/response models (camelCase over the wire)
  routers/              FastAPI routers: health, campaigns, captions, assets, instagram
  services/              business logic (see below)
    campaign_service.py    campaign CRUD + status recomputation
    generation_service.py  the initial plan -> images -> video -> captions workflow
    asset_service.py        asset revision (new version), delete, overlays, download
    caption_service.py       caption create/update/revise/alternatives/versions
    chat_service.py           chat turn orchestration + action-plan validation
    instagram_publisher.py    Instagram OAuth + publish state machine
    composition_service.py     FFmpeg overlay burn-in + thumbnail extraction
    job_service.py             GenerationJob bookkeeping + startup recovery
    storage/                    StorageProvider (local disk or Cloudinary)
    providers/                   text/image/video/social providers, real + mock
  prompts/               every LLM prompt, kept out of route handlers
  background/recovery.py  marks abandoned 'processing' rows failed on restart
alembic/                database migrations
storage/                 local file storage when USE_LOCAL_STORAGE=true
tests/                   pytest suite against TestClient + mock providers
```

**Data flow for a campaign:**

1. `POST /api/campaigns` uploads the product photo to storage and creates a
   `Campaign` row (`status=draft`).
2. `POST /api/campaigns/{id}/generate` returns `202` immediately and queues
   `generation_service.run_campaign_generation` as a background task, which:
   - asks the OpenAI orchestration model for a structured `CampaignPlan`
     (`app/schemas/plan.py`) that separates user-supplied facts, image-supported
     facts, and creative language, and explicitly lists unverified claims never
     to make;
   - creates one `Asset` row per plan concept (2 images, 1 video) and one
     `Caption` per asset;
   - generates the two images (GPT Image, conditioned on the product photo);
   - starts a Runway image-to-video task and polls it to completion, then
     extracts a thumbnail (FFmpeg) and uploads both to storage.
3. The Vue frontend polls `GET /api/campaigns/{id}` (and/or
   `GET /api/campaigns/{id}/jobs`) — assets transition
   `queued -> processing -> completed | failed` and the response always matches
   the frontend's existing `Campaign`/`CampaignAsset` TypeScript shape.

**Versioning:** every image/video revision and every caption edit creates a
**new row** (`parent_asset_id`/`root_asset_id`, `parent_caption_id`/`root_caption_id`,
`version`, `is_current`) rather than overwriting the current one. A campaign's
asset list only ever returns the current tip of each lineage; full history is
available via the `/versions` endpoints, and `/restore/{version_id}` creates a
new current version copying an old one's content (history itself is never
mutated).

## 2. Setup instructions

Requires Python 3.12 and FFmpeg.

```sh
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

Or with the provided Makefile: `make install`, `make migrate`, `make dev`.

The API serves at `http://localhost:8000`, docs at `/docs`, health at `/api/health`.

## 3. Environment variables

See `.env.example` for the full list with defaults. Highlights:

| Variable | Purpose |
| --- | --- |
| `DATABASE_URL` | SQLite URL for local dev |
| `FRONTEND_ORIGINS` | Comma-separated CORS allowlist (the Vue dev server) |
| `PUBLIC_BASE_URL` | Base URL used to build absolute `storage/...` URLs in local-storage mode |
| `OPENAI_API_KEY`, `OPENAI_TEXT_MODEL`, `OPENAI_IMAGE_MODEL` | OpenAI config — model names are read from env everywhere, never hardcoded |
| `RUNWAYML_API_SECRET`, `RUNWAY_VIDEO_MODEL`, `RUNWAY_VIDEO_DURATION_SECONDS`, `RUNWAY_VIDEO_RATIO` | Runway config |
| `CLOUDINARY_*`, `USE_LOCAL_STORAGE` | Storage backend selection |
| `META_APP_ID`, `META_APP_SECRET`, `META_REDIRECT_URI`, `INSTAGRAM_API_VERSION`, `INSTAGRAM_DEMO_MODE` | Instagram Graph API / demo mode |
| `USE_MOCK_PROVIDERS` | Master switch: mock every AI/video provider (Instagram is switched separately by `INSTAGRAM_DEMO_MODE`) |
| `FFMPEG_BINARY` | Path/name of the ffmpeg executable |

## 4. Local SQLite setup

`DATABASE_URL=sqlite:///./campaign_studio.db` (the default) is a file next to
this README. Nothing else to configure — `alembic upgrade head` creates it.

## 5. Alembic commands

```sh
alembic upgrade head              # apply all migrations
alembic revision --autogenerate -m "message"   # generate a new migration from model changes
alembic downgrade -1              # roll back one migration
```

## 6. Mock-provider mode

`USE_MOCK_PROVIDERS=true` (the default) routes every OpenAI/GPT Image/Runway
call to an in-process mock implementation under `app/services/providers/*/mock_*.py`:

- realistic delays instead of instant responses;
- a `CampaignPlan` built from your actual product name/description/tone;
- real placeholder image bytes (Pillow, stamped with the prompt so revisions
  are visibly different) and a real bundled placeholder video/thumbnail —
  actual files under `app/mock_assets/`, actually written to `storage/`;
- simulated Runway task progress over a few seconds via a real async polling
  loop (the same code path a real Runway task would take);
- an intentional ~15% video / ~6-8% image failure rate so retry/error-state UI
  has something to exercise.

`INSTAGRAM_DEMO_MODE=true` (also the default, independent of the flag above)
simulates the Instagram container-publish lifecycle without calling Meta.
**Every simulated publish is marked `isSimulated: true`, and the permalink is
suffixed `-simulated`** — the code never pretends a simulated publish is real,
in the API response or anywhere else.

With both flags at their defaults, the entire workflow works end-to-end with
**no API keys at all**.

## 7. Real OpenAI setup

1. Set `OPENAI_API_KEY` and `USE_MOCK_PROVIDERS=false`.
2. `OPENAI_TEXT_MODEL` should name an inexpensive current text+vision model
   (used for planning, captions, chat routing, and revision-prompt merging via
   the Responses API's structured-output `client.responses.parse(...)`).
3. `OPENAI_IMAGE_MODEL` should name your image generation/edit model. The
   image provider always uses the *edit* endpoint (conditioned on the product
   photo for the first generation, and on the previous output for revisions)
   so product identity is preserved — never a blind text-to-image call.

## 8. Real Runway setup

1. Set `RUNWAYML_API_SECRET` and `USE_MOCK_PROVIDERS=false`.
2. `RUNWAY_VIDEO_MODEL` (default `gen4_turbo`), `RUNWAY_VIDEO_DURATION_SECONDS`
   (default `5`), `RUNWAY_VIDEO_RATIO` (default `720:1280`, the real 9:16
   portrait ratio Runway's API actually accepts — valid options are
   `1280:720 | 720:1280 | 1104:832 | 832:1104 | 960:960 | 1584:672`) control
   the image-to-video call. The backend creates a task, then polls it via the
   same `_poll_video_task` loop used in mock mode, downloads the completed
   output, extracts a thumbnail, and uploads both to storage.

## 9. Cloudinary setup

1. Set `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET`.
2. Set `USE_LOCAL_STORAGE=false`.

`StorageProvider` (`app/services/storage/base.py`) is a small protocol with a
local-disk and a Cloudinary implementation; nothing else in the codebase knows
which one is active.

## 10. Instagram developer setup

1. Create a Meta app with Instagram Graph API access, connected to a Facebook
   Page with a linked Instagram professional account.
2. Set `META_APP_ID`, `META_APP_SECRET`, `META_REDIRECT_URI` (must match the
   app's OAuth redirect URI, default `http://localhost:8000/api/instagram/callback`).
3. Set `INSTAGRAM_DEMO_MODE=false`.
4. Hit `GET /api/instagram/connect` for the authorization URL, complete the
   Meta OAuth flow; the callback exchanges the code for a token and walks
   `/me/accounts` to find the connected Instagram business account id.
5. `POST /api/instagram/publish` then drives the real container-create ->
   status-poll -> publish -> permalink flow.

## 11. FFmpeg installation

```sh
brew install ffmpeg        # macOS
apt install ffmpeg         # Debian/Ubuntu
```

`GET /api/health` reports `ffmpeg: true/false`. If it's missing, overlay
composition and video-thumbnail extraction return a clear `CompositionError`
rather than failing silently — image/video *generation* still works, but the
overlays endpoint and video thumbnails will error until FFmpeg is installed.

## 12. API endpoint summary

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/health` | Service + dependency configuration status |
| POST | `/api/campaigns` | Create a campaign (multipart: `productImage` + fields) |
| GET | `/api/campaigns` | List campaigns |
| GET | `/api/campaigns/{id}` | Fetch campaign + current assets |
| DELETE | `/api/campaigns/{id}` | Delete a campaign |
| POST | `/api/campaigns/{id}/generate` | Kick off planning + generation (202) |
| POST | `/api/campaigns/{id}/regenerate` | Regenerate all images + video (202) |
| GET | `/api/campaigns/{id}/jobs` | List generation jobs for the campaign |
| POST | `/api/campaigns/{id}/chat` | Natural-language iteration (see below) |
| POST | `/api/campaigns/{id}/captions` | Generate an initial caption for an asset |
| PATCH | `/api/captions/{id}` | Manual caption edit (new version) |
| POST | `/api/captions/{id}/revise` | AI caption revision (new version) |
| POST | `/api/captions/{id}/alternatives` | AI alternative caption, optional tone override |
| GET | `/api/captions/{id}/versions` | Caption version history |
| POST | `/api/captions/{id}/restore/{version_id}` | Restore an old caption version (new version) |
| POST | `/api/campaigns/{id}/images` | Add one more image asset |
| POST | `/api/campaigns/{id}/videos` | Add one more video asset |
| GET | `/api/assets/{id}` | Fetch one asset |
| GET | `/api/assets/{id}/versions` | Asset version history |
| POST | `/api/assets/{id}/revise` | AI revision (new version, 202) |
| POST | `/api/assets/{id}/restore/{version_id}` | Restore an old asset version |
| PATCH | `/api/assets/{id}/overlays` | Deterministic FFmpeg overlay update (no AI call) |
| DELETE | `/api/assets/{id}` | Delete an asset |
| GET | `/api/assets/{id}/download` | `{ url, fileName }` for the current output |
| GET | `/api/instagram/connect` | Meta OAuth authorization URL |
| GET | `/api/instagram/callback` | OAuth callback, stores the access token |
| GET | `/api/instagram/accounts` | Connected Instagram account(s) |
| POST | `/api/instagram/publish` | Publish an asset (202) |
| GET | `/api/instagram/publish/{job_id}` | Publish job status |

Full request/response schemas with examples are in `/docs` (Swagger UI).

## 13. Natural-language iteration behavior

`POST /api/campaigns/{id}/chat` takes `{ message, scope, selectedAssetId? }`
where `scope` is `campaign | selected_asset | caption_only | visual_only` —
matching the frontend's existing chat scope selector exactly.

The OpenAI orchestration model translates the message into a structured
`ChatActionPlan` (an `assistantMessage` plus a list of actions), using only the
fixed `ChatActionType` enum. **The model's output is never trusted blindly** —
`chat_service._validate_actions` enforces, in Python, before anything executes:

- only the action types legal for the given `scope` survive (e.g.
  `caption_only` can never emit `revise_image`);
- for any scope other than `campaign`, every action's `assetId` is
  force-overwritten to the request's own `selectedAssetId` — the model can
  never redirect an action at a different asset;
- any action naming an asset that doesn't belong to this campaign is dropped;
- if a scope requires a selected asset and none was provided, every action is
  dropped in favor of `request_clarification`.

Fast actions (`revise_caption`, `generate_caption_alternative`) run
synchronously so the chat response already reflects the change. Slower actions
(image/video regeneration, overlay updates) are queued as `BackgroundTasks`;
the frontend picks up the result on its next campaign poll.

**Simplified scope, documented honestly:** `revise_campaign_plan` does not
restructure the stored `CampaignPlan` — it cascades the instruction as a
revision across every current image and the video. A from-scratch re-plan
was judged out of scope for a one-week build; see Known demo limitations.

## 14. Known demo limitations

- **Video revision is a new generation, not frame-level editing.** Per the
  brief: a video "revision" loads the original product image and the previous
  motion prompt, asks the orchestration model to merge in the new instruction,
  and starts a brand new Runway image-to-video task. There is no timeline
  editing, no partial re-render, no editing of an existing clip's frames.
- `revise_campaign_plan` (see above) cascades as a broad revision rather than
  regenerating the structured plan itself.
- `update_video_overlays` triggered from chat uses the raw instruction text as
  the overlay headline — it doesn't parse out a specific price/CTA/heading
  from natural language. The dedicated `PATCH /assets/{id}/overlays` endpoint
  takes explicit structured fields and is the precise way to do this.
- A single development user stands in for authentication; ownership checks
  run the same query shape real auth would use, but there's no login.
- Instagram real-publish OAuth/token-exchange code is written and structured
  correctly but, like the real OpenAI/Runway paths, is only exercised manually
  against real credentials — it's not part of the automated test suite (which
  must never spend API credits).

## 15. Cost-control notes

- `USE_MOCK_PROVIDERS=true` and `INSTAGRAM_DEMO_MODE=true` are the defaults —
  you have to opt in to spending money.
- The automated test suite forces mock/demo mode via `tests/conftest.py`
  regardless of your local `.env`, and asserts nothing in it can reach a real
  provider.
- `OPENAI_TEXT_MODEL`/`OPENAI_IMAGE_MODEL`/`RUNWAY_VIDEO_MODEL` are each read
  from one place (`app/config.py`) and threaded through everywhere else — to
  swap to a cheaper or more capable model, change the env var once.
- Caption generation, chat routing, and prompt-merging are the only
  synchronous-in-request LLM calls; image and video generation are always
  backgrounded, so a slow/expensive provider call never holds an HTTP
  connection open.

## 16. How the Vue frontend connects

Set `VITE_API_BASE_URL=http://localhost:8000/api` in `../Frontend/.env` and
`VITE_USE_MOCK_API=false` to point the existing Vue service layer
(`src/services/*.ts`) at this backend instead of its own bundled mock. Every
response shape here was built to match the frontend's existing TypeScript
models (`Campaign`, `CampaignAsset`, `ChatMessage`, `CaptionVersion`) via
Pydantic camelCase aliases, so no visual or component changes are needed —
only the service-layer request/response wiring (see the frontend's own
integration notes for the small, specific adjustments this required, e.g. the
campaign-creation endpoint expecting `multipart/form-data` with the raw file
rather than a separate upload step).

CORS is configured from `FRONTEND_ORIGINS` (comma-separated), defaulting to
`http://localhost:5173` — the Vite dev server's default port.

## Testing

```sh
pytest -q          # or: make test
ruff check .        # or: make lint
ruff format .        # or: make format
```

All tests run against `TestClient` with mock providers and demo Instagram
mode forced on in `tests/conftest.py` — no network calls, no API costs.
Covers: campaign creation, upload validation, campaign-plan-derived assets,
ownership checks, all four chat scopes (including server-side action
validation/rejection), image and video revision version creation, overlay
updates without AI regeneration, a forced provider failure, mock job
progress, caption CRUD/versioning/restore, and the Instagram demo publish
flow end to end.
