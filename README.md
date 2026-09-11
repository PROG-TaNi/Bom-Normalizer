<p align="center">
  <img src="https://img.shields.io/badge/🏭_BOM_Normalizer-OpenEnv_Agent_Training_Environment-blueviolet?style=for-the-badge" alt="BOM Normalizer" />
</p>

<h3 align="center">Enterprise-grade Bill of Materials (BOM) normalization environment<br/>for training AI agents on real-world supply-chain data-cleaning tasks.</h3>

<p align="center">
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python 3.10+" /></a>
  <a href="https://fastapi.tiangolo.com"><img src="https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI" /></a>
  <a href="https://react.dev"><img src="https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react&logoColor=black" alt="React" /></a>
  <a href="https://tailwindcss.com"><img src="https://img.shields.io/badge/Tailwind_CSS-3.3-06B6D4?style=flat-square&logo=tailwindcss&logoColor=white" alt="Tailwind CSS" /></a>
  <a href="#license"><img src="https://img.shields.io/badge/License-MIT-green?style=flat-square" alt="License: MIT" /></a>
</p>

<p align="center">
  Built by <strong>Team Quasars</strong> for the <a href="https://github.com/PROG-TaNi/Bom-Normalizer">OpenEnv Hackathon 2025</a>
</p>

---

## 📑 Table of Contents

