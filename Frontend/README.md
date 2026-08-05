# Campaign Studio

An AI social media campaign generator. Upload a product image, describe the
product through a chat-style interface, and generate Instagram posts,
captions, and short videos — then refine any of it with natural language.

Built with Vue 3 (Composition API, `<script setup>`), TypeScript, Vite,
Pinia, Vue Router, Tailwind CSS, and Axios.

## Install

```sh
npm install
```

## Run

```sh
npm run dev
```

The app runs entirely against an in-memory mock backend by default, so
there's nothing else to configure to try it out.

Other scripts:

```sh
npm run build        # type-check + production build
npm run preview       # preview the production build locally
npm run type-check    # vue-tsc only
```

## Mock mode

Configuration lives in `.env` (copy `.env.example` to get started):

```sh
VITE_API_BASE_URL=http://localhost:8000/api
VITE_USE_MOCK_API=true
```

With `VITE_USE_MOCK_API=true`, every service call in `src/services/*.ts` is
routed to `src/services/mock.ts` instead of the network. The mock layer:

- simulates realistic network delay on every call
- simulates image upload progress
- returns a generated campaign with 3 image posts + 1 video, each moving
  through `queued → processing → completed` (or occasionally `failed`, to
  exercise retry/error states) with live progress
- simulates video render time and progress
- regenerates assets, captions, and full campaigns with fresh placeholder
  creative on each request

Set `VITE_USE_MOCK_API=false` to call a real backend at `VITE_API_BASE_URL`
instead — no component or store code needs to change, since UI code only
ever calls the typed functions in `src/services/*.ts`.

## Connecting a FastAPI (or other) backend

1. Set `VITE_USE_MOCK_API=false` and point `VITE_API_BASE_URL` at your API.
2. Implement the endpoints below with matching request/response shapes —
   see `src/types/campaign.ts` and `src/types/chat.ts` for the exact
   TypeScript models (`Campaign`, `CampaignAsset`, `ChatMessage`, etc.).
3. Uploads are sent as `multipart/form-data` with a single `file` field.

No frontend code changes are required beyond the env vars, since
`src/services/campaignService.ts`, `chatService.ts`, and `uploadService.ts`
already call these routes when mock mode is off.

### Expected API endpoints

| Method | Path                              | Purpose                                   |
| ------ | --------------------------------- | ------------------------------------------ |
| POST   | `/uploads/product-image`          | Upload a product image, returns `UploadedImage` |
| POST   | `/campaigns`                      | Create a campaign (`CreateCampaignPayload` → `Campaign`) |
| GET    | `/campaigns/:id`                  | Fetch current campaign state (for polling generation progress) |
| POST   | `/campaigns/:id/chat`             | Send a chat instruction (`CampaignChatPayload` → `ChatMessage`) |
| POST   | `/campaigns/:id/regenerate`       | Regenerate the entire campaign |
| POST   | `/campaigns/:id/publish`          | Publish the campaign |
| POST   | `/assets/:id/regenerate`          | Regenerate a single asset, optional `{ instruction }` body |
| PATCH  | `/assets/:id/caption`             | Update an asset's caption text, `{ caption }` body |
| POST   | `/assets/:id/caption/regenerate`  | Generate an alternative caption, optional `{ tone }` body |
| DELETE | `/assets/:id`                     | Delete an asset |
| GET    | `/assets/:id/download`            | Get a downloadable URL, returns `{ url, fileName }` |

The chat endpoint's request body carries a `scope` describing what the
instruction should affect:

```json
{
  "campaignId": "campaign_123",
  "message": "Make this feel more premium and reduce the amount of text",
  "scope": "selected_asset",
  "selectedAssetId": "asset_456"
}
```

`scope` is one of `"campaign" | "selected_asset" | "caption_only" | "visual_only"`.

## Project structure

```
src/
  components/     # layout, campaign, chat, assets, captions, shared
  views/          # CampaignStudioView (the single workspace view)
  stores/         # campaignStore, chatStore, uiStore (Pinia)
  services/       # api.ts, campaignService.ts, chatService.ts,
                  # uploadService.ts, mock.ts (mock backend)
  types/          # campaign.ts, chat.ts
  router/         # index.ts
```

Business logic lives in stores and services — components only read from
stores and call store actions, which in turn call the service layer.
