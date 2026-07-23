---
description: Estándares de desarrollo, mejores prácticas y convenciones de backend para la aplicación Python/FastAPI, incluyendo Domain-Driven Design, principios SOLID, patrones de arquitectura, diseño de API y prácticas de testing
globs: ["backend/app/**/*.py", "backend/alembic/**/*.py", "backend/pytest.ini", "backend/pyproject.toml", "backend/Dockerfile", "backend/requirements*.txt"]
alwaysApply: true
---

# Estándares y Mejores Prácticas del Proyecto Backend

## Tabla de Contenidos

- [Resumen](#resumen)
- [Stack Tecnológico](#stack-tecnológico)
  - [Tecnologías Core](#tecnologías-core)
  - [Base de Datos y ORM](#base-de-datos-y-orm)
  - [Framework de Testing](#framework-de-testing)
  - [Herramientas de Desarrollo](#herramientas-de-desarrollo)
- [Visión General de Arquitectura](#visión-general-de-arquitectura)
  - [Domain-Driven Design (DDD)](#domain-driven-design-ddd)
  - [Arquitectura en Capas](#arquitectura-en-capas)
  - [Estructura del Proyecto](#estructura-del-proyecto)
- [Principios de Domain-Driven Design](#principios-de-domain-driven-design)
  - [Entidades](#entidades)
  - [Value Objects](#value-objects)
  - [Agregados](#agregados)
  - [Repositorios](#repositorios)
  - [Servicios de Dominio](#servicios-de-dominio)
  - [Recomendaciones Adicionales](#recomendaciones-adicionales)
- [Principios SOLID y DRY](#principios-solid-y-dry)
  - [Single Responsibility Principle (SRP)](#single-responsibility-principle-srp)
  - [Open/Closed Principle (OCP)](#openclosed-principle-ocp)
  - [Liskov Substitution Principle (LSP)](#liskov-substitution-principle-lsp)
  - [Interface Segregation Principle (ISP)](#interface-segregation-principle-isp)
  - [Dependency Inversion Principle (DIP)](#dependency-inversion-principle-dip)
  - [DRY (Don't Repeat Yourself)](#dry-dont-repeat-yourself)
- [Estándares de Código](#estándares-de-código)
  - [Convenciones de Nomenclatura](#convenciones-de-nomenclatura)
  - [Uso de Type Hints](#uso-de-type-hints)
  - [Manejo de Errores](#manejo-de-errores)
  - [Patrones de Validación](#patrones-de-validación)
  - [Estándares de Logging](#estándares-de-logging)
- [Estándares de Diseño de API](#estándares-de-diseño-de-api)
  - [Endpoints REST](#endpoints-rest)
  - [Patrones de Request/Response](#patrones-de-requestresponse)
  - [Formato de Respuesta de Error](#formato-de-respuesta-de-error)
  - [Configuración de CORS](#configuración-de-cors)
- [Patrones de Base de Datos](#patrones-de-base-de-datos)
  - [Modelos SQLModel](#modelos-sqlmodel)
  - [Migraciones](#migraciones)
  - [Patrón Repository](#patrón-repository)
- [Estándares de Testing](#estándares-de-testing)
  - [Unit Testing](#unit-testing)
  - [Integration Testing](#integration-testing)
  - [Requisitos de Cobertura](#requisitos-de-cobertura)
  - [Estándares de Mocking](#estándares-de-mocking)
- [Mejores Prácticas de Performance](#mejores-prácticas-de-performance)
  - [Optimización de Queries](#optimización-de-queries)
  - [Patrones Async/Await](#patrones-asyncawait)
  - [Performance en Manejo de Errores](#performance-en-manejo-de-errores)
- [Mejores Prácticas de Seguridad](#mejores-prácticas-de-seguridad)
  - [Validación de Entradas](#validación-de-entradas)
  - [Variables de Entorno](#variables-de-entorno)
  - [Inyección de Dependencias](#inyección-de-dependencias)
- [Flujo de Trabajo de Desarrollo](#flujo-de-trabajo-de-desarrollo)
  - [Flujo de Git](#flujo-de-git)
  - [Scripts de Desarrollo](#scripts-de-desarrollo)
  - [Calidad de Código](#calidad-de-código)
- [Despliegue con Docker](#despliegue-con-docker)
  - [Imagen Docker](#imagen-docker)
  - [Azure DevOps / Deployment Groups](#azure-devops--deployment-groups)

---

## Resumen

Este documento describe las mejores prácticas, convenciones y estándares usados en la aplicación backend. El backend sigue principios de Domain-Driven Design (DDD) e implementa una arquitectura en capas para garantizar consistencia de código, mantenibilidad y escalabilidad.

## Stack Tecnológico

### Tecnologías Core
- **Python 3.11+**: Entorno de ejecución
- **FastAPI**: Framework web asíncrono
- **Pydantic**: Validación de datos y esquemas (v2)
- **Uvicorn / Gunicorn+Uvicorn workers**: Servidor ASGI

### Base de Datos y ORM
- **PostgreSQL**: Base de datos relacional (contenedor Docker)
- **SQLModel (async)**: ORM type-safe con soporte asyncio, combina SQLAlchemy y Pydantic en un único modelo
- **Alembic**: Herramienta de migraciones de base de datos

### Framework de Testing
- **pytest** + **pytest-asyncio**: Framework de testing con soporte para código async
- **pytest-cov**: Reportes de cobertura
- **Umbral de cobertura**: 90% en branches, funciones, líneas y statements
- **Ubicación de tests**: carpeta `tests/` reflejando la estructura de `app/`, archivos `test_*.py`

### Herramientas de Desarrollo
- **ruff**: Linting (reemplaza flake8 + isort)
- **black**: Formateo de código
- **mypy**: Chequeo estático de tipos (`strict = true`)
- **pre-commit**: Hooks de git para correr lint/format/type-check antes de cada commit

## Visión General de Arquitectura

### Domain-Driven Design (DDD)

Domain-Driven Design es una metodología que se enfoca en modelar el software según la lógica de negocio y el conocimiento del dominio. Al centrar el desarrollo en un entendimiento profundo del dominio, DDD facilita la creación de sistemas complejos.

**Beneficios:**
- **Mejor comunicación**: Promueve un lenguaje común entre desarrolladores y expertos de dominio, reduciendo errores de interpretación.
- **Modelos de dominio claros**: Ayuda a construir modelos que reflejan con precisión las reglas y procesos de negocio.
- **Alta mantenibilidad**: Al dividir el sistema en subdominios, facilita el mantenimiento y la evolución del software.

### Arquitectura en Capas

El backend sigue una arquitectura DDD en capas:

**Capa de Presentación** (`app/presentation/`)
- Routers de FastAPI manejan requests/responses HTTP
- Los routers definen los endpoints de la API
- Los routers usan servicios de la capa de Application

**Capa de Application** (`app/application/`)
- Los servicios contienen la lógica de negocio y orquestación
- `validators.py` maneja la validación de entradas (esquemas Pydantic)
- Los servicios usan repositorios de la capa de Domain

**Capa de Domain** (`app/domain/`)
- Los modelos definen las entidades de negocio core (Candidate, Position, Application, Interview, etc.)
- Las interfaces de repositorio definen los contratos de acceso a datos (usando `abc.ABC`)
- Lógica de negocio pura, sin dependencias externas (sin SQLModel ni Pydantic acá)

**Capa de Infrastructure** (`app/infrastructure/`)
- SQLModel maneja las operaciones de base de datos
- Las implementaciones de repositorio (vía SQLModel) satisfacen las interfaces de domain

### Estructura del Proyecto

```
backend/
├── app/
│   ├── domain/
│   │   ├── models/          # Entidades de dominio (dataclasses o clases planas)
│   │   └── repositories/    # Interfaces de repositorio (ABC)
│   ├── application/
│   │   ├── services/        # Servicios de lógica de negocio
│   │   └── validators.py    # Esquemas Pydantic de validación
│   ├── presentation/
│   │   └── routers/         # Routers de FastAPI (equivalente a controllers)
│   ├── infrastructure/
│   │   ├── logger.py        # Utilidades de logging
│   │   └── database.py      # Setup de engine/session de SQLModel
│   ├── core/
│   │   ├── config.py        # Settings (pydantic-settings)
│   │   └── exceptions.py    # Excepciones custom del dominio
│   └── main.py               # Entry point de la aplicación FastAPI
├── alembic/
│   ├── env.py
│   └── versions/             # Migraciones de base de datos
├── tests/
│   ├── unit/
│   ├── integration/
│   └── factories/             # Factories de datos de prueba
├── pytest.ini                # Configuración de pytest
├── pyproject.toml             # Config de black/ruff/mypy y dependencias
├── Dockerfile
└── requirements.txt / poetry.lock
```

## Principios de Domain-Driven Design

### Entidades

Las entidades son objetos con una identidad distintiva que persiste en el tiempo.

**Antes:**
```python
# Antes, los datos del candidato se manejaban como un dict plano sin métodos
candidate = {
    "id": 1,
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@example.com",
}
```

**Después:**
```python
from dataclasses import dataclass, field

@dataclass
class Candidate:
    first_name: str
    last_name: str
    email: str
    id: int | None = None

    # Métodos que encapsulan lógica de negocio pueden agregarse acá
```

**Explicación**: `Candidate` es una entidad porque tiene un identificador único (`id`) que la distingue de otros candidatos, incluso si el resto de propiedades son idénticas.

**Buena práctica**: Las entidades deben encapsular la lógica de negocio relacionada a su concepto de dominio y mantener la consistencia de su estado interno.

### Value Objects

Los Value Objects describen aspectos del dominio sin identidad conceptual. Se definen por sus atributos, no por un identificador.

**Antes:**
```python
# Manejo de la información de educación como un dict plano
education = {
    "institution": "University",
    "degree": "Bachelor",
    "start_date": "2010-01-01",
    "end_date": "2014-01-01",
}
```

**Después:**
```python
from dataclasses import dataclass
from datetime import date

@dataclass(frozen=True)
class Education:
    institution: str
    title: str
    start_date: date
    end_date: date | None = None
```

**Explicación**: `Education` puede considerarse un Value Object en algunos contextos, ya que describe la educación de un candidato sin necesitar un identificador único. Usar `frozen=True` refuerza la inmutabilidad propia de un Value Object.

**Recomendación**: Clases como `Education` y `WorkExperience` a veces terminan con identificadores únicos propios, lo que las convierte en entidades. En muchos casos podrían tratarse como Value Objects dentro del agregado `Candidate`. Considerar quitar identificadores únicos de clases que deberían ser Value Objects.

### Agregados

Los agregados son clusters de objetos que deben tratarse como una unidad. Tienen una entidad raíz que impone invariantes y límites de consistencia.

**Antes:**
```python
# Datos de candidato y educación manejados por separado
candidate = {"id": 1, "name": "John Doe"}
educations = [{"candidate_id": 1, "institution": "University"}]
```

**Después:**
```python
from dataclasses import dataclass, field

@dataclass
class Candidate:
    first_name: str
    last_name: str
    email: str
    id: int | None = None
    educations: list[Education] = field(default_factory=list)
```

**Explicación**: `Candidate` actúa como raíz del agregado que contiene `Education`, `WorkExperience`, `Resume` y `Application`. `Candidate` es la raíz del agregado, ya que las demás entidades solo tienen sentido en relación con un candidato.

**Recomendación**: Los agregados deben diseñarse cuidadosamente para asegurar que todas las operaciones dentro del límite del agregado mantengan consistencia. Las operaciones que afecten `Education` y `WorkExperience` deben pasar por la raíz del agregado, `Candidate`.

### Repositorios

Los repositorios exponen interfaces para acceder a agregados y entidades, encapsulando la lógica de acceso a datos.

**Antes:**
```python
# Acceso directo a la base de datos sin abstracción
def get_candidate_by_id(id: int):
    return database.query("SELECT * FROM candidates WHERE id = %s", [id])
```

**Después:**
```python
from abc import ABC, abstractmethod

class ICandidateRepository(ABC):
    @abstractmethod
    async def find_by_id(self, candidate_id: int) -> Candidate | None: ...

    @abstractmethod
    async def save(self, candidate: Candidate) -> Candidate: ...

    @abstractmethod
    async def find_all(self) -> list[Candidate]: ...


class CandidateRepository(ICandidateRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def find_by_id(self, candidate_id: int) -> Candidate | None:
        result = await self._session.get(CandidateModel, candidate_id)
        return Candidate(**result.__dict__) if result else None

    async def save(self, candidate: Candidate) -> Candidate:
        # Implementación con SQLModel
        ...
```

**Explicación**: `CandidateRepository` provee una interfaz clara para acceder a los datos de candidatos, encapsulando la lógica de acceso a la base de datos.

**Recomendación**:
- Desarrollar interfaces de repositorio completas para cada entidad/agregado, asegurando que toda interacción con la base de datos pase por el repositorio
- Implementar métodos que manejen colecciones de entidades (listas de Candidates) que puedan filtrarse o modificarse en bloque
- Usar inyección de dependencias (vía `Depends` de FastAPI) para inyectar la `AsyncSession` en los repositorios

### Servicios de Dominio

Los Domain Services contienen lógica de negocio que no pertenece naturalmente a una entidad o value object.

**Antes:**
```python
# Funciones sueltas para manejar lógica de negocio
def calculate_age(candidate: dict) -> int:
    today = date.today()
    birth_date = candidate["birth_date"]
    age = today.year - birth_date.year
    if (today.month, today.day) < (birth_date.month, birth_date.day):
        age -= 1
    return age
```

**Después:**
```python
class CandidateService:
    @staticmethod
    def calculate_age(candidate: Candidate) -> int:
        today = date.today()
        age = today.year - candidate.birth_date.year
        if (today.month, today.day) < (candidate.birth_date.month, candidate.birth_date.day):
            age -= 1
        return age
```

**Explicación**: `CandidateService` encapsula la lógica de negocio relacionada con candidatos, como el cálculo de edad, dando un punto centralizado y coherente para estas operaciones.

### Recomendaciones Adicionales

**Uso de Factories**

Las factories son útiles en DDD para encapsular la lógica de creación de objetos complejos, asegurando que todo objeto creado cumpla con las reglas de dominio desde el momento de su creación.

**Recomendación**: Implementar factories (funciones o `classmethod`s) para la creación de entidades y agregados complejos que requieran configuración inicial específica.

**Mejora en el Modelado de Relaciones**

Las relaciones entre entidades y agregados deben ser claras y consistentes con las reglas de negocio.

**Recomendación**: Revisar y eventualmente rediseñar las relaciones entre entidades para asegurar que reflejen correctamente las necesidades y reglas del dominio.

**Integración de Domain Events**

Los domain events son una parte importante de DDD y pueden usarse para manejar efectos secundarios de operaciones de dominio de forma desacoplada.

**Recomendación**: Implementar un sistema de domain events (por ejemplo, con un event bus simple o una librería como `blinker`) que permita a entidades y agregados publicar eventos que otros componentes puedan manejar sin acoplarse directamente.

## Principios SOLID y DRY

### Principios SOLID

Los principios SOLID son cinco principios de diseño orientado a objetos que ayudan a crear sistemas más entendibles, flexibles y mantenibles.

#### Single Responsibility Principle (SRP)

Cada clase debe tener una única responsabilidad o razón para cambiar.

**Antes:**
```python
# Una función que maneja múltiples responsabilidades: validación y persistencia
def process_candidate(candidate: dict):
    if "@" not in candidate["email"]:
        print("Invalid email")
        return
    database.save(candidate)
    print("Candidate saved")
```

**Después:**
```python
@dataclass
class Candidate:
    email: str

    def validate_email(self) -> None:
        if "@" not in self.email:
            raise ValueError("Invalid email")


class CandidateRepository:
    async def save(self, candidate: Candidate) -> Candidate:
        candidate.validate_email()
        # persistencia con SQLModel
        ...
```

**Explicación**: La clase `Candidate` ahora tiene un método separado para validación, mientras que el repositorio maneja la persistencia, cumpliendo con SRP.

**Observación**: Si `app/domain/models/candidate.py` termina manejando tanto lógica de negocio como acceso a datos, viola SRP.

**Recomendación**: Separar la lógica de acceso a datos en la capa de repositorio para apegarse más a SRP.

#### Open/Closed Principle (OCP)

Las entidades de software deben estar abiertas para extensión pero cerradas para modificación.

**Antes:**
```python
# Modificación directa de la clase para agregar funcionalidad
class Candidate:
    def save_to_database(self):
        ...
    # Para agregar nueva funcionalidad, modificamos la clase directamente
    def send_email(self):
        ...
```

**Después:**
```python
class Candidate:
    def save_to_database(self):
        ...

# Extender funcionalidad sin modificar la clase existente
class CandidateWithEmail(Candidate):
    def send_email(self):
        ...
```

**Explicación**: La funcionalidad de envío de email se extiende en una subclase, manteniendo la clase original cerrada a modificaciones pero abierta a extensión.

**Observación**: Si `add_candidate` en `app/application/services/candidate_service.py` instancia directamente `Candidate`, `Education`, `WorkExperience` y `Resume`, se dificulta la extensión.

**Recomendación**: Usar factory functions para crear instancias, facilitando la extensión sin modificar código existente.

#### Liskov Substitution Principle (LSP)

Los objetos de una clase derivada deben poder reemplazar a los de la clase base sin alterar el funcionamiento del programa.

**Antes:**
```python
class TemporaryCandidate(Candidate):
    def save_to_database(self):
        raise NotImplementedError("Temporary candidates can't be saved")
```

**Después:**
```python
class TemporaryCandidate(Candidate):
    def save_to_database(self):
        # Implementación apropiada que permite el manejo temporal
        print("Handled temporarily")
        # Alternativa: guardar en almacenamiento temporal
```

**Explicación**: `TemporaryCandidate` ahora provee una implementación apropiada que respeta el contrato de la clase base, permitiendo sustitución sin errores.

**Observación**: Preferir composición sobre herencia en Python (mixins solo cuando aporten claridad real) para evitar violaciones de LSP.

**Recomendación**: Continuar usando composición para evitar violar LSP, y asegurar que cualquier jerarquía de herencia futura permita sustituir clases derivadas por su clase base sin alterar el comportamiento del programa.

#### Interface Segregation Principle (ISP)

Muchas interfaces específicas son mejores que una sola interfaz general.

**Antes:**
```python
from abc import ABC, abstractmethod

class CandidateOperations(ABC):
    @abstractmethod
    def save(self): ...
    @abstractmethod
    def validate(self): ...
    @abstractmethod
    def send_email(self): ...
    @abstractmethod
    def generate_report(self): ...
```

**Después:**
```python
class SaveOperation(ABC):
    @abstractmethod
    def save(self): ...

class EmailOperations(ABC):
    @abstractmethod
    def send_email(self): ...

class ReportOperations(ABC):
    @abstractmethod
    def generate_report(self): ...

class Candidate(SaveOperation, EmailOperations):
    def save(self):
        ...
    def send_email(self):
        ...
```

**Explicación**: Las interfaces (en Python, clases `ABC` o `Protocol`) se segregan en operaciones más pequeñas, permitiendo que las clases implementen solo lo que necesitan.

**Recomendación**: Usar `typing.Protocol` como alternativa liviana a `ABC` cuando no se necesite herencia explícita, y definir interfaces más granulares para las clases de servicio.

#### Dependency Inversion Principle (DIP)

Los módulos de alto nivel no deben depender de módulos de bajo nivel; ambos deben depender de abstracciones.

**Antes:**
```python
class Candidate:
    def __init__(self):
        self._session = create_session()  # dependencia concreta directa

    def save(self):
        self._session.add(self)
        self._session.commit()
```

**Después:**
```python
class DatabasePort(Protocol):
    async def save(self, candidate: "Candidate") -> "Candidate": ...

class Candidate:
    def __init__(self, database: DatabasePort):
        self._database = database

    async def save(self) -> "Candidate":
        return await self._database.save(self)
```

**Explicación**: `Candidate` ahora depende de una abstracción (`DatabasePort`), no de una implementación concreta, facilitando la flexibilidad y el testing del código.

**Recomendación**: Usar inyección de dependencias (vía `Depends` de FastAPI en la capa de presentación, y constructores explícitos en las capas internas) para invertir la dependencia, apoyándose en abstracciones en lugar de implementaciones concretas.

### DRY (Don't Repeat Yourself)

El principio DRY se enfoca en reducir la duplicación de código. Cada pieza de conocimiento debe tener una representación única, inequívoca y autoritativa dentro del sistema.

**Antes:**
```python
def save_candidate(candidate: dict):
    if "@" not in candidate["email"]:
        raise ValueError("Invalid email")
    # lógica de guardado

def update_candidate(candidate: dict):
    if "@" not in candidate["email"]:
        raise ValueError("Invalid email")
    # lógica de actualización
```

**Después:**
```python
@dataclass
class Candidate:
    email: str

    def validate_email(self) -> None:
        if "@" not in self.email:
            raise ValueError("Invalid email")

    async def save(self) -> "Candidate":
        self.validate_email()
        # lógica de guardado

    async def update(self) -> "Candidate":
        self.validate_email()
        # lógica de actualización
```

**Explicación**: La validación de email se centraliza en un único método `validate_email`, eliminando la duplicación de código en las funciones de guardado y actualización.

**Recomendación**: Abstraer la lógica común de operaciones de base de datos en una función o clase reutilizable (por ejemplo, un `BaseRepository` genérico).

## Estándares de Código

### Convenciones de Nomenclatura

- **Variables y funciones**: `snake_case` (ej. `candidate_id`, `find_candidate_by_id`)
- **Clases**: `PascalCase` (ej. `Candidate`, `CandidateRepository`)
- **Constantes**: `UPPER_SNAKE_CASE` (ej. `MAX_CANDIDATES_PER_PAGE`)
- **Tipos/Protocols**: `PascalCase` (ej. `CandidateData`, `ICandidateRepository`)
- **Nombres de archivo**: `snake_case` (ej. `candidate_service.py`, `candidate_router.py`)

**Ejemplos:**

```python
# Bien: todo en inglés
class CandidateRepository:
    async def find_by_id(self, candidate_id: int) -> Candidate | None:
        # Buscar candidato por ID en la base de datos
        result = await self._session.get(CandidateModel, candidate_id)
        return Candidate(**result.__dict__) if result else None

# Evitar: nombres o comentarios en español dentro del código
class RepositorioCandidato:
    async def buscar_por_id(self, id_candidato: int) -> Candidato | None:
        # Buscar candidato por ID en la base de datos
        ...
```

**Mensajes de error y logs:**

```python
# Bien: mensajes de error en inglés
raise NotFoundError("Candidate not found with the provided ID")
logger.error("Failed to create candidate", extra={"error": str(error)})

# Evitar: mensajes en español dentro del código
raise NotFoundError("Candidato no encontrado con el ID proporcionado")
```

### Uso de Type Hints

- **Type hints obligatorios**: Usar tipos explícitos en parámetros y valores de retorno de todas las funciones
- **mypy strict**: Habilitar `strict = true` en `pyproject.toml`
- **Pydantic para fronteras**: Usar modelos Pydantic para request/response de la API; dataclasses o clases planas para el dominio interno
- **Evitar `Any`**: Preferir `object`, genéricos (`TypeVar`) o tipos específicos en vez de `Any` cuando sea posible

```python
# Bien: tipos explícitos
async def find_candidate_by_id(candidate_id: int) -> Candidate | None:
    ...

# Evitar: uso de Any
def process_data(data: Any) -> Any:
    ...
```

### Manejo de Errores

- **Clases de error custom**: Crear excepciones específicas del dominio heredando de `Exception`
- **Exception handlers de FastAPI**: Usar `@app.exception_handler(...)` para respuestas de error consistentes
- **Mensajes descriptivos**: Proveer mensajes de error claros para debugging

```python
class NotFoundError(Exception):
    def __init__(self, message: str):
        super().__init__(message)


# En app/main.py
@app.exception_handler(NotFoundError)
async def not_found_handler(request: Request, exc: NotFoundError):
    return JSONResponse(status_code=404, content={"success": False, "error": {"message": str(exc)}})


# En el router
@router.get("/candidates/{candidate_id}")
async def get_candidate(candidate_id: int, service: CandidateService = Depends(get_candidate_service)):
    candidate = await service.find_by_id(candidate_id)
    if not candidate:
        raise NotFoundError("Candidate not found")
    return candidate
```

### Patrones de Validación

- **Validación de entrada**: Validar todas las entradas en la capa de application, usando esquemas Pydantic
- **Centralizar validadores**: Centralizar lógica de validación en `app/application/validators.py`
- **Validar antes de procesar**: Siempre validar antes de ejecutar lógica de negocio

```python
from app.application.validators import CandidateCreateSchema

@router.post("/candidates", status_code=201)
async def add_candidate(
    payload: CandidateCreateSchema,
    service: CandidateService = Depends(get_candidate_service),
):
    candidate = await service.create(payload)
    return candidate
```

### Estándares de Logging

- **Logger centralizado**: Usar el logger centralizado de `app/infrastructure/logger.py` (basado en `logging` estándar o `structlog`)
- **Niveles de log**: Usar niveles apropiados (info, error, warning, debug)
- **Logging estructurado**: Incluir contexto relevante en los mensajes de log

```python
from app.infrastructure.logger import get_logger

logger = get_logger(__name__)

logger.info("Candidate created", extra={"candidate_id": candidate.id})
logger.error("Failed to create candidate", extra={"error": str(error)})
```

## Estándares de Diseño de API

### Endpoints REST

- **Nomenclatura RESTful**: Usar convenciones RESTful para nombrar endpoints
- **Métodos HTTP**: Usar el método HTTP apropiado (GET, POST, PUT, DELETE, PATCH)
- **URLs basadas en recursos**: Las URLs deben representar recursos, no acciones

```python
GET    /candidates          # Listar candidatos
GET    /candidates/{id}     # Obtener candidato por ID
POST   /candidates          # Crear nuevo candidato
PUT    /candidates/{id}     # Actualizar candidato
DELETE /candidates/{id}     # Eliminar candidato
```

### Patrones de Request/Response

- **Formato JSON**: Usar JSON para los cuerpos de request y response (nativo en FastAPI vía Pydantic)
- **Estructura consistente**: Mantener una estructura de respuesta consistente en todos los endpoints
- **Códigos de estado**: Usar los códigos HTTP apropiados

```python
# Respuesta exitosa
{
    "success": True,
    "data": { ... },
    "message": "Operation completed successfully"
}

# Respuesta de error
{
    "success": False,
    "error": {
        "message": "Error description",
        "code": "ERROR_CODE"
    }
}
```

### Formato de Respuesta de Error

- **Formato consistente**: Todos los errores deben seguir la misma estructura de respuesta
- **Códigos de error**: Usar códigos significativos para distintos tipos de error
- **Códigos HTTP**: Mapear errores a los códigos de estado HTTP apropiados

```python
# 400 Bad Request
{
    "success": False,
    "error": {
        "message": "Validation failed",
        "code": "VALIDATION_ERROR",
        "details": [ ... ]
    }
}

# 404 Not Found
{
    "success": False,
    "error": {
        "message": "Resource not found",
        "code": "NOT_FOUND"
    }
}
```

### Configuración de CORS

- **Habilitar CORS**: Configurar CORS para permitir el origen del frontend
- **Configuración segura**: Solo permitir orígenes específicos en producción
- **Credentials**: Configurar el manejo de credenciales apropiadamente

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Patrones de Base de Datos

### Modelos SQLModel

- **Fuente única de verdad**: Los modelos SQLModel con `table=True` (`app/infrastructure/models/`) son la fuente única de verdad de la estructura de base de datos
- **Relaciones**: Definir relaciones usando `Relationship()` de SQLModel
- **Convenciones de nombres**: `snake_case` para columnas y tablas, `PascalCase` para clases modelo

### Migraciones

- **Control de versiones**: Todo cambio de base de datos debe versionarse mediante migraciones de Alembic
- **Nombres descriptivos**: Usar nombres descriptivos para las migraciones
- **Revisar migraciones**: Revisar el archivo de migración generado antes de aplicarlo (Alembic no siempre detecta todo correctamente)

```bash
# Crear migración
alembic revision --autogenerate -m "descriptive_migration_name"

# Aplicar migraciones
alembic upgrade head

# Revertir última migración
alembic downgrade -1
```

### Patrón Repository

- **Interfaces de repositorio**: Definir interfaces de repositorio (`ABC` o `Protocol`) en la capa de dominio
- **Implementación SQLModel**: Implementar los repositorios usando SQLModel en la capa de infrastructure
- **Inyección de dependencias**: Inyectar la `AsyncSession` en los repositorios vía `Depends`

```python
# Interfaz en la capa de dominio
class ICandidateRepository(ABC):
    @abstractmethod
    async def find_by_id(self, candidate_id: int) -> Candidate | None: ...
    @abstractmethod
    async def save(self, candidate: Candidate) -> Candidate: ...

# Implementación en la capa de infrastructure
class CandidateRepository(ICandidateRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def find_by_id(self, candidate_id: int) -> Candidate | None:
        result = await self._session.get(CandidateModel, candidate_id)
        return Candidate(**result.__dict__) if result else None
```

## Estándares de Testing

El proyecto tiene requisitos estrictos de calidad y mantenibilidad de código. Estos son los estándares y mejores prácticas de unit testing que deben aplicarse.

### Estructura de Archivos de Test
- Usar nombres descriptivos: `test_[nombre_componente].py`
- Ubicar los tests en `tests/` reflejando la estructura de `app/`
- Usar pytest + pytest-asyncio como framework de testing
- Mantener un umbral de cobertura del 90% en branches, funciones, líneas y statements

### Patrón de Organización de Tests
Plantilla:
```python
class TestCandidateServiceFindById:
    def setup_method(self):
        # equivalente a beforeEach: reset de mocks
        ...

    class TestShouldReturnCandidateWhenFound:
        async def test_returns_candidate_data(self):
            # Arrange
            # Act
            # Assert
            ...
```

Ejemplo real:
```python
import pytest
from unittest.mock import AsyncMock

class TestCandidateServiceFindById:
    def setup_method(self):
        self.repository = AsyncMock()
        self.service = CandidateService(repository=self.repository)

    @pytest.mark.asyncio
    async def test_should_return_candidate_when_found(self):
        # Arrange
        candidate_id = 1
        mock_candidate = Candidate(id=1, first_name="John", last_name="Doe", email="john@example.com")
        self.repository.find_by_id.return_value = mock_candidate

        # Act
        result = await self.service.find_by_id(candidate_id)

        # Assert
        assert result == mock_candidate
        self.repository.find_by_id.assert_called_once_with(candidate_id)
```

### Convención de Nombres de Test Case
- Usar nomenclatura descriptiva orientada a comportamiento: `test_should_[comportamiento_esperado]_when_[condición]`
- Agrupar tests relacionados en clases `Test[NombreComponente][NombreMétodo]`
- Usar `snake_case` para nombres de funciones de test

### Estructura de Test (Patrón AAA)
Seguir siempre el patrón Arrange-Act-Assert:
```python
@pytest.mark.asyncio
async def test_should_update_candidate_stage_successfully_when_valid_data_provided():
    # Arrange - preparar datos de prueba y mocks
    candidate_id = 1
    application_id = 1
    new_interview_step = 2

    # Act - ejecutar la función bajo prueba
    result = await update_candidate_stage(candidate_id, application_id, new_interview_step)

    # Assert - verificar el comportamiento esperado
    assert result == expected_result
```

Patrón de aserciones:
- Usar matchers específicos: `assert_called_with()`, `assert_called_once()`, `assert_awaited_with()`
- Verificar tanto operaciones exitosas como condiciones de error
- Comprobar que los mocks fueron llamados con los parámetros correctos
- Verificar valores de retorno y efectos secundarios

### Estándares de Mocking

- Mockear todas las dependencias externas (modelos, servicios, clientes de base de datos)
- Mockear la capa de repositorio en los tests de servicio
- Mockear la capa de servicio en los tests de router/controller
- Usar `unittest.mock.AsyncMock` para dependencias async, `MagicMock` para síncronas
- Crear instancias mock con estructuras de datos realistas
- Resetear todos los mocks en `setup_method()` (o fixtures de pytest) para asegurar aislamiento entre tests

### Requisitos de Cobertura

- **Cobertura comprehensiva**: Incluir estas categorías de test para cada función:
1. **Happy Path**: Entradas válidas que producen las salidas esperadas
2. **Manejo de Errores**: Entradas inválidas, datos faltantes, errores de base de datos
3. **Edge Cases**: Valores límite, entradas `None`, datos vacíos
4. **Validación**: Validación de entrada, cumplimiento de reglas de negocio
5. **Puntos de Integración**: Llamadas a servicios externos, operaciones de base de datos

- **Umbral**: 90% en branches, funciones, líneas y statements
- **Reportes de cobertura**: Generar con `pytest --cov=app --cov-report=html`
- **Archivos de cobertura**: Reportes en el directorio `coverage/`, agregando la fecha, ej. `YYYYMMDD-backend-coverage.md`

### Testing de Errores
- Probar tanto errores esperados como inesperados
- Verificar que los mensajes de error sean descriptivos y útiles
- Probar la propagación de errores a través de las capas de servicio
- Asegurar los códigos de estado HTTP correctos en los tests de router

### Especificidades del Testing de Routers
- Mockear completamente la capa de servicio
- Probar el manejo de request/response HTTP
- Verificar el parsing y validación de parámetros (vía `TestClient` de FastAPI)
- Probar el formateo de respuestas de error
- Usar `httpx.AsyncClient` o `TestClient` de FastAPI para requests realistas

### Especificidades del Testing de Servicios
- Mockear modelos de dominio y repositorios
- Probar la lógica de negocio de forma aislada
- Verificar la transformación y validación de datos
- Probar el manejo de errores y edge cases
- Mockear dependencias externas (SQLModel, validadores)

### Testing de Base de Datos
- Mockear la sesión de SQLModel y todas las operaciones de base de datos en unit tests
- Probar tanto operaciones de base de datos exitosas como fallidas
- Verificar las queries y parámetros correctos
- Probar manejo de transacciones y escenarios de rollback
- Para integration tests, usar una base de datos de test real (contenedor Docker efímero) en vez de mocks

### Testing Async
- Usar siempre `async/await` para operaciones asíncronas, con `@pytest.mark.asyncio`
- Usar `asyncio.gather()` para probar operaciones concurrentes
- Manejar correctamente las excepciones en corrutinas dentro de los tests
- Probar escenarios de timeout donde aplique

### Manejo de Datos de Test
- Usar factory functions (o librerías como `factory_boy`) para crear datos de prueba
- Mantener los datos de test consistentes y realistas
- Evitar valores hardcodeados repetidos en múltiples lugares
- Usar datos de test significativos que reflejen escenarios reales

### Integration Testing

- **Testing de Routers**: Probar el manejo de request/response HTTP end-to-end
- **Testing de Base de Datos**: Probar implementaciones de repositorio contra una base de datos real de test
- **Flujo End-to-End**: Probar flujos completos de request

### Estándares de Calidad de Código

#### Uso de Type Hints
- Usar tipado estricto en todos los parámetros y valores de retorno de los tests
- Definir interfaces/tipos apropiados para los datos mockeados
- Usar `cast()` con moderación y justificación adecuada
- Aprovechar el sistema de tipos de Python para mayor confiabilidad de los tests

#### Documentación
- Escribir nombres de test claros y descriptivos que expliquen el escenario
- Agregar comentarios para setups de test complejos
- Documentar condiciones especiales o edge cases
- Mantener el código de test tan legible como el código de producción

#### Consideraciones de Performance
- Mantener los tests rápidos y focalizados
- Evitar operaciones async innecesarias en los tests
- Usar estrategias de mocking apropiadas para evitar I/O real
- Agrupar tests relacionados para minimizar overhead de setup/teardown

### Integración con el Flujo de Desarrollo
- Correr los tests antes de cada commit
- Asegurar que todos los tests pasen antes de mergear
- Usar test-driven development cuando aplique
- Actualizar los tests al modificar funcionalidad existente

### Anti-Patrones Comunes a Evitar
- No probar detalles de implementación, probar comportamiento
- No crear setups de test excesivamente complejos
- No ignorar tests que fallan ni saltarse escenarios de error
- No usar conexiones reales de base de datos en unit tests
- No crear tests que dependan de servicios externos
- No escribir tests demasiado acoplados a la implementación

## Mejores Prácticas de Performance

### Optimización de Queries

- **Seleccionar campos específicos**: Solo seleccionar los campos necesarios (`select(Model.field1, Model.field2)`)
- **Usar índices**: Asegurar índices apropiados para campos consultados frecuentemente
- **Evitar queries N+1**: Usar `selectinload()`/`joinedload()` (de `sqlalchemy.orm`, compatibles con SQLModel) para traer datos relacionados eficientemente

```python
from sqlalchemy.orm import selectinload
from sqlmodel import select

# Bien: traer datos relacionados eficientemente
stmt = select(CandidateModel).options(
    selectinload(CandidateModel.educations),
    selectinload(CandidateModel.work_experiences),
).where(CandidateModel.id == candidate_id)
result = await session.execute(stmt)

# Evitar: queries N+1
candidate = await session.get(CandidateModel, candidate_id)
educations = await session.execute(select(EducationModel).where(EducationModel.candidate_id == candidate_id))
```

### Patrones Async/Await

- **Usar siempre async/await**: Usar `async`/`await` en vez de callbacks o código bloqueante
- **Manejo de errores**: Manejar correctamente las excepciones en operaciones async
- **Operaciones en paralelo**: Usar `asyncio.gather()` para operaciones en paralelo cuando aplique

```python
import asyncio

# Bien: operaciones en paralelo
candidates, positions = await asyncio.gather(
    candidate_service.find_all(),
    position_service.find_all(),
)
```

### Performance en Manejo de Errores

- **Early returns**: Retornar temprano para evitar procesamiento innecesario
- **Propagación de errores**: Dejar que los errores se propaguen naturalmente por el stack de llamadas
- **Evitar sobre-envolver**: No envolver errores innecesariamente en capas adicionales de excepciones

## Mejores Prácticas de Seguridad

### Validación de Entradas

- **Validar todas las entradas**: Validar todas las entradas del usuario antes de procesarlas (vía esquemas Pydantic)
- **Sanitizar datos**: Sanitizar datos para prevenir ataques de inyección
- **Chequeo de tipos**: Usar type hints + Pydantic para garantizar type safety en runtime

### Variables de Entorno

- **Nunca commitear secretos**: Nunca commitear archivos `.env` ni secretos al control de versiones
- **Usar variables de entorno**: Usar variables de entorno para la configuración, gestionadas con `pydantic-settings`
- **Validar el entorno**: Validar las variables de entorno requeridas al arrancar la aplicación

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    port: int = 8000

    class Config:
        env_file = ".env"

settings = Settings()  # Pydantic valida y falla rápido si falta una variable requerida
```

### Inyección de Dependencias

- **Inyectar la sesión de base de datos**: Inyectar la `AsyncSession` de SQLModel vía `Depends` de FastAPI
- **Evitar estado global**: Evitar estado global para conexiones de base de datos
- **Testabilidad**: Usar inyección de dependencias para mejorar la testabilidad

```python
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session

@router.get("/candidates/{candidate_id}")
async def get_candidate(
    candidate_id: int,
    session: AsyncSession = Depends(get_db_session),
):
    candidate = await session.get(CandidateModel, candidate_id)
    return candidate
```

## Flujo de Trabajo de Desarrollo

### Flujo de Git

- **Feature branches**: Desarrollar features en ramas separadas con nombres claros y descriptivos, para permitir trabajo en paralelo y evitar conflictos
- **Commits descriptivos**: Escribir mensajes de commit descriptivos en inglés
- **Code review**: Revisión de código antes de mergear
- **Ramas pequeñas**: Mantener las ramas pequeñas y focalizadas

### Scripts de Desarrollo

```bash
uvicorn app.main:app --reload       # Servidor de desarrollo con hot reload
pytest                                # Correr tests
pytest --cov=app --cov-report=html   # Correr tests con cobertura
alembic revision --autogenerate -m "msg"  # Crear migración
alembic upgrade head                  # Aplicar migraciones
ruff check .                          # Linting
black .                               # Formateo
mypy app                              # Chequeo de tipos
```

### Calidad de Código

- **Validación con ruff**: Correr ruff antes de cada commit
- **Compilación de tipos**: Asegurar que mypy pase sin errores
- **Todos los tests pasando**: Asegurar que todos los tests pasen antes de desplegar
- **Code review**: Revisar el código respecto a estos estándares

## Despliegue con Docker

### Imagen Docker

- **Multi-stage build**: Usar build multi-stage para mantener la imagen final liviana (stage de build con dependencias de compilación, stage final solo con runtime)
- **Imagen base**: `python:3.11-slim` como base, evitando imágenes `-alpine` si hay dependencias con bindings nativos que compliquen el build
- **Usuario no root**: Correr el contenedor con un usuario sin privilegios de root
- **Entry point**: `uvicorn app.main:app --host 0.0.0.0 --port 8000` (o `gunicorn` con workers `uvicorn.workers.UvicornWorker` en producción)

```dockerfile
FROM python:3.11-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY app/ ./app/
ENV PATH=/root/.local/bin:$PATH
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Azure DevOps / Deployment Groups

- **Pipeline de CI/CD**: Build de la imagen Docker y push a un registry (Azure Container Registry o similar) desde el pipeline de Azure DevOps
- **Deployment Groups**: Despliegue del contenedor en los servidores Linux on-premise vía Azure DevOps Deployment Groups
- **Gestión de puertos**: Auditar los puertos ocupados en el servidor destino antes de asignar el puerto del contenedor, para evitar colisiones con otros despliegues
- **Variables de entorno**: Inyectar la configuración vía variables de entorno del pipeline (nunca hardcodear secretos en el `Dockerfile` ni en el repo)
- **Health check**: Exponer un endpoint `/health` que el pipeline y el Deployment Group puedan usar para verificar que el contenedor levantó correctamente antes de dar el despliegue por exitoso

Este documento sirve como base para mantener la calidad y consistencia del código en toda la aplicación backend. Todo el equipo debe seguir estas prácticas para asegurar un código base mantenible, escalable y testeable.