# Arquitectura para Escala

Sistema diseñado para **50M registros** y **miles de consultas/segundo**.

---

## Escenario A: Arquitectura Clásica (Ingeniería de Datos)

### Diagrama

```
                                    ┌─────────────────┐
                                    │   CloudFront    │
                                    │   (CDN/Cache)   │
                                    └────────┬────────┘
                                             │
                                    ┌────────▼────────┐
                                    │  Load Balancer  │
                                    │   (ALB/NLB)     │
                                    └────────┬────────┘
                                             │
              ┌──────────────────────────────┼──────────────────────────────┐
              │                              │                              │
     ┌────────▼────────┐           ┌────────▼────────┐           ┌────────▼────────┐
     │   API Server    │           │   API Server    │           │   API Server    │
     │   (FastAPI)     │           │   (FastAPI)     │           │   (FastAPI)     │
     └────────┬────────┘           └────────┬────────┘           └────────┬────────┘
              │                              │                              │
              └──────────────────────────────┼──────────────────────────────┘
                                             │
                              ┌──────────────┴──────────────┐
                              │                             │
                     ┌────────▼────────┐          ┌────────▼────────┐
                     │  Redis Cluster  │          │  Elasticsearch  │
                     │  (Query Cache)  │          │    Cluster      │
                     │                 │          │   (3+ nodes)    │
                     │  - LRU eviction │          │   - Sharding    │
                     │  - TTL 10 min   │          │   - Replicas    │
                     └─────────────────┘          └─────────────────┘
```

### Componentes

#### 1. Elasticsearch Cluster

**Ventajas:**
- Motor de búsqueda diseñado para texto y fuzzy matching
- Soporte nativo para n-gramas y análisis fonético
- Escalamiento horizontal con sharding
- Scoring de relevancia built-in
- Latencia: 5-20ms

**Configuración de índice:**
```json
{
  "settings": {
    "number_of_shards": 15,
    "number_of_replicas": 2,
    "analysis": {
      "analyzer": {
        "name_analyzer": {
          "tokenizer": "standard",
          "filter": ["lowercase", "asciifolding", "phonetic_metaphone"]
        }
      },
      "filter": {
        "phonetic_metaphone": {
          "type": "phonetic",
          "encoder": "metaphone"
        }
      }
    }
  },
  "mappings": {
    "properties": {
      "id": {"type": "keyword"},
      "name": {
        "type": "text",
        "analyzer": "name_analyzer",
        "fields": {
          "exact": {"type": "keyword"},
          "ngram": {
            "type": "text",
            "analyzer": "ngram_analyzer"
          }
        }
      }
    }
  }
}
```

**Estrategia de sharding:**
- 15-20 shards para 50M registros (~2.5-3.3M por shard)
- 2-3 réplicas por shard para throughput de lectura
- Distribución balanceada por hash de ID

#### 2. Redis Cluster (Capa de Cache)

**Estrategia de cache:**
```python
# Clave: hash del query normalizado
cache_key = f"search:{hash(normalize(name) + str(threshold))}"

# TTL: 10 minutos (balance entre frescura y hit rate)
TTL = 600

# Invalidación: Por pub/sub cuando se actualiza el dataset
```

**Beneficios:**
- Reduce carga en Elasticsearch ~60-80%
- Latencia de cache hit: <1ms
- LRU eviction para gestión automática de memoria

#### 3. API Servers (Stateless)

- Auto-scaling horizontal (K8s HPA / ECS)
- Connection pooling a Elasticsearch
- Circuit breakers (Hystrix/Resilience4j) para tolerancia a fallos
- Health checks para load balancer

### Estrategia de Disponibilidad

| Componente | Estrategia | RTO |
|------------|------------|-----|
| API Servers | Multi-AZ, auto-scaling | <30s |
| Redis | Cluster mode, replicas | <5s |
| Elasticsearch | Multi-node, replicas | <60s |

---

## Escenario B: Arquitectura AI-Native (100% IA)

### Diagrama

```
                                    ┌─────────────────┐
                                    │   API Gateway   │
                                    └────────┬────────┘
                                             │
                              ┌──────────────┴──────────────┐
                              │                             │
                     ┌────────▼────────┐           ┌────────▼────────┐
                     │  Query Service  │           │   Redis Cache   │
                     │   (Embedding    │           │   (Vector +     │
                     │    Generation)  │           │    Results)     │
                     └────────┬────────┘           └────────┬────────┘
                              │                             │
                              └──────────────┬──────────────┘
                                             │
                              ┌──────────────▼──────────────┐
                              │      Vector Database        │
                              │   (Pinecone / Qdrant /      │
                              │    Milvus / Weaviate)       │
                              │                             │
                              │   50M vectors @ 384 dims    │
                              │   HNSW index               │
                              └─────────────────────────────┘
```

### 1. Representación: Embeddings

**Modelo recomendado:**
```python
from sentence_transformers import SentenceTransformer

# Modelo optimizado para texto corto y multilingüe
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

# Indexación (batch)
embeddings = model.encode(names_list, batch_size=256, show_progress_bar=True)
# Resultado: 50M vectores de 384 dimensiones

# Query en tiempo real
query_embedding = model.encode(input_name)  # ~10ms
```

