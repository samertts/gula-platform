# PI-005 — Performance Report

## AI Platform Performance Benchmarks

**Version:** 2.1.0
**Date:** July 2026

---

## 1. AI Service Latency

| Service | P50 | P95 | P99 | Target | Status |
|---------|-----|-----|-----|--------|--------|
| Drug Interaction Check | 350ms | 800ms | 1.5s | < 1s | ✅ |
| Critical Result Detection | 120ms | 300ms | 600ms | < 500ms | ✅ |
| Clinical Pathway Suggestion | 500ms | 1.2s | 2s | < 2s | ✅ |
| Bed Occupancy Prediction | 150ms | 350ms | 700ms | < 500ms | ✅ |
| Disease Forecasting | 800ms | 2s | 4s | < 3s | ✅ |
| Resource Optimization | 200ms | 500ms | 1s | < 1s | ✅ |
| Failure Prediction | 50ms | 150ms | 300ms | < 200ms | ✅ |
| Citizen Health Assistant | 1.2s | 3s | 5s | < 3s | ✅ |
| Explainability Generation | 200ms | 450ms | 900ms | < 500ms | ✅ |
| Bias Detection | 300ms | 700ms | 1.2s | < 1s | ✅ |
| Model Registry Query | 10ms | 30ms | 60ms | < 100ms | ✅ |
| Prompt Registry Query | 5ms | 15ms | 30ms | < 50ms | ✅ |

---

## 2. Throughput

| Service | Current QPS | Max QPS | Headroom |
|---------|-------------|---------|----------|
| Drug Interaction Check | 8/s | 50/s | 84% |
| Critical Result Detection | 15/s | 100/s | 85% |
| Clinical Pathways | 5/s | 30/s | 83% |
| Bed Occupancy | 5/s | 40/s | 87.5% |
| Disease Forecasting | 1/s | 10/s | 90% |
| Resource Optimization | 3/s | 25/s | 88% |
| Failure Prediction | 10/s | 80/s | 87.5% |
| Health Assistant | 2/s | 20/s | 90% |

---

## 3. Model Inference Performance

| Model | Batch Size | Inference Time | Throughput | GPU Memory |
|-------|-----------|----------------|------------|------------|
| Drug Interaction (XGBoost) | 1 | 15ms | 1,000/s | CPU only |
| Critical Result (Random Forest) | 1 | 8ms | 2,000/s | CPU only |
| Clinical Pathway (LLM) | 1 | 800ms | 20/s | 8GB |
| Bed Occupancy (LSTM) | 32 | 45ms | 700/s | 2GB |
| Disease Forecast (Transformer) | 64 | 120ms | 500/s | 4GB |
| Health Assistant (LLM) | 1 | 1.2s | 10/s | 16GB |

---

## 4. Resource Utilization

| Component | CPU | Memory | GPU | Storage |
|-----------|-----|--------|-----|---------|
| LLM Gateway | 25% | 4GB | 0% | 10GB |
| Model Serving (CPU) | 35% | 8GB | — | 20GB |
| Model Serving (GPU) | 15% | 16GB | 1× A10G (45%) | 30GB |
| Vector Database | 20% | 8GB | — | 50GB |
| Model Registry | 5% | 2GB | — | 10GB |
| Prompt Registry | 2% | 1GB | — | 5GB |

---

## 5. Model Registry Benchmarks

| Operation | Records | P50 | P95 | P99 |
|-----------|---------|-----|-----|-----|
| Register model | 10K | 5ms | 12ms | 25ms |
| Get model by ID | 10K | 2ms | 5ms | 10ms |
| Query by status | 10K | 8ms | 20ms | 40ms |
| Query by tags | 10K | 12ms | 30ms | 60ms |
| Get lineage | 1K models | 15ms | 40ms | 80ms |
| Add deployment record | 50K | 3ms | 8ms | 15ms |
| Full registry scan | 10K | 50ms | 100ms | 200ms |

---

## 6. Bias Detector Benchmarks

| Operation | Dataset Size | P50 | P95 | P99 |
|-----------|-------------|-----|-----|-----|
| Dataset analysis | 1K samples | 25ms | 60ms | 120ms |
| Dataset analysis | 10K samples | 150ms | 350ms | 700ms |
| Dataset analysis | 100K samples | 1.2s | 2.5s | 5s |
| Prediction analysis | 1K predictions | 30ms | 70ms | 150ms |
| Prediction analysis | 10K predictions | 200ms | 500ms | 1s |
| Mitigation suggestions | Any | 5ms | 10ms | 20ms |

---

## 7. Performance vs. Accuracy Trade-off

| Model | Performance (P50) | Accuracy | Optimized For |
|-------|-------------------|----------|---------------|
| Drug Interaction v1.0 | 200ms | 97.5% | Speed |
| Drug Interaction v1.1 | 350ms | 99.2% | Accuracy |
| Disease Forecast v0.9 | 500ms | 83.4% | Speed |
| Disease Forecast v1.0 | 800ms | 87.5% | Accuracy |
| Health Assistant v0.8 | 800ms | 89.2% | Speed |
| Health Assistant v1.0 | 1.2s | 92.4% | Accuracy |

---

## 8. Scaling Profile

| Service | Min Instances | Max Instances | Scale Trigger | QPS per Instance |
|---------|--------------|---------------|---------------|------------------|
| LLM Gateway | 1 | 5 | CPU > 60% | 20 req/s |
| Model Serving (CPU) | 2 | 10 | Queue depth > 50 | 100 req/s |
| Model Serving (GPU) | 1 | 3 | GPU memory > 80% | 30 req/s |
| Vector DB | 1 | 3 | CPU > 50% | 500 q/s |
| Registry | 1 | 3 | Latency > 100ms | 500 q/s |
