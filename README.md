# PPTX API

A simple API for generating PowerPoint presentations from JSON schemas.

## Features

- Create title slides with optional subtitles
- Create bullet point slides with multi-level lists
- RESTful API with FastAPI

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
curl -X POST http://localhost:8080/generate-pptx \
  -H "Content-Type: application/json" \
  -d @sample.json \
  -o presentation.pptx
```

## JSON Schema

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
          "level": 0,
          "children": [
            {
              "text": "Second level bullet",
              "level": 1
            }
          ]
        },
        {
          "text": "Another first level bullet",
          "level": 0
        }
      ]
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