**Ventajas del modelo:**
- Multilingüe con soporte completo para español y acentos
- Compacto: 384 dimensiones = búsquedas rápidas
- Similitud semántica optimizada para textos cortos
- Inference rápida: ~10ms por query

### 2. Almacenamiento y Búsqueda Vectorial

**Comparación de Vector DBs:**

| Característica | Pinecone | Qdrant | Milvus |
|----------------|----------|--------|--------|
| Managed | Sí | Opcional | No |
| Escala | Excelente | Buena | Buena |
| Latencia | ~10ms | ~15ms | ~20ms |
| Costo | $$$ | $$ | $ |
| Filtrado | Sí | Sí | Sí |

**Recomendación:**
- **Producción enterprise**: Pinecone (fully managed, SLA)
- **Balance costo/control**: Qdrant (self-hosted o cloud)
- **On-premise**: Milvus

**Configuración de índice HNSW:**
```python
# Parámetros para 50M vectores
index_config = {
    "metric": "cosine",           # Similitud coseno
    "hnsw": {
        "M": 16,                  # Conexiones por nodo
        "ef_construction": 200,   # Calidad de construcción
        "ef_search": 100          # Calidad de búsqueda
    }
}
# Complejidad búsqueda: O(log n) ≈ ~25 operaciones para 50M
```

### 3. Estrategia de Cache (Crítico para Performance)

**Cache de dos niveles:**

```
┌─────────────────────────────────────────────────┐
│                  Nivel 1: Query Cache           │
│  Key: hash(normalized_query)                    │
│  Value: lista de IDs + scores                   │
│  TTL: 15 minutos                                │
│  Hit rate esperado: 40-60%                      │
└─────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────┐
│              Nivel 2: Embedding Cache           │
│  Key: hash(normalized_query)                    │
│  Value: vector embedding (384 floats)           │
│  TTL: 1 hora                                    │
│  Evita re-computar embeddings                   │
└─────────────────────────────────────────────────┘
```

**Implementación:**
```python
async def search_with_cache(query: str, threshold: float):
    # Nivel 1: Cache de resultados completos
    cache_key = f"results:{hash(normalize(query))}:{threshold}"
    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached)

    # Nivel 2: Cache de embeddings
    emb_key = f"embedding:{hash(normalize(query))}"
    embedding = await redis.get(emb_key)
    if not embedding:
        embedding = model.encode(query)
        await redis.setex(emb_key, 3600, embedding.tobytes())

    # Búsqueda vectorial
    results = vector_db.search(embedding, top_k=100)

    # Filtrar por threshold y cachear
    filtered = [r for r in results if r.score >= threshold/100]
    await redis.setex(cache_key, 900, json.dumps(filtered))

    return filtered
```

### Performance Esperado

| Métrica | Valor |
|---------|-------|
| Latencia p50 (cache hit) | <5ms |
| Latencia p50 (cache miss) | ~30ms |
| Latencia p99 | <100ms |
| Throughput | 5000+ QPS |
| Cache hit rate | 50-70% |

---

## Comparación: Clásica vs AI-Native

| Aspecto | Clásica (ES) | AI-Native (Vector) |
|---------|--------------|-------------------|
| **Precisión** | Buena (reglas) | Excelente (semántica) |
| **Latencia** | 5-20ms | 15-50ms |
| **Costo** | $$ | $$$ |
| **Complejidad** | Media | Alta |
| **Typos** | Bueno | Excelente |
| **Fonética** | Configurable | Incorporado |
| **Mantenimiento** | Bajo | Medio |
| **Escalabilidad** | Excelente | Excelente |

### Recomendación Final

1. **MVP/Producción inicial**: Arquitectura Clásica con Elasticsearch
   - Probada, económica, fácil de operar
   - Suficiente para la mayoría de casos de uso

2. **Evolución futura**: Añadir capa AI para casos edge
   - Embeddings para queries que fallan con ES
   - Modelo híbrido: ES primero, fallback a vectores

3. **Full AI-Native**: Solo si hay requerimientos específicos
   - Matching semántico complejo
   - Nombres en múltiples idiomas/scripts
   - Budget y equipo para mantener ML infra

---

## Arquitectura Híbrida (Mejor de ambos mundos)

```
                          ┌─────────────┐
                          │   Request   │
                          └──────┬──────┘
                                 │
                          ┌──────▼──────┐
                          │    Cache    │
                          │   (Redis)   │
                          └──────┬──────┘
                                 │
                    ┌────────────┴────────────┐
                    │                         │
             ┌──────▼──────┐          ┌──────▼──────┐
             │Elasticsearch│          │  Vector DB  │
             │  (Primary)  │          │ (Fallback)  │
             └──────┬──────┘          └──────┬──────┘
                    │                         │
                    │     Si ES < threshold   │
                    └─────────────────────────┘
```

Esta arquitectura usa Elasticsearch como búsqueda primaria y recurre a búsqueda vectorial solo cuando ES no encuentra matches suficientemente buenos, optimizando costo y latencia mientras mantiene alta precisión.
