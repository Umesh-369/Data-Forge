# DataForge AI (Conversational AutoML & Data Wrangling Platform)

DataForge AI is an advanced web application combining AI-assisted data wrangling, deterministic tool-based schema/row transformations, algorithm recommendation, AutoML model training, and version lineage with a cinematic dark-mode UI.

## Key Features

- **2D Statistical Dataset Profiler**: Instant row/column statistics, missingness detection, unique counts, sample value pills, and inline sparkline distribution histograms.
- **Conversational Data Editor**: Natural language edit agent powered by Claude tool calling with 11 whitelisted pandas operations.
- **Previewable & Revertible Diffs**: Visual before-and-after row/column diff cards. No operation commits canonical state without explicit user approval.
- **AutoML Engine**: Rule-based + meta-feature algorithm recommendation engine with traceable dataset statistics and sklearn model training.
- **Immutable Version Lineage**: Complete parent-child version lineage tree with instant revert and audit capability.
- **Cinematic 3D Hero**: React Three Fiber ambient particle canvas active on intro/profiling screens, automatically paused/unmounted during heavy spreadsheet editing.

## Tech Stack

- **Frontend**: Next.js 15 (App Router), TypeScript, Tailwind CSS, React Three Fiber, Framer Motion, Zustand.
- **Backend**: FastAPI, Python 3.11+, Pydantic v2, SQLAlchemy (async), Pandas, Scikit-Learn, Anthropic Claude API.

## Quick Start

### 1. Backend Setup
```bash
cd backend
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload --port 8000
```

### 2. Frontend Setup
```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.
