# Name Similarity API

API que recibe un nombre y verifica su similitud contra una base de datos histórica para identificar posibles coincidencias.

## Instalación

```bash
# Crear entorno virtual (opcional pero recomendado)
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

## Ejecución

```bash
# Iniciar el servidor
uvicorn app.main:app --host 0.0.0.0 --port 8000

# El servidor estará disponible en http://localhost:8000
```

## Uso de la API

### Buscar nombres similares

```bash
GET /search?name={nombre}&threshold={umbral}&limit={max_resultados}&use_blocking={true|false}&spanish_mode={true|false}
```

**Parámetros:**
- `name` (string, requerido): Nombre completo a buscar
- `threshold` (float, opcional, default=70): Umbral mínimo de similitud (0-100)
- `limit` (int, opcional, default=100): Máximo número de resultados a retornar (1-1000)
- `use_blocking` (bool, opcional, default=true): Usar bloqueo por prefijo para mejor rendimiento
- `spanish_mode` (bool, opcional, default=false): Activar procesamiento de nombres españoles

**Ejemplos:**

Búsqueda básica:
```bash
curl "http://localhost:8000/search?name=Juan%20Garcia&threshold=80"
```

Búsqueda con modo español (maneja partículas y apodos):
```bash
curl "http://localhost:8000/search?name=Pepe%20de%20la%20Cruz&spanish_mode=true"
```

Búsqueda limitada a top 10 resultados:
```bash
curl "http://localhost:8000/search?name=Maria%20Lopez&threshold=70&limit=10"
```

**Respuesta:**
```json
{
  "123": {"name": "Juan García López", "similarity": 95.5},
  "456": {"name": "Juan Garcia Perez", "similarity": 88.2}
}
```

### Health Check

```bash
GET /health
```

**Respuesta:**
```json
{"status": "healthy", "records_loaded": 1000}
```

### Documentación interactiva

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Tests

```bash
python3 -m pytest tests/ -v
```

## Estructura del Proyecto

```
ml-challenge/
├── app/
│   ├── main.py              # API FastAPI
│   ├── services/
│   │   ├── normalizer.py    # Normalización de texto
│   │   └── similarity.py    # Cálculo Jaro-Winkler
│   └── repositories/
│       └── names.py         # Carga de datos
├── tests/
│   ├── test_normalizer.py
│   ├── test_similarity.py
│   └── test_repository.py
├── scripts/
│   └── benchmark_performance.py  # Benchmark de rendimiento
├── names_dataset.csv        # 5000 nombres españoles
├── requirements.txt
├── README.md
└── ARCHITECTURE.md
```

---

## Mejoras Implementadas

### Performance
- **RapidFuzz**: Reemplazo de implementación Python pura por librería optimizada en C++ (10-50x más rápida)
- **Prefix Blocking**: Sistema de indexación por prefijo que reduce comparaciones de O(N) a O(N/k)
- **Limit Parameter**: Control de resultados máximos para prevenir respuestas excesivamente grandes

### Funcionalidad
- **Modo Español**: Soporte específico para nombres hispanos con:
  - 20+ apodos comunes (Pepe, Paco, Nacho, Lupe, etc.)
  - Eliminación de partículas (de, del, de la, de los, de las, y)
- **API mejorada**: Parámetros adicionales para control fino de búsqueda

### Calidad
- **40 tests unitarios**: Cobertura completa de normalización, similitud y repositorio
- **Tests de Spanish mode**: Validación de partículas y apodos
- **Tests de blocking**: Verificación de indexación por prefijo

---

## Algoritmo: Jaro-Winkler (RapidFuzz)

### ¿Por qué Jaro-Winkler?

1. **Diseñado para nombres**: Originalmente creado para enlace de registros en datos censales
2. **Bonus por prefijo**: Da mayor puntuación cuando los strings coinciden desde el inicio (crítico para nombres)
3. **Maneja transposiciones**: "García" vs "Graica" obtiene mejor score que con Levenshtein
4. **Rango 0-1**: Se mapea naturalmente a porcentaje (× 100)
5. **Validado académicamente**: Estudios de CMU confirman su superioridad para matching de nombres

### Implementación: RapidFuzz

Utilizamos [RapidFuzz](https://github.com/rapidfuzz/RapidFuzz), una implementación optimizada en C++ con soporte SIMD:
- **10-50x más rápido** que implementaciones en Python puro
- Complejidad O(|S1|×|S2|) optimizada con operaciones bitwise
- Ampliamente usada en producción (Pandas, Polars, etc.)

### Optimizaciones de Rendimiento

#### 1. Prefix Blocking
Reduce el espacio de comparación de N a ~N/676:
- Agrupa nombres por los primeros 2 caracteres normalizados
- Solo compara nombres con prefijos similares
- Configurable vía parámetro `use_blocking`

#### 2. Modo Español
Mejora precisión para nombres hispanos:
- **Eliminación de partículas**: "de", "del", "de la", "de los", "de las"
- **Resolución de apodos**: Pepe→Jose, Paco→Francisco, Nacho→Ignacio, etc.
- Configurable vía parámetro `spanish_mode`

### Pipeline de preprocesamiento

**Modo estándar:**
1. Conversión a minúsculas
2. Normalización Unicode (NFD)
3. Eliminación de acentos
4. Colapso de espacios múltiples
5. Trim de espacios

**Modo español (spanish_mode=true):**
1. Pipeline estándar
2. Resolución de apodos comunes
3. Eliminación de partículas

### Ejemplos de similitud

| Nombre 1 | Nombre 2 | Modo | Similitud |
|----------|----------|------|-----------|
| Juan García | juan garcia | Estándar | 100% |
| María López | maria lopez | Estándar | 100% |
| Juan García | Juan Garsia | Estándar | ~95% |
| Pepe García | Jose García | Español | 100% |
| Juan de la Cruz | Juan Cruz | Español | 100% |
| Juan García | Pedro López | Estándar | ~55% |

---

## Dataset

El proyecto utiliza `names_dataset.csv` con **5000 registros** de nombres españoles:

Estructura:
```csv
ID,Full Name
1,María Sánchez
2,Marta Alonso
3,Javier González
...
```

**Características:**
- 5000 nombres reales españoles
- Variaciones de formato (mayúsculas, espacios extra, títulos)
- Nombres compuestos y apellidos dobles
- Incluye prefijos como "Col.", "Mg.", etc.
