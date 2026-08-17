# EVision: AI Battery Utilization Copilot for Electric Vehicles

EVision is a software-first AI copilot for electric vehicles. It helps EV drivers use their battery more efficiently by analyzing live vehicle, battery, driving, route, and environmental data, then showing practical suggestions on the car screen.

This is not a normal EV dashboard or a simple battery monitoring system. EVision is designed as an intelligent in-car assistant that helps the driver increase the value of every charge.

## Core Idea

EVision continuously observes driving context and battery behavior, then guides the driver with simple, useful recommendations.

For example:

- If acceleration is aggressive, EVision suggests smoother starts to save energy.
- If speed is too high, it recommends an efficient speed range.
- If air conditioning usage is high, it suggests a more efficient cabin temperature.
- If the destination is far and battery is low, it suggests an energy-saving driving strategy.
- If the driver is unsure about charging, it explains whether fast charging is needed.

## What This Repository Contains

- A polished in-car copilot web prototype
- A Python backend API using only the standard library
- A Kaggle-trained energy prediction model blended with explainable range analytics
- A proactive suggestion engine
- A simple assistant layer for driver questions
- An optional provider-neutral generative LLM adapter with an offline fallback
- A RAG pipeline with document chunking and TF-IDF retrieval
- A reproducible Kaggle ingestion, feature-engineering, training, and validation pipeline
- Knowledge-base documents for battery efficiency, range prediction, charging, and response style

## Key Features

- Battery percentage display
- Battery Utilization Index
- Current predicted range
- Optimized predicted range
- Energy wastage percentage
- Live AI driving suggestions
- Energy consumption breakdown
- Chat or voice assistant for driver questions
- Trip summary report

## AI Capabilities

EVision combines multiple AI approaches:

- **Predictive AI / Machine Learning** to estimate battery usage, range, destination feasibility, and energy wastage.
- **Generative AI** to explain insights and recommendations in natural language.
- **NLP** to understand driver questions such as:
  - "Why is my battery draining fast?"
  - "Can I reach my destination without charging?"
  - "How can I save more battery?"
  - "Should I fast charge now?"
- **Hybrid AI** to combine analytics, prediction, scoring, and recommendation generation.

## Project Structure

```text
EVision/
├── backend/
│   ├── app.py
│   ├── data/
│   │   └── prepare_kaggle_dataset.py
│   ├── evision_engine/
│   │   ├── assistant.py
│   │   ├── model.py
│   │   ├── rag.py
│   │   └── schemas.py
│   ├── rag/
│   │   ├── build_index.py
│   │   └── query_index.py
│   └── training/
│       └── train_model.py
├── docs/
│   ├── ARCHITECTURE.md
│   ├── WORKFLOW.md
│   └── eraser/
├── frontend/
│   ├── index.html
│   ├── styles.css
│   └── src/
│       └── app.js
├── knowledge_base/
├── data/
│   ├── rag_index.json
│   ├── raw/kaggle_ev_energy/
│   └── processed/evision_energy_training.csv
├── models/
│   └── evision_energy_model.json
├── tests/
├── EVision_Documentation/
├── requirements.txt
└── README.md
```

## Inputs Analyzed

EVision can analyze:

- Battery percentage
- Current speed
- Acceleration pattern
- Braking pattern
- Driving mode
- Air conditioning usage
- Traffic condition
- Weather
- Road type
- Route distance
- Estimated destination range
- Charging habits
- Past driving behavior

## Planned User Experience

The main interface is intended to appear on the car screen. Instead of asking the driver to manually enter values, EVision reads available vehicle and contextual signals, then surfaces short and timely guidance.

Example suggestions:

- "Traffic is dense ahead. Hold 42-48 km/h and avoid sharp starts."
- "Set cabin to 24C to reduce AC load."
- "You can reach your destination without charging if you stay in Eco mode."
- "Fast charging is not needed for this route."

## Running the Project

Create and activate a virtual environment:

```powershell
python -m venv .venv_evision
.\.venv_evision\Scripts\Activate.ps1
```

The backend and ML pipeline use only the Python standard library, so no extra runtime packages are required.

Prepare the downloaded Kaggle dataset:

```powershell
python -m backend.data.prepare_kaggle_dataset
```

Build the RAG index:

```powershell
python -m backend.rag.build_index
```

Train the EVision energy model:

```powershell
python -m backend.training.train_model
```

Run the automated tests:

```powershell
python -m unittest discover -s tests -v
```

Start the backend and app:

```powershell
python -m backend.app
```

Optional generative model configuration uses any chat-completions-compatible endpoint:

```powershell
$env:EVISION_LLM_ENDPOINT = "https://your-provider.example/v1/chat/completions"
$env:EVISION_LLM_API_KEY = "your-api-key"
$env:EVISION_LLM_MODEL = "your-model-name"
```

Without these variables, EVision uses its grounded local response engine, so the demo remains fully functional offline.

Open:

```text
http://127.0.0.1:8000
```

## Backend API

Health check:

```text
GET /api/health
```

Analyze EV telemetry:

```text
POST /api/analyze
```

Ask the assistant:

```text
POST /api/assistant
```

Search the RAG knowledge base:

```text
GET /api/rag/search?q=Why is my battery draining fast?
```

## Dataset, Model, and RAG

The primary model is trained on Kaggle's **EV Energy Consumption Dataset** (`ziya07/ev-energy-consumption-dataset`), licensed CC0. Raw data, processed features, and the trained model are kept separately, and the model artifact records its provenance and validation metrics.

Held-out validation result:

- 4,000 training records and 1,000 validation records
- 0.393 kWh mean absolute error
- 0.493 kWh root mean squared error
- 0.948 R-squared

EVision does not claim to train a giant general-purpose foundation model from scratch. Its hybrid intelligence consists of:

- A Kaggle-trained EV energy prediction model
- A guard-railed analytics engine for braking, AC load, utilization, and destination safety
- A RAG knowledge base for battery efficiency, charging strategy, range prediction, and assistant response style
- A recommendation layer that combines live telemetry, model outputs, and retrieved context

This is the right foundation for a hackathon prototype because it is explainable, demo-ready, and expandable into real EV API integrations later.

## Project Goal

EVision does not increase battery capacity. It helps the driver increase the value of every charge through smarter, more efficient decisions.

## Current Status

The repository contains a complete prototype foundation: frontend, backend, training pipeline, RAG chunking, retrieval, assistant responses, and documentation.

## Future Scope

- Real EV API integration
- In-car infotainment UI prototype
- Mobile companion app
- Fleet efficiency dashboard
- Charging optimization
- Multilingual voice assistant
