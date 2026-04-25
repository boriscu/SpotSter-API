# SpotSter API

SpotSter is a robust, Python Flask-based API backend designed for a Monster Energy drink spotting application. The core objective of the API is to allow users to report "spottings" of specific Monster drinks with their geographic coordinates and photos. The backend processes the sighting, leverages image recognition to match the product, and updates a global availability map for others to see where their favourite drinks can be found.

## Features

*   **Public Spotting & Catalogue:** Users can upload spotting photos with geographic coordinates (latitude/longitude), and view the global database of Monster drinks and stores without requiring authentication.
*   **Image Recognition:** Spotting submissions pass through a generic recognition engine (currently using a stub strategy that simulates detection) to link user uploads to ground-truth products.
*   **Admin Dashboard:** JWT-protected endpoints to manage (CRUD) the ground truth database of `MonsterDrink` variations and physical `Store` locations.
*   **Unique Inventory Tracking:** Complex constraints ensure that the database models physical reality accurately (e.g., maintaining a unique store+drink availability record without duplicates).
*   **Modular Architecture:** Designed with maintainability in mind, utilizing the App Factory pattern, robust Class-Based Configurations, Peewee ORM, and dedicated Repository/Service-layers mirroring enterprise architecture standards.
*   **Object Storage Integration:** S3 client compatibility (e.g., AWS S3, MinIO) for secure, scalable image upload and sharing.
*   **Dockerized Ecosystem:** Painless setup containing both the API layer (via Gunicorn) and an Alpine PostgreSQL database out-of-the-box.

## Prerequisites

1.  **Docker Desktop** (or Docker Engine + Docker Compose)
2.  **(Optional)** Python 3.12+ (if running outside of Docker for development)
3.  Any S3 compatible object storage instance (e.g., AWS S3, DigitalOcean Spaces, MinIO).

## Initial Setup

1. **Clone the repository:** Ensure you are in the project root `C:\Projekti\SpotSter-API`.
2. **Setup Environment Variables:** We have provided a template for the environment variables.
    *   Copy the `.env.example` file and rename it to `.env`:
        ```bash
        cp .env.example .env
        ```
    *   Open `.env` and fill in your custom values. Be specifically sure to set:
        *   `JWT_SECRET_KEY`: A strong, random string (e.g., generated with `openssl rand -hex 32`).
        *   `S3_*` values: To support uploading of spotting images.
        *   `ADMIN_EMAIL` and `ADMIN_PASSWORD`: Used to generate the initial admin superuser.

3. **Build and Run the Containers:**
    ```bash
    docker-compose up -d --build
    ```
   This will pull the Postgres image, build the Python 3.12 Flask image, and start both containers. The API will be exposed on `http://localhost:5000`.

4. **Initialize Database and Admin:**
    Since the application uses `peewee-migrate`, you must handle migrations manually via built-in CLI commands from the API container.
    *   **Health Check:** Wait until the database is ready:
        ```bash
        docker-compose exec api flask db-health-check
        ```
    *   **Run Migrations:** Initialize the database schema:
        ```bash
        docker-compose exec api flask db-migrate
        ```
    *   **Seed Admin User:** Generate your initial admin using the credentials you defined in the `.env` file:
        ```bash
        docker-compose exec api flask seed-admin
        ```

## Utilizing the API

The API exposes a comprehensive, interactive Swagger UI out of the box. 
**Navigate your browser to `http://localhost:5000/api/1.0/`** to explore, test, and authenticate against all available endpoints.

### Authentication Flow (Admin Only)

To interact with the `/api/v1/admin/monsters` or `/api/v1/admin/stores` endpoints, you must authenticate.
1. Make a POST request to `/api/v1/auth/` containing `{ "email": "your_admin_email", "password": "your_password" }`.
2. Grab the returned `access_token`.
3. In the Swagger UI, click the **Authorize** lock icon button at the top of the page.
4. Provide the token using the format: `Bearer <your_token>` and click Authorize.

### Core Endpoints Overview

*   **Auth:** `/api/v1/auth/` (POST, GET - manage and validate admin sessions)
*   **Monsters Admin:** `/api/v1/admin/monsters/` (GET, POST, PUT, DELETE - admin ground truth catalog management)
*   **Stores Admin:** `/api/v1/admin/stores/` (GET, POST, PUT, DELETE - manage known store coordinates)
*   **Public Catalogue:** `/api/v1/monsters/` and `/api/v1/stores/` (GET - fetch available products and stores with current inventory availability)
*   **Spottings:** `/api/v1/spottings/` 
    *   **POST:** *Requires a `multipart/form-data` payload containing an image `file`, `latitude`, and `longitude`.* 

## Project Structure Highlights

*   **`/app/endpoints/`:** Contains Flask-RESTX controller route registrations separated by domain namespaces (e.g., auth, spottings, public).
*   **`/app/models/`:** Definiton of PG tables (`peewee`) and basic Enums/Maps mappings mapping HTTP statues.
*   **`/app/services/`:** Segregation of all business and data logic away from the API boundary. Highlights include the facade `spotting_report_service.py`, generic `base_repository.py`, and the S3 handler `storage_service.py`.
*   **`/app/commands/`:** Extends Flask CLI to provide utilities like db migrating and scripting administrative tasks.
*   **`/config/`:** Houses `AppConfig`, reading immediately from the environment payload to securely bootstrap configurations. 

## Making Schema Changes
If you modify the models inside `/app/models/pg/`:
1. Generate an automatic migration patch:
    ```bash
    docker-compose exec api flask create-migration my_new_feature_name
    ```
2. Apply the change:
    ```bash
    docker-compose exec api flask db-migrate
    ```
