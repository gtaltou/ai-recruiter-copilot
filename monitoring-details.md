# Documentation du Monitoring

Ce document détaille l'implémentation du monitoring pour l'AI Recruiter Copilot.

## 🏗️ Architecture du Monitoring

L'infrastructure de monitoring repose sur trois piliers :
1. **Application (FastAPI)** : Expose les métriques via `prometheus_client`.
2. **Prometheus** : Collecte (scrapes) les métriques à intervalles réguliers.
3. **Grafana** : Visualise les données via des tableaux de bord.

## 📈 Métriques Exposées

L'application expose des métriques personnalisées pour suivre les performances de l'IA :

- `http_requests_total` : Nombre total de requêtes par méthode et endpoint.
- `cv_analysis_duration_seconds` : Temps de traitement de l'analyse des CV par l'IA.
- `token_usage_total` : Consommation de tokens OpenAI.
- `active_analysis_count` : Nombre d'analyses en cours de traitement.

## 🐳 Configuration Docker

Le monitoring est isolé dans son propre fichier de composition pour plus de flexibilité.

```yaml
# docker-compose.monitoring.yml
services:
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