<details>
<summary>Click to expand</summary>

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Architecture](#-architecture)
- [Project Structure](#-project-structure)
- [Getting Started](#-getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Environment Variables](#environment-variables)
  - [Running the Application](#running-the-application)
  - [Docker Deployment](#-docker-deployment)
- [How the Environment Works](#-how-the-environment-works)
  - [The Problem: Messy BOMs](#the-problem-messy-boms)
  - [Task Difficulty Levels](#task-difficulty-levels)
  - [Action Space](#action-space)
  - [Observation Space](#observation-space)
  - [Reward System](#reward-system)
  - [Grading & Scoring](#grading--scoring)
- [Backend — Deep Dive](#-backend--deep-dive)
- [Frontend — Deep Dive](#-frontend--deep-dive)
- [Inference Script](#-inference-script)
- [Demo Script](#-demo-script)
- [Data Files](#-data-files)
- [API Reference](#-api-reference)
- [Configuration Files](#-configuration-files)
- [Development](#-development)
- [License](#-license)

</details>

---

## 🔍 Overview

In electronics manufacturing, a **Bill of Materials (BOM)** is a structured list of every component needed to build a product — vendors, part numbers, values, packages, and quantities. In the real world, BOMs arrive from multiple suppliers in wildly inconsistent formats:

| 🚩 Problem | Example |
|:---|:---|
| Vendor abbreviations | `TI`, `T.I.`, `Texas Inst.` → **`Texas Instruments`** |
| Inconsistent units | `10K`, `10k`, `10kΩ`, `10kohm` → **`10000`** |
| Package variation | `SOT23`, `SOT-23`, `SOT23-3` → **`SOT-23`** |
| Duplicate rows | Same component listed twice with different names |

This project provides a **complete reinforcement-learning environment** where AI agents learn to clean messy BOMs. It follows the [OpenEnv](https://openenv.dev) standard (`reset` → `step` → `state` loop) and exposes a **FastAPI HTTP API** that any LLM or RL agent can interact with.

---

## ✨ Key Features

| Category | Features |
|:---|:---|
| 🎮 **Environment** | Three difficulty levels (Easy / Medium / Hard) · Dense reward signal `[-0.15, +0.30]` · Deterministic seed-controlled data generation |
| 🤖 **Agent Interface** | 10 discrete actions · Partial-credit grading · Levenshtein similarity · Unit-aware value equivalence |
| 🧠 **AI Integration** | LLM auto-normalize via any OpenAI-compatible endpoint · Competition-ready inference script |
| 🖥️ **Web Dashboard** | React + TypeScript frontend · Live BOM table · Action builder · Reward log · Episode stats |
| 📦 **Deployment** | Docker-ready · Excel/CSV upload · Windows one-click startup |

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                    Frontend (React + Vite)                        │
│                       localhost:3000                              │
│  ┌──────────┐ ┌──────────────┐ ┌────────────┐ ┌──────────────┐  │
│  │ BOMTable │ │ ActionBuilder│ │EpisodeStats│ │  RewardLog   │  │
│  └──────────┘ └──────────────┘ └────────────┘ └──────────────┘  │
└───────────────────────────┬──────────────────────────────────────┘
                            │  /api/* → proxy
                            ▼
┌──────────────────────────────────────────────────────────────────┐
│                   FastAPI Server (Python)                         │
│                     localhost:7860                                │
│                                                                  │
│  /health  /tasks  /reset  /step  /state                          │
│  /upload-bom  /download-template  /auto-normalize                │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                  BOMEnv (Core Engine)                       │  │
│  │  ┌───────────┐ ┌───────────┐ ┌────────┐ ┌─────────────┐  │  │
│  │  │ Generator │ │  Reward   │ │ Grader │ │   Models    │  │  │
│  │  └───────────┘ └───────────┘ └────────┘ └─────────────┘  │  │
│  └────────────────────────────────────────────────────────────┘  │
│                           │                                      │
│                  ┌────────┴────────┐                             │
│                  │   Data Files    │                             │
│                  │ vendor_aliases  │                             │
│                  │ unit_variants   │                             │
│                  │ part_numbers    │                             │
│                  └─────────────────┘                             │
└──────────────────────────────────────────────────────────────────┘
                            │
              (auto-normalize only)
                            ▼
                ┌───────────────────────┐
                │  LLM Provider (any    │
                │  OpenAI-compatible)   │
                │  Ollama / HF / OpenAI │
                └───────────────────────┘
```

---

## 📂 Project Structure

<details>
<summary>Click to expand full project tree</summary>

```
bom-normalizer/
├── bom_normalizer/                # Core Python package
│   ├── __init__.py                # Package metadata (v1.0.0, Team Quasars)
│   ├── models.py                  # Pydantic v2 data models
│   ├── tasks.py                   # Task difficulty configurations
│   ├── generator.py               # Deterministic BOM generator + corruption engine
│   ├── env.py                     # Core environment (reset/step/state loop)
│   ├── reward.py                  # Dense per-step reward computation
│   ├── grader.py                  # Final episode scoring with partial credit
│   └── server.py                  # FastAPI HTTP API + LLM auto-normalize
│
├── server/
│   └── app.py                     # Alternate entry point for `server` CLI command
│
├── frontend/                      # React + TypeScript web dashboard
│   ├── src/
│   │   ├── App.tsx                # Main app: task selector, file upload, AI normalize
│   │   ├── App.css                # App-level styles
│   │   ├── index.css              # Global Tailwind CSS imports
│   │   ├── main.tsx               # React DOM entry point
│   │   └── components/
│   │       ├── BOMTable.tsx       # Interactive BOM data table with status colors
│   │       ├── ActionBuilder.tsx  # Action form builder for manual normalization
│   │       ├── EpisodeStats.tsx   # Step count, reward, fields remaining display
│   │       └── RewardLog.tsx      # Scrollable reward history log
│   ├── package.json               # NPM dependencies & scripts
│   ├── vite.config.ts             # Vite config with API proxy to :7860
│   ├── tailwind.config.js         # Tailwind CSS configuration
│   ├── postcss.config.js          # PostCSS pipeline
│   ├── tsconfig.json              # TypeScript compiler options
│   └── index.html                 # HTML entry point
│
├── data/                          # JSON reference data
│   ├── vendor_aliases.json        # 24 vendor → alias mappings (140+ aliases)
│   ├── unit_variants.json         # Unit variants for R, C, L, V, A, Hz, W, etc.
│   └── part_numbers.json          # Canonical part numbers + package variants
│
├── inference.py                   # Competition baseline inference (LLM agent loop)
├── demo_normalization.py          # Interactive CLI demo with colorized output
├── START_ALL_SERVICES.bat         # Windows: launch Ollama + backend + frontend
│
├── pyproject.toml                 # Python project metadata & dependencies
├── requirements.txt               # Pinned Python dependencies
├── openenv.yaml                   # OpenEnv environment specification
├── Dockerfile                     # Docker image (Python 3.11-slim, port 7860)
├── .dockerignore                  # Docker build exclusions
├── .env.example                   # Environment variable template
├── .gitignore                     # Git exclusion rules
├── validate-submission.ps1        # PowerShell submission validator
├── validate-submission.sh         # Bash submission validator
├── FINAL_SUBMISSION_CHECKLIST.md  # Submission checklist document
└── SUPER_SIMPLE_GUIDE.md          # Quick-start guide
```

</details>

---

## 🚀 Getting Started

### Prerequisites

| Tool | Version | Purpose |
|:---|:---|:---|
| **Python** | 3.10 – 3.12 | Backend runtime |
| **Node.js** | 18+ | Frontend build tooling |
| **npm** | 9+ | Package manager |
| **Git** | Any | Version control |
| Ollama *(optional)* | Any | Local LLM for auto-normalize |
| Docker *(optional)* | 20+ | Container deployment |

### Installation

**1. Clone the repository**

```bash
git clone https://github.com/PROG-TaNi/Bom-Normalizer.git
cd Bom-Normalizer
```

**2. Set up the Python environment**

```bash
# Create and activate a virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# OR install as editable package (recommended for development)
pip install -e ".[dev]"
```

**3. Set up the Frontend**

```bash
cd frontend
npm install
cd ..
```

### Environment Variables

Copy the example file and configure:

```bash
cp .env.example .env
```

| Variable | Required | Default | Description |
|:---|:---:|:---|:---|
| `HF_TOKEN` | For `inference.py` | — | Hugging Face API token |
| `API_BASE_URL` | No | `https://router.huggingface.co/v1` | LLM API endpoint URL |
| `MODEL_NAME` | No | `meta-llama/Llama-3.3-70B-Instruct` | LLM model identifier |
| `OPENAI_API_KEY` | No | — | OpenAI-compatible API key |
| `ENV_URL` | No | `http://localhost:7860` | Environment server URL |
| `DEBUG` | No | `false` | Enable debug logging |

### Running the Application

<details>
<summary><strong>Option A — Two terminals (recommended for development)</strong></summary>

```bash
# Terminal 1: Start the backend
python -m uvicorn bom_normalizer.server:app --host 0.0.0.0 --port 7860 --reload

# Terminal 2: Start the frontend
cd frontend
npm run dev
```

Then open **http://localhost:3000** in your browser.

</details>

<details>
<summary><strong>Option B — Windows one-click</strong></summary>

```bash
START_ALL_SERVICES.bat
```

This starts Ollama, the backend (port 7860), and the frontend (port 3001).

</details>

### 🐳 Docker Deployment

```bash
# Build the image
docker build -t bom-normalizer .

# Run the container
docker run -p 7860:7860 --env-file .env bom-normalizer
```

> The Docker image exposes port **7860** with a built-in health check at `/health`.

---

## 🎮 How the Environment Works

### The Problem: Messy BOMs

The environment generates a **messy BOM** from a 50-entry canonical electronics dataset. Each entry has:

- **Vendor name** — e.g., `Texas Instruments`, `Murata Manufacturing`
- **Part number** — e.g., `SN74HC00N`, `GRM188R71H104KA93D`
- **Value** — resistance in ohms, capacitance in farads, voltage
- **Package** — e.g., `DIP-14`, `0402`, `SOT-23`
- **Quantity** — integer count

The generator applies **difficulty-appropriate corruptions** to produce the messy version, while preserving the gold-standard answer.

### Task Difficulty Levels

| Level | Rows | Fields to Normalize | Max Steps | Baseline Score | Special |
|:---:|:---:|:---|:---:|:---:|:---|
| 🟢 **Easy** | 10 | `vendor_name` only | 30 | 0.85 | — |
| 🟡 **Medium** | 50 | `vendor_name`, `value`, `package` | 100 | 0.55 | — |
| 🔴 **Hard** | ~100 | All 4 fields | 250 | 0.25 | 40 duplicate pairs + 10 edge cases |

<details>
<summary><strong>Easy Task Details</strong></summary>

Only vendor names are corrupted. The agent must map abbreviations and aliases to canonical names:
- `TI` → `Texas Instruments`
- `Murata` → `Murata Manufacturing`
- `ST` → `STMicroelectronics`

</details>

<details>
<summary><strong>Medium Task Details</strong></summary>

Three fields are corrupted:
- **Vendors**: Same as Easy
- **Values**: `10K` → `10000`, `100nF` → `100e-9`, `5V` → `5`
- **Packages**: `DIP14` → `DIP-14`, `SOT23` → `SOT-23`

</details>

<details>
<summary><strong>Hard Task Details</strong></summary>

All four fields are corrupted, plus:
- **40 duplicate row pairs** — rows that refer to the same component but with different corruptions
- **10 edge cases** — empty vendor names, conflicting units, near-duplicate entries, typos like `Infinion` for `Infineon Technologies`
- The agent must identify and **merge duplicates** using the `merge_rows` action

</details>

### Action Space

The environment provides **10 discrete actions**:

| Action | Parameters | Description |
|:---|:---|:---|
| `normalize_vendor` | `row_id`, `new_value` | Set canonical vendor name for one row |
| `normalize_value` | `row_id`, `new_value` | Set canonical component value for one row |
| `normalize_package` | `row_id`, `new_value` | Set canonical package code for one row |
| `normalize_part` | `row_id`, `new_value` | Set canonical part number for one row |
| `merge_rows` | `row_id`, `duplicate_row_id` | Mark a row as duplicate of another *(Hard only)* |
| `flag_anomaly` | `row_id` | Flag a row as suspicious or invalid data |
| `inspect_row` | `row_id` | Reveal the gold-standard answer *(costs a hint; 3 per episode)* |
| `batch_normalize` | `field`, `from_value`, `new_value` | Normalize all matching rows in one action |
| `undo_last` | — | Revert the previous action *(small reward penalty)* |
| `submit` | — | End the episode and trigger final grading |

### Observation Space

After every action, the agent receives a structured observation:

```json
{
  "task_id": "easy",
  "task_description": "Normalize vendor names across 10 BOM rows",
  "rows": [
    {
      "row_id": 1,
      "vendor_name": "TI",
      "part_number": "SN74HC00N",
      "value": "5",
      "package": "DIP-14",
      "quantity": 10,
      "status": "raw",
      "merged_into": null
    }
  ],
  "step_count": 0,
  "max_steps": 30,
  "fields_remaining": 10,
  "last_reward": 0.0,
  "cumulative_reward": 0.0,
  "done": false,
  "hint_budget": 3,
  "last_action_result": null
}
```

> **Row Statuses:** `raw` (untouched) · `normalized` (agent acted) · `flagged` (anomaly) · `merged` (duplicate)

### Reward System

The environment provides **dense rewards** at every step to guide learning:

| Outcome | Reward | Description |
|:---|:---:|:---|
| ✅ Perfect field match | **+0.30** | New value exactly matches gold standard |
| ✅ Case-insensitive match | **+0.25** | Correct but wrong casing |
| ✅ Numerically equivalent | **+0.20** | Different notation, same numeric value |
| ✅ Correct duplicate merge | **+0.20** | Correctly identified a duplicate pair |
| 🔶 Substring match | **+0.15** | Partial match (one contains the other) |
| 🔶 High Levenshtein similarity (>0.7) | **+0.10** | Close but not exact |
| 🔶 Moderate similarity (>0.5) | **+0.05** | Somewhat similar |
| ⚪ Already correct (no-op) | **+0.02** | Field was already right |
| 🔻 Undo action | **−0.01** | Small cost to discourage excessive undos |
| 🔻 Inspect hint used | **−0.02** | Small cost for using a hint |
| ❌ Invalid action / wrong normalization | **−0.05** | Incorrect or missing parameters |
| ❌ Corrupting a correct field | **−0.15** | Changing a correct value to a wrong one |
| ⚡ Batch normalize | **±0.15/0.10** | +0.15 per correct row, −0.10 per wrong row |

### Grading & Scoring

When the agent calls `submit` or runs out of steps, a **final deterministic score** is computed:

<details>
<summary><strong>🟢 Easy Task Scoring</strong></summary>

Vendor accuracy with partial credit:
- **1.0** — exact match
- **0.8** — case-insensitive match
- **0.5** — substring match
- **0.3** — high similarity (Levenshtein > 0.7)
- Divided by total rows → score in `[0.0, 1.0]`

</details>

<details>
<summary><strong>🟡 Medium Task Scoring</strong></summary>

Three-field accuracy:
- **Vendor**: Same partial-credit scheme as Easy
- **Value**: 1.0 if numerically equivalent (handles unit conversion), else 0.0
- **Package**: 1.0 if normalized form matches, 0.5 for substring
- Divided by (rows × 3) → score in `[0.0, 1.0]`

</details>

<details>
<summary><strong>🔴 Hard Task Scoring</strong></summary>

Weighted composite:
- **50%** — Field normalization (same as Medium, for non-duplicate rows)
- **30%** — Duplicate detection (fraction of gold-standard pairs correctly merged)
- **20%** — Quantity aggregation (fraction of quantities matching gold)

</details>

---

## 🔧 Backend — Deep Dive

### Core Package (`bom_normalizer/`)

The `bom_normalizer` package is the heart of the project — a self-contained Python package that implements the OpenEnv interface and exposes it over HTTP.

```python
__version__ = "1.0.0"
__author__ = "Team Quasars"
```

<details>
<summary><strong>📦 Data Models — <code>models.py</code></strong></summary>

All data structures use **Pydantic v2** with `model_config = ConfigDict(extra='forbid')` for strict validation.

| Model | Purpose |
|:---|:---|
| `RowStatus` | Enum: `raw`, `normalized`, `flagged`, `merged` |
| `BOMRow` | Single BOM row with all fields + status tracking |
| `ActionType` | Enum of all 10 available actions |
| `Action` | Agent action with optional parameters |
| `Observation` | Full environment state returned to the agent |
| `Reward` | Immediate reward + reason + cumulative total |
| `StepResponse` | Combined response from `step()`: observation + reward + done + info |

</details>

<details>
<summary><strong>⚙️ BOM Generator — <code>generator.py</code></strong></summary>

The generator creates reproducible messy/gold BOM pairs from a seed integer.

**Canonical BOM**: A hard-coded array of 50 real electronics components from 24 manufacturer families covering:
- Logic ICs (SN74HC00N)
- Passive components (10kΩ resistors, 100nF capacitors)
- Microcontrollers (ATmega328P, STM32F103)
- Voltage regulators (LM7805, LT1763)
- Communication ICs (MAX232, TJA1050)
- Wireless modules (BCM43438, QCA9377)

**Corruption Pipeline**:
1. `_corrupt_vendor()` — Replaces canonical vendor names with random aliases
2. `_corrupt_value()` — Converts numeric values to human-readable variants
3. `_corrupt_package()` — Applies package variant mappings
4. `_corrupt_part()` — Applies part number variants
5. `_inject_duplicates()` — For Hard mode: creates 40 duplicate pairs
6. `_inject_edge_cases()` — For Hard mode: adds 10 tricky edge-case rows

</details>

<details>
<summary><strong>🔄 Environment Engine — <code>env.py</code></strong></summary>

The `BOMEnv` class implements the standard RL environment interface:

```python
class BOMEnv:
    def reset(self) -> Observation
    def step(self, action) -> (obs, reward, done, info)
    def state(self) -> Observation
```

**Key internal mechanics**:
- Maintains `_rows` (current state) and `_gold` (ground truth)
- Tracks `action_history` for undo functionality (deep-copied snapshots)
- Counts `fields_remaining` by comparing each row's fields against gold
- Episode ends on `submit` action or when `step_count >= max_steps`
- `info['score']` is populated on episode completion via the grader

</details>

<details>
<summary><strong>🎯 Reward Function — <code>reward.py</code></strong></summary>

`compute_reward(action, rows, gold)` returns a `(float, str)` tuple using:

1. **String similarity** — Custom Levenshtein distance implementation
2. **Numeric closeness** — `_numeric_close()` checks within 1% tolerance
3. **Duplicate verification** — `_is_true_duplicate()` checks gold-standard mappings
4. **Corruption detection** — Penalizes changing correct fields to wrong values (−0.15)

</details>

<details>
<summary><strong>📊 Grader — <code>grader.py</code></strong></summary>

Deterministic final scoring with specialized functions:

- `_levenshtein_similarity()` — Pure-Python edit distance for vendor comparison
- `_normalize_to_base_value()` — Parses unit prefixes (p/n/u/m/k/M/G) and base units
- `_are_values_equivalent()` — Compares value strings after unit normalization (1% tolerance)
- `_normalize_package_string()` — Strips hyphens, spaces, converts to uppercase
- `_grade_easy/medium/hard()` — Task-specific scoring with partial credit
- `_grade_quantities()` — Quantity match accuracy for non-merged rows

</details>

<details>
<summary><strong>🌐 FastAPI Server — <code>server.py</code></strong></summary>

**Core OpenEnv Endpoints** *(required by spec)*:

| Method | Endpoint | Description |
|:---|:---|:---|
| `GET` | `/health` | Health check |
| `GET` | `/tasks` | List available tasks |
| `POST` | `/reset?task_id=easy` | Reset environment |
| `POST` | `/step?task_id=easy` | Execute action |
| `GET` | `/state?task_id=easy` | Read current state |

**Extended Endpoints** *(custom features)*:

| Method | Endpoint | Description |
|:---|:---|:---|
| `POST` | `/upload-bom` | Upload Excel/CSV file as BOM data |
| `GET` | `/download-template` | Download sample Excel BOM template |
| `POST` | `/auto-normalize?task_id=easy` | AI-powered auto-normalization via LLM |

**Auto-normalize loop**: Sends batches of 20 raw rows to the LLM, parses JSON responses into actions, and repeats until complete or 5 consecutive failures.

**CORS**: Enabled for all origins (`*`).

</details>

<details>
<summary><strong>📋 Task Configs — <code>tasks.py</code></strong></summary>

```python
TASK_CONFIGS = {
    'easy':   { 'row_count': 10, 'max_steps': 30,  'fields_to_normalize': ['vendor_name'] },
    'medium': { 'row_count': 50, 'max_steps': 100, 'fields_to_normalize': ['vendor_name', 'value', 'package'] },
    'hard':   { 'row_count': 50, 'max_steps': 250, 'fields_to_normalize': ['vendor_name', 'value', 'package', 'part_number'],
                'duplicate_pairs': 40 },
}
```

Each task also defines a `baseline_score` and `grading_weights`.

</details>

---

## 🖥️ Frontend — Deep Dive

The frontend is a **React 18 + TypeScript** single-page application built with **Vite** and styled with **Tailwind CSS**.

### Tech Stack

| Library | Version | Purpose |
|:---|:---:|:---|
| React | 18.2 | UI framework |
| TypeScript | 5.2 | Type safety |
| Vite | 5.0 | Build tool + dev server |
| Tailwind CSS | 3.3 | Utility-first CSS |
| Axios | 1.6 | HTTP client |
| Lucide React | 0.294 | Icon library |
| clsx | 2.0 | Conditional class names |

### Components

| Component | Description |
|:---|:---|
| **`App.tsx`** | Main application — task selector, reset button, file upload, AI normalize, export |
| **`BOMTable.tsx`** | Interactive data table with color-coded status: 🔴 raw · 🟢 normalized · 🟡 flagged · 🔵 merged |
| **`ActionBuilder.tsx`** | Dynamic action form with dropdown selection and contextual input fields |
| **`EpisodeStats.tsx`** | Progress dashboard: steps, fields remaining, cumulative reward, done state |
| **`RewardLog.tsx`** | Auto-scrolling log of all rewards with value, reason, and cumulative total |

### API Proxy

```typescript
// vite.config.ts
proxy: {
  '/api': {
    target: 'http://localhost:7860',
    changeOrigin: true,
    rewrite: (path) => path.replace(/^\/api/, '')
  }
}
```

---

## 🤖 Inference Script

`inference.py` is the **competition-grade baseline agent** that uses an LLM to normalize BOMs automatically.

### How It Works

1. **Waits** for the environment server to come online (up to 60s)
2. **Runs all three tasks** sequentially: `easy` → `medium` → `hard`
3. **For each task**:
   - Calls `POST /reset` to start a new episode
   - Loops up to `max_steps` times, sending rows to the LLM and executing parsed actions
   - Logs `[STEP]` to stdout per OpenEnv spec
   - On completion, logs `[END]` with the final score

### Logging Format (OpenEnv Standard)

```
[START] task=easy env=bom-normalizer model=meta-llama/Llama-3.3-70B-Instruct
[STEP]  step=1  action=batch_normalize  reward=0.30  done=false  error=null
[STEP]  step=2  action=normalize_vendor  reward=0.25  done=false  error=null
...
[END]   success=true  steps=12  score=0.9500  rewards=0.30,0.25,...
```

---

## 🎬 Demo Script

`demo_normalization.py` is an **interactive CLI demo** with colorized terminal output:

| Demo | Description |
|:---:|:---|
| **1** | Easy task — shows 5 rows, normalizes 3 vendors, displays rewards |
| **2** | Medium task — normalizes vendor, value, and package for one row |
| **3** | Before/After comparison — normalizes all 10 Easy rows, submits for grading |
| **4** | Interactive — step through normalization with Enter key |

```bash
# Start the backend first, then:
python demo_normalization.py
```

---

## 📁 Data Files

<details>
<summary><strong><code>data/vendor_aliases.json</code></strong> — 24 vendors, 140+ aliases</summary>

```json
{
  "Texas Instruments": ["TI", "T.I.", "Texas Inst.", "Texas Instru.", "TI Inc"],
  "Murata Manufacturing": ["Murata", "Murata Mfg", "MURATA"],
  "STMicroelectronics": ["ST", "STM", "STMicro", "ST Micro"]
}
```

</details>

<details>
<summary><strong><code>data/unit_variants.json</code></strong> — 8 measurement categories</summary>

| Category | Units Covered |
|:---|:---|
| Resistance | Ω, kΩ, MΩ (+ text variants: ohm, kohm, etc.) |
| Capacitance | F, mF, µF, nF, pF |
| Inductance | µH, mH, nH (with multipliers) |
| Voltage | 3v3 → 3.3, 5v0 → 5.0, etc. |
| Current | A, mA, µA |
| Frequency | Hz, kHz, MHz, GHz |
| Power | W, mW, kW |
| Length / Weight | mm, cm, m, inch, ft / kg, g, mg, lb, oz |

</details>

<details>
<summary><strong><code>data/part_numbers.json</code></strong> — Canonical parts + package variants</summary>

- **`canonical_parts`** — Maps 10 canonical part numbers to their common variants
  - e.g., `SN74HC00N` → `["74HC00", "74HC00N", "SN74HC00", "HC00"]`
- **`package_variants`** — Maps 10 canonical package codes to variants
  - e.g., `SOT-23` → `["SOT23", "SOT23-3", "SOT-23-3", "SOT23/3"]`

</details>

---

## 📡 API Reference

| Method | Endpoint | Description |
|:---|:---|:---|
| `GET` | `/health` | Returns `{"status": "ok", "version": "1.0.0"}` |
| `GET` | `/tasks` | List available tasks and descriptions |
| `POST` | `/reset?task_id={easy\|medium\|hard}` | Reset environment, returns initial `Observation` |
| `POST` | `/step?task_id={easy\|medium\|hard}` | Execute action, returns `StepResponse` |
| `GET` | `/state?task_id={easy\|medium\|hard}` | Get current state without advancing |
| `POST` | `/upload-bom?task_id={easy\|medium\|hard}` | Upload Excel/CSV file (multipart form) |
| `GET` | `/download-template` | Download sample BOM Excel template |
| `POST` | `/auto-normalize?task_id={easy\|medium\|hard}` | Run AI auto-normalization |

### Example Request

```bash
curl -X POST "http://localhost:7860/step?task_id=easy" \
  -H "Content-Type: application/json" \
  -d '{"action_type": "normalize_vendor", "row_id": 1, "new_value": "Texas Instruments"}'
```

> 📖 **Interactive Docs**: Visit **http://localhost:7860/docs** for the auto-generated Swagger UI.

---

## ⚙️ Configuration Files

| File | Purpose |
|:---|:---|
| `pyproject.toml` | Python project metadata, dependencies, build system, ruff/pytest config |
| `requirements.txt` | Pinned production dependencies |
| `openenv.yaml` | OpenEnv environment specification (tasks, action/obs space, reward, endpoints) |
| `Dockerfile` | Container build: Python 3.11-slim, port 7860, health check |
| `.env.example` | Template for environment variables |
| `.gitignore` | Exclusions for Python, Node.js, IDE, OS files |
| `.dockerignore` | Exclusions for Docker build context |
| `validate-submission.ps1` | PowerShell script to validate competition submission |
| `validate-submission.sh` | Bash script to validate competition submission |

---

## 🛠️ Development

### Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linter
ruff check .
```

### Code Quality

- **Ruff** — Python linting (line length: 100, target: Python 3.10)
- **TypeScript strict mode** — Frontend type checking
- **Pydantic v2 strict validation** — `extra='forbid'` for API models
- **ESLint** — Frontend code quality

### Adding New Vendors

1. Add the canonical name and aliases to `data/vendor_aliases.json`
2. Add corresponding normalizations to the `SYSTEM_PROMPT` in `server.py` and `inference.py`
3. If needed, add entries to `CANONICAL_BOM` in `generator.py`

### Adding New Task Difficulty

1. Add a new entry to `TASK_CONFIGS` in `tasks.py`
2. Add the corresponding `_grade_<level>()` function in `grader.py`
3. Update the `_task_configs` dict in `env.py`
4. Add the difficulty to the `lifespan()` function in `server.py`

---

## 📄 License

This project is licensed under the **MIT License**. See [pyproject.toml](pyproject.toml) for full metadata.

---

<p align="center">
  Built with 🧪 by <strong>Team Quasars</strong> for OpenEnv Hackathon 2025
</p>
