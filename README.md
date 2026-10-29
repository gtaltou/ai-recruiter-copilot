# AI Recruiter Copilot

Assistant IA de recrutement — Analyse de CV, matching intelligent avec descriptions de poste, et export structuré des résultats. Propulsé par LangGraph, ChromaDB et LiteLLM.

---

## Stack technique

| Catégorie | Technologie |
| :-------- | :---------- |
| **API** | FastAPI (Python 3.12+) |
| **AI / Orchestration** | LangGraph |
| **LLM** | LiteLLM (multi-provider : OpenAI, Anthropic, Ollama…) |
| **Vector Store** | ChromaDB (embedding + retrieval) |
| **Validation** | Pydantic v2 / pydantic-settings |
| **Auth** | JWT (PyJWT) |
| **Tests** | pytest, pytest-asyncio, Locust (load testing) |
| **CI/CD** | GitHub Actions |
| **Container** | Docker / Docker Compose |
| **Déploiement** | AWS ECS (Fargate) |

---

## Architecture

```
┌─────────────┐     ┌──────────────────────────────────────┐
│   Client    │────▶│           FastAPI (API Gateway)       │
└─────────────┘     │  - JWT Auth Middleware                │
                    │  - Rate Limiting                      │
                    │  - CORS                               │
                    └───────────┬──────────────────────────┘
                                │
                    ┌───────────▼──────────────────────────┐
                    │       LangGraph Agent Workflow       │
                    │                                      │
                    │  ┌─────────────┐  ┌───────────────┐  │
                    │  │ Orchestrator│─▶│  CV Analyzer   │  │
                    │  └─────────────┘  └───────┬───────┘  │
                    │                           │          │
                    │  ┌─────────────┐  ┌───────▼───────┐  │
                    │  │    RAG      │◀─│   Matcher     │  │
                    │  │ (ChromaDB)  │  └───────────────┘  │
                    │  └─────────────┘                     │
                    └──────────────────────────────────────┘
```

---

## Prérequis

- Python 3.12+
- Docker & Docker Compose (optionnel, recommandé)
- Une clé API pour au moins un fournisseur LLM (OpenAI, Anthropic, etc.)

---

## Installation & Setup

### 1. Cloner le dépôt

```bash
git clone https://github.com/<ton-org>/ai-recruiter-copilot.git
cd ai-recruiter-copilot
```

### 2. Environnement virtuel

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1   # Windows
# ou source .venv/bin/activate  # Linux/Mac
```

### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 4. Configuration

Crée un fichier `.env` à la racine :

```env
# LLM
LITELLM_API_KEY=sk-...
LITELLM_MODEL=gpt-4o

# Base de données vectorielle
CHROMA_PERSIST_DIR=./data/chroma

# JWT
JWT_SECRET_KEY=change-me-to-a-random-secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000
```

---

## Lancer l'API

### Local (sans Docker)

```bash
uvicorn app.main:app --reload --port 8000
```

API disponible sur `http://localhost:8000`  
Docs : `http://localhost:8000/docs` (Swagger)  
 ou `http://localhost:8000/redoc` (ReDoc)

### Avec Docker Compose

```bash
docker-compose up --build
```

Lance l'API + une instance ChromaDB persistante.

---

## Authentification (JWT)

Tous les endpoints (sauf `/api/v1/auth/token` et `/docs`) sont protégés par JWT.

### Obtenir un token

```bash
curl -X POST "http://localhost:8000/api/v1/auth/token" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}'
```

### Utiliser le token

```bash
curl -X POST "http://localhost:8000/api/v1/analyze" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "cv": {"nom_complet": "Jean Dupont", "competences": [...]},
    "job_description": {"titre": "Data Engineer", ...}
  }'
```

---

## Endpoints disponibles

| Méthode | Path | Description |
| :------ | :--- | :---------- |
| `POST` | `/api/v1/auth/token` | Obtenir un JWT |
| `POST` | `/api/v1/analyze` | Analyser un CV vs description de poste |
| `GET` | `/api/v1/export/csv` | Exporter les résultats en CSV |
| `GET` | `/api/v1/export/json` | Exporter les résultats en JSON |
| `GET` | `/health` | Health check |

---

## Tests

### Tests unitaires & d'intégration

```bash
pytest -v
```

### Test de charge (Locust)

```bash
locust -f tests/locustfile.py --host=http://localhost:8000
```

Ouvrir `http://localhost:9090` dans le navigateur.

---

## Déploiement (AWS ECS)

Le dossier `deploy/` contient la définition de tâche ECS Fargate :

- `deploy/ecs-task-definition.json` — tâche Fargate avec conteneur API
- `docker-compose.yml` — environnement local identique au déploiement

---

## CI/CD

À chaque push sur `develop` ou `main`, GitHub Actions :

1. Installe les dépendances
2. Exécute les tests (`pytest`)
3. Vérifie le linting
4. Construit l'image Docker (si configuré)

---

## Roadmap

- [x] **Sprint 1** — Setup, schémas Pydantic, tests CI
- [x] **Sprint 2** — Pipeline AI (LangGraph + ChromaDB + LiteLLM)
- [x] **Sprint 3** — Production Ready (Auth JWT, Docker, ECS, Rate Limiting, Export)
- [ ] **Sprint 4** — Monitoring, logging, observabilité
- [ ] **Sprint 5** — UI / Dashboard
- [ ] **Sprint 6** — Multi-tenancy & scaling

---

## Licence

MIT