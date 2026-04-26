# Graphical Simulator for Resource Allocation Graph

A lightweight **interactive website** for drawing **Resource Allocation Graphs (RAGs)** and detecting **deadlocks** in **single-instance** resource systems.

This project is consist of two modules:
- **Frontend (Web UI):** Cytoscape.js graph editor/visualizer
- **Backend (Python API):** FastAPI + NetworkX deadlock detection

Deadlock detection is **cycle-based**: a deadlock exists if the graph contains a directed cycle that includes both **request** and **allocation** edges.

---

## Features

- Interactive editor to add:
  - **Processes** (`P1`, `P2`, ...)
  - **Resources** (`R1`, `R2`, ...)
- Create edges:
  - **Request edge:** `Process → Resource`
  - **Allocation edge:** `Resource → Process`
- **Deadlock detection** via API
- Highlights deadlocked cycles directly on the graph
- Clean, structured output panel:
  - deadlock status
  - message
  - cycles list
  - highlighted nodes/edges

---

## How deadlock detection works

In a single-instance RAG:
- A cycle in the graph implies circular waiting.
- The backend finds directed cycles and reports those that include:
  - at least one **allocation** edge (resource held by a process), and
  - at least one **request** edge (process waiting for a resource).

---

## Project structure

```
graphical-simulator-for-resource-allocation-graph/
  api/
    main.py              # FastAPI backend + deadlock detection (NetworkX)
    requirements.txt     # Python dependencies
  web/
    index.html           # Cytoscape.js UI (interactive graph editor)
```

---

## Requirements

- Python **3.10+** recommended
- A modern browser (Chrome/Firefox/Edge)
- Internet connection

---

## Installation & Run (Local)

### 1) Start the backend API

```bash
cd rag-web/api
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### 2) Start the frontend

In a second terminal:

```bash
cd rag-web/web
python -m http.server 8080
```

Open in browser:
- `http://localhost:8080`

Make sure **API base URL** in the UI is set to:
- `http://localhost:8000`

---

## Usage

### Build a simple deadlock example

1. Add nodes: `P1`, `P2`, `R1`, `R2`
2. Create allocation edges:
   - `R1 → P1`
   - `R2 → P2`
3. Create request edges:
   - `P1 → R2`
   - `P2 → R1`
4. Click **Analyze deadlock**

Expected:
- Deadlock detected
- Cycle nodes/edges are highlighted in red

### Notes

- **Request** edges must be `Process → Resource`
- **Allocation** edges must be `Resource → Process`
- This simulator is intended for **single-instance** resources (each resource has at most one active allocation).
