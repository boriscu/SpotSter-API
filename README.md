# SpotSter API

Python Flask REST API for a Monster Energy drink spotting application. Users report sightings of Monster drinks by uploading photos with geographic coordinates. The API processes the image through a vision LLM to identify the product, matches it to the nearest store, and updates a global availability map.

## Features

*   **Spotting Flow:** Users upload a photo + coordinates. The image is stored in S3, identified via a pluggable vision LLM (currently Mistral Pixtral), matched to a known Monster variant, linked to the nearest store, and the availability record is created or refreshed.
*   **Monster Catalogue:** Admin-managed ground truth database of Monster Energy drink variants, each with name, flavour, nutritional info, product line tag, and a reference image stored in S3.
*   **Store Discovery:** Single public endpoint for browsing stores with distance sorting, text search (store name or monster name/flavour), tag/flavour filtering, recency filtering, and pagination.
*   **Store Detail:** Detailed store view with available monsters (sorted by last spotted), recent spotting images, and aggregate counts.
*   **Vision Recognition Engine:** Strategy pattern with a `VisionProvider` abstraction. Swap LLM providers (Mistral, Anthropic, OpenAI) by implementing one method and updating the env config.
*   **S3 Storage:** Image upload/deletion for both admin product images and user spotting photos. Compatible with any S3-compatible service (AWS, DigitalOcean Spaces, MinIO).

## Running

See [SpotSter-Infra](https://github.com/TODO/SpotSter-Infra) for Docker setup. To run standalone without Docker:

```bash
cp .env.example .env
# fill in values
pip install -r requirements.txt
python run.py
```

Requires Python 3.12+ and a running PostgreSQL instance.

## API Workflows

### Authentication (Admin)

1.  `POST /api/v1/auth/` with `{"email": "...", "password": "..."}` to get an access token.
2.  Use the token as `Authorization: Bearer <token>` header on admin endpoints.
3.  In Swagger UI (`http://localhost:5000/api/1.0/`), click **Authorize** and enter `Bearer <token>`.

### Admin: Manage Monster Drinks

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/admin/monsters/` | List all monsters |
| POST | `/api/v1/admin/monsters/` | Create a monster (`multipart/form-data` with form fields + optional `image` file) |
| GET | `/api/v1/admin/monsters/<id>` | Get a single monster |
| PUT | `/api/v1/admin/monsters/<id>` | Update a monster (same format as create, image replaces old one in S3) |
| DELETE | `/api/v1/admin/monsters/<id>` | Delete a monster and its S3 image |

Monster fields: `name`, `flavour`, `description`, `calories`, `sugar_grams`, `caffeine_mg`, `is_zero_sugar`, `tag` (1=Original, 2=Ultra, 3=Java, 4=Juiced, 5=Special), `image` (file upload).

### Admin: Manage Stores

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/admin/stores/` | List all stores |
| POST | `/api/v1/admin/stores/` | Create a store (JSON: `name`, `address`, `latitude`, `longitude`) |
| GET | `/api/v1/admin/stores/<id>` | Get a single store |
| PUT | `/api/v1/admin/stores/<id>` | Update a store |
| DELETE | `/api/v1/admin/stores/<id>` | Delete a store |

### Public: Submit a Spotting

`POST /api/v1/public/spottings/` — `multipart/form-data` with:
*   `file` — photo of the Monster drink
*   `latitude` / `longitude` — where the photo was taken

**Flow:** Image is validated and uploaded to S3. The vision LLM receives the photo alongside all known Monster slugs and attempts identification. If matched, the nearest store (within 1km) is found and availability is recorded. The response includes the matched monster (with reference image URL) and store info.

### Public: Browse Stores

`GET /api/v1/public/stores/` — single endpoint with optional query params:

| Param | Type | Description |
|-------|------|-------------|
| `lat` | float | User latitude (enables distance sorting) |
| `lng` | float | User longitude |
| `limit` | int | Page size (default 20) |
| `offset` | int | Skip N stores for pagination |
| `search` | string | Search by store name or monster name/flavour |
| `tags` | string | Comma-separated tag values (e.g. `1,2` for Original + Ultra) |
| `flavours` | string | Comma-separated monster slugs |
| `spotted_since` | string | ISO date (e.g. `2026-04-01`) — only stores with spottings after this date |

Response:
```json
{
  "stores": [
    {
      "id": 1,
      "name": "Store Name",
      "address": "...",
      "latitude": 44.81,
      "longitude": 20.46,
      "distance_km": 0.5,
      "available_monsters": [
        {
          "id": 1,
          "name": "Monster Ultra Sunrise",
          "flavour": "Ultra Sunrise",
          "slug": "monster-ultra-sunrise",
          "image_url": "...",
          "is_zero_sugar": true,
          "tag": 2,
          "last_spotted_at": "2026-04-25 22:00:00"
        }
      ]
    }
  ],
  "total": 45,
  "limit": 20,
  "offset": 0
}
```

### Public: Store Detail

`GET /api/v1/public/stores/<id>` — returns full store info with:
*   Available monsters sorted by last spotted
*   Last 10 spotting report images with matched monster info
*   `flavour_count` and `total_spottings` counts

### Public: Monster Catalogue

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/public/monsters/` | List all Monster drinks |
| GET | `/api/v1/public/monsters/<id>` | Get a single Monster drink |

### Public: Available Filters

`GET /api/v1/public/filters` — returns tags that have at least one monster, with counts. Used to populate filter UI.

```json
{
  "tags": [
    {"value": 2, "label": "Ultra", "count": 5},
    {"value": 1, "label": "Original", "count": 3}
  ]
}
```

## Vision Recognition Architecture

The recognition engine uses a strategy pattern with two layers of abstraction:

1.  **`RecognitionStrategy`** — defines the recognition approach (vision LLM vs. CLIP vs. fine-tuned model)
2.  **`VisionProvider`** — defines the LLM provider within the vision LLM strategy

To add a new provider (e.g. OpenAI):
1.  Create `app/services/spotting_services/openai_vision_provider.py` implementing `VisionProvider.analyze_image()`
2.  Add a branch in `MonsterRecognitionEngine._create_default_strategy()`
3.  Set `VISION_PROVIDER=openai` and `OPENAI_API_KEY=...` in `.env`

The prompt, response parsing, and monster matching logic in `VisionLLMRecognitionStrategy` stays untouched.

Config: `VISION_PROVIDER`, `VISION_MODEL`, `VISION_MIN_CONFIDENCE`, and the provider-specific API key.

## Project Structure

```
app/
  endpoints/          Route handlers grouped by namespace
  models/
    pg/               Peewee ORM models (BaseModel with auto timestamps)
    enums/            HttpStatus, SpottingStatus, MonsterTag
  services/
    base_crud_services/   Generic CRUD repository
    monster_drink_services/   Monster CRUD + S3 image lifecycle
    store_services/       Store queries, proximity search, filtering
    spotting_services/    Spotting flow orchestration, recognition engine, vision providers
    storage_service.py    S3 upload/delete/presign
  commands/           Flask CLI (migrations, seeding)
  helpers/            Response generation, slug generation
  init/               App bootstrap (DB, logging, Sentry, error handlers)
config/               AppConfig (env-based)
migrations/           Peewee-migrate migration scripts
```

## Schema Changes

```bash
# Create a migration
docker compose exec api flask create-migration my_change_name

# Apply
docker compose exec api flask db-migrate

# Rollback
docker compose exec api flask db-rollback
```
