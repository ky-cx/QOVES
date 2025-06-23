# QOVES Face Segmentation API

This project is a comprehensive backend service built as a technical task for the Python Engineer role at Qoves Inc. The application accepts an image of a face, along with segmentation and landmark data, and asynchronously processes it to generate an SVG file with styled contour masks overlaid on the facial regions.

The entire stack is containerized using Docker and is designed with production-ready practices including scalability, observability, and caching.

## Key Features

This implementation successfully meets all **Advanced Criteria** by incorporating the following features:

* [cite_start]**Asynchronous Job Processing**: Utilizes Celery and Redis to handle long-running image processing tasks without blocking the API, providing an immediate response with a job ID.
* [cite_start]**Real-time Job Status Tracking**: A dedicated endpoint allows clients to poll for the status of a job (`pending`, `completed`, `failed`) and retrieve the result upon completion.
* **PostgreSQL Caching System**: Implements a database cache to store results. [cite_start]It uses a hashing mechanism to prevent reprocessing of duplicate requests, fetching results directly from the database when available.
* [cite_start]**Prometheus Monitoring**: Integrates with Prometheus to expose key application metrics (e.g., request latency, counts) for observability.
* [cite_start]**Rich Console Logging**: Provides beautifully formatted and color-coded logs for both the API server and the background worker for an enhanced developer experience.
* [cite_start]**Load Testing Mode**: A configurable mode that bypasses artificial delays, allowing for performance and load testing.
* **Advanced Image Processing**:
    * [cite_start]Automatically rotates images to be upright using facial landmarks.
    * [cite_start]Intelligently crops the face to remove unnecessary padding.
    * [cite_start]Applies smoothing algorithms to generate clean, aesthetically pleasing contours.
* [cite_start]**Dynamic SVG Generation**: Creates styled SVG files with dashed outlines and transparent fills as per the design requirements.
* **Fully Containerized**: The entire stack (API, Worker, Database, Cache, Monitoring) is defined and orchestrated with Docker Compose for easy, one-command setup.

## Architecture Overview

```
+-----------------+      +--------------------+      +------------------+
|   FastAPI App   |----->| Celery Job Queue   |----->|  Celery Worker   |
| (API Endpoints) |      | (Redis)            |      | (Image Processing)|
+-----------------+      +--------------------+      +------------------+
        ^                        ^                            |
        |                        |                            |
        | (Check Status)         | (Store Result)             | (Store/Fetch Cache)
        |                        |                            v
        |                        +------------------>+  PostgreSQL DB   |
        |                                            | (Job & Cache)    |
        +--------------------------------------------+------------------+
```

## Prerequisites

* [Docker](https://www.docker.com/products/docker-desktop/)
* [Docker Compose](https://docs.docker.com/compose/install/)

## How to Run

1.  **Clone the repository:**
    ```bash
    git clone <your-github-repository-url>
    cd qoves-face-segmentation
    ```

2.  **Start the services:**
    Run the following command from the root of the project directory. This will build the Docker images and start all the services.
    ```bash
    docker-compose up --build
    ```

3.  **The application is now running:**
    * **API Service**: `http://localhost:8000/redoc`
    * **Interactive API Docs (Swagger UI)**: `http://localhost:8000/docs`
    * **Prometheus Monitoring**: `http://localhost:9090`

## How to Use the API

### Option A: Using the Interactive Docs (Recommended)

1.  Open your web browser and navigate to **`http://localhost:8000/docs`**.
2.  Expand the `POST /api/v1/submit` endpoint and click **"Try it out"**.
3.  Prepare your `payload.json` file by running the helper script:
    ```bash
    python3 prepare_data.py
    ```
4.  Copy the entire content from the generated `payload.json` file and paste it into the "Request body" text area on the docs page.
5.  Click **"Execute"**. You will receive a response with a `job_id`.
6.  Expand the `GET /api/v1/status/{job_id}` endpoint, click **"Try it out"**, paste the `job_id`, and execute to get the final result.

### Option B: Using `curl`

1.  First, ensure you have the test files (`original_image.png`, `landmarks.txt`, etc.) in the root directory and generate the `payload.json` file:
    ```bash
    python3 prepare_data.py
    ```

2.  Submit the job and get a `job_id`:
    ```bash
    curl -X POST http://localhost:8000/api/v1/submit \
    -H "Content-Type: application/json" \
    -d @payload.json
    ```

3.  Check the job status using the `job_id` from the previous command:
    ```bash
    # Replace {Your-Job-ID-Here} with the actual ID
    curl http://localhost:8000/api/v1/status/{Your-Job-ID-Here}
    ```
