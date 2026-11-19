
---

## 📄 `monitoring-guide.md`

```markdown
# Guide de Monitoring - AI Recruiter Copilot

Ce document détaille l'implémentation de la stack d'observabilité utilisant Prometheus et Grafana.

## 🏗 Architecture

L'application expose un endpoint `/metrics` au format Prometheus. La stack est composée de trois éléments principaux :
1.  **FastAPI App** : Génère les métriques via un middleware personnalisé (`MetricsMiddleware`).
2.  **Prometheus** : Récupère (scrape) les données de l'application toutes les 15 secondes.
3.  **Grafana** : Visualise les données stockées dans Prometheus via des tableaux de bord.

## 📊 Métriques Exposées

| Métrique | Type | Description |
| :--- | :--- | :--- |
| `http_requests_total` | Counter | Nombre total de requêtes HTTP (labels: `method`, `endpoint`, `status`). |
| `http_request_duration_seconds` | Histogram | Latence des requêtes en secondes. |
| `http_requests_in_progress` | Gauge | Nombre de requêtes en cours de traitement. |
| `app_info` | Gauge | Informations statiques (version, nom de l'application). |

## 🚀 Déploiement

### 1. Configuration Docker
Le fichier `docker-compose.monitoring.yml` gère les services.
- **Prometheus** : Accessible sur `http://localhost:9090`
- **Grafana** : Accessible sur `http://localhost:3000` (admin/admin)

### 2. Configuration du Scrape
Le fichier `./prometheus/prometheus.yml` est configuré pour cibler l'application :
- Cible locale : `host.docker.internal:8000` (pour l'application lancée hors Docker).
- Cible réseau : `app:8000` (pour l'application lancée via Docker Compose).

## 🛠 Commandes Utiles

### Vérifier l'exposition des métriques
```powershell
# Depuis PowerShell
curl.exe http://localhost:8000/metrics
