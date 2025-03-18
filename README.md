# PPTX API

A simple API for generating PowerPoint presentations from JSON schemas.

## Features

- Create title slides with optional subtitles
- Create bullet point slides with multi-level lists
- Create image slides from URLs with automatic broken image handling
- Create data tables with headers and rows
- Create split layout slides with different content combinations
- Custom filenames for downloaded presentations
- Cloud storage for presentations with public download links
- Presenter notes with detailed error information for troubleshooting

## Setup

```bash
# Install dependencies
poetry install

# Run the server
poetry run python -m app.main
```

The API will be available at http://localhost:8080.

## API Usage

### Generate a PowerPoint presentation

```bash
# Basic example with V1 features
curl -X POST http://localhost:8080/generate-pptx \
  -H "Content-Type: application/json" \
  -d @sample.json

# Advanced example with V2 features
curl -X POST http://localhost:8080/generate-pptx \
  -H "Content-Type: application/json" \
  -d @sample-v2.json
```

The API returns a JSON response with a download URL:

```json
{
  "presentation_id": "fb7b0a52-0dbd-4922-b7be-c1a78139466c",
  "download_url": "http://localhost:8080/download/fb7b0a52-0dbd-4922-b7be-c1a78139466c",
  "filename": "example-presentation.pptx",
  "expires_in_hours": 24
}
```

## JSON Schema (V2)

### Basic Slide Types

```json
{
  "slides": [
    {
      "type": "title",
      "title": "Presentation Title",
      "subtitle": "Optional Subtitle"
    },
    {
      "type": "bullet",
      "title": "Bullet Points Slide",
      "points": [
        {
          "text": "First level bullet",
          "children": [
            {
              "text": "Second level bullet"
            }
          ]
        },
        {
          "text": "Another first level bullet"
        }
      ]
    },
    {
      "type": "image",
      "title": "Image Slide Title",
      "url": "https://example.com/image.jpg",
      "alt": "Description of the image"
    },
    {
      "type": "table",
      "title": "Data Table Title",
      "headers": ["Column 1", "Column 2", "Column 3"],
      "rows": [
        ["Row 1, Cell 1", "Row 1, Cell 2", "Row 1, Cell 3"],
        ["Row 2, Cell 1", "Row 2, Cell 2", "Row 2, Cell 3"]
      ]
    }
  ],
  "filename": "custom-filename.pptx"
}
```

### Split Layout Slides

```json
{
  "type": "split",
  "title": "Split Layout Example",
  "layout": "left-right",
  "sections": [
    {
      "type": "bullet",
      "points": [
        {
          "text": "Point on the left side"
        }
      ]
    },
    {
      "type": "image",
      "url": "https://example.com/image.jpg",
      "alt": "Image on the right side"
    }
  ]
}
```

## Deployment to Fly.io

1. Install the Fly CLI: `curl -L https://fly.io/install.sh | sh`
2. Log in to Fly: `fly auth login`
3. Deploy the app: `fly launch`

Alternatively, deploy manually:

```bash
fly launch --name pptx-api
fly deploy
```

## Storage Configuration

The API supports S3-compatible storage (like Tigris) for storing presentations. Set the following environment variables:

```
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_ENDPOINT_URL_S3=your_s3_endpoint
AWS_REGION=your_region
BUCKET_NAME=your_bucket_name
```

If S3 storage is not configured, the API will fall back to local file storage.
