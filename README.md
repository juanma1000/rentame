# Rentame

Plataforma de arrendamiento de inmuebles (publicación de propiedades, agencias, identidad, firma de contrato, seguro y pagos). Este README explica, paso a paso y sin asumir experiencia previa, cómo levantar **todo el proyecto en tu computador** usando Docker.

No necesitas instalar Python, Node.js, PostgreSQL ni nada parecido: todo corre dentro de contenedores.

---

## 1. Qué vas a instalar antes de empezar

Solo necesitas dos programas:

1. **Docker Desktop** — es el único requisito real.
   - Windows / Mac: descárgalo de https://www.docker.com/products/docker-desktop/ e instálalo como cualquier programa.
   - Linux: instala `docker` y el plugin `docker compose` con el gestor de paquetes de tu distro, o sigue https://docs.docker.com/engine/install/.
   - Una vez instalado, ábrelo y espera a que diga que está "running" (en Windows/Mac aparece una ballena en la barra de tareas).
2. **Git** — para descargar el código.
   - Windows: https://git-scm.com/download/win
   - Mac: viene instalado, o `brew install git`
   - Linux: `sudo apt install git` (Ubuntu/Debian) o el equivalente de tu distro.

Para verificar que quedaron bien instalados, abre una terminal (en Windows, "Git Bash" o "PowerShell") y corre:

```bash
docker --version
docker compose version
git --version
```

Si los tres comandos responden con un número de versión (y no un error), estás listo.

---

## 2. Descargar el proyecto

```bash
git clone <URL-del-repositorio>
cd Rentame
```

(Si ya tienes la carpeta del proyecto porque te la compartieron, simplemente abre una terminal dentro de ella y sáltate este paso.)

---

## 3. Configurar las variables de entorno

El proyecto necesita un archivo `.env` en la raíz con contraseñas y configuración para desarrollo local. Ya viene un ejemplo listo para copiar:

```bash
cp .env.example .env
```

No necesitas cambiar nada dentro de `.env` para correr el proyecto en tu máquina — los valores por defecto ya funcionan.

---

## 4. Levantar todo el proyecto

Desde la raíz del repo (donde está el archivo `docker-compose.yml`), corre:

```bash
docker compose up -d --build
```

Qué hace este comando:
- Descarga las imágenes base (PostgreSQL, MinIO) la primera vez.
- Construye las imágenes del backend y de los tres frontends (esto puede tardar varios minutos la primera vez; las siguientes veces es mucho más rápido).
- Levanta todo en segundo plano (`-d` = "detached", no bloquea tu terminal).

Cuando termine, revisa que todo esté corriendo:

```bash
docker compose ps
```

Deberías ver 6 servicios en estado `Up` (o `healthy`):

| Servicio | Qué es |
|---|---|
| `postgres` | Base de datos |
| `minio` | Almacenamiento de fotos de inmuebles |
| `minio-init` | Tarea que prepara MinIO (termina y queda como "Exited (0)", eso es normal) |
| `backend` | API (FastAPI) |
| `shell` | Frontend principal (la app que abres en el navegador) |
| `inmuebles-app` | Frontend de inmuebles (se carga dentro del shell) |
| `arrendamiento-app` | Frontend del flujo de arrendamiento (se carga dentro del shell) |

> `minio-init` aparece como detenido apenas termina su trabajo — **no es un error**.

---

## 5. Poblar la base de datos con datos de prueba (opcional pero recomendado)

Recién levantado, el proyecto no tiene ningún dato: no hay usuarios ni inmuebles. Para no empezar de cero, hay un script que crea usuarios y propiedades de ejemplo (con fotos reales):

```bash
docker compose exec backend sh -c "cd /app && PYTHONPATH=/app python -m scripts.seed_data"
```

Al terminar, imprime en la terminal una lista de usuarios de prueba, por ejemplo:

```
- ana.propietaria@seed.rentame.test [propietario]
- carlos.propietario@seed.rentame.test [propietario]
- laura.agente@seed.rentame.test [agente]
- pedro.agente@seed.rentame.test [agente]
- sofia.inquilino@seed.rentame.test [inquilino]
- diego.inquilino@seed.rentame.test [inquilino]
```

La contraseña de **todos** esos usuarios es: **`Seed1234!`**

Puedes volver a correr este comando cuantas veces quieras: cada vez borra los datos de prueba anteriores y crea unos nuevos, sin afectar otros datos que hayas creado manualmente.

---

## 6. Abrir la aplicación

Con todo corriendo, abre tu navegador en:

- **App principal (login, navegación completa):** http://localhost:3000
- API del backend (documentación interactiva Swagger): http://localhost:8000/docs
- Consola de administración de MinIO (fotos subidas): http://localhost:9001
  - Usuario: `rentame` — Contraseña: `rentame12345`

Para entrar a la app, ve a http://localhost:3000, inicia sesión con uno de los correos del paso 5 (por ejemplo `ana.propietaria@seed.rentame.test`) y la contraseña `Seed1234!`.

> Los puertos `3001` y `3002` (`inmuebles-app` y `arrendamiento-app`) también responden por separado, pero normalmente no los necesitas abrir directamente: el shell (`3000`) los carga automáticamente cuando navegas a esas secciones.

---

## 7. Comandos del día a día

Apagar todo (sin borrar datos):
```bash
docker compose down
```

Volver a encenderlo más tarde:
```bash
docker compose up -d
```

Ver los logs en vivo (por ejemplo, para depurar el backend):
```bash
docker compose logs -f backend
```

Ver logs de todos los servicios:
```bash
docker compose logs -f
```

Reconstruir después de bajar cambios nuevos del repo (por si cambiaron dependencias):
```bash
docker compose up -d --build
```

Borrar **todo**, incluyendo la base de datos y las fotos subidas (empezar 100% de cero):
```bash
docker compose down -v
```

---

## 8. Solución de problemas comunes

**"Cannot connect to the Docker daemon" / error de conexión con Docker**
Docker Desktop no está corriendo. Ábrelo y espera a que el ícono indique que está listo, luego reintenta.

**Un puerto ya está en uso (`port is already allocated`)**
Algún otro programa en tu computador ya usa ese puerto (por ejemplo otro Postgres local en el 5432). Cierra ese programa, o cambia el puerto en el archivo `.env` (por ejemplo `POSTGRES_PORT=5433`) y vuelve a correr `docker compose up -d`.

**La página en localhost:3000 no carga o da error**
Revisa que los 6 servicios estén `Up`/`healthy` con `docker compose ps`. Si `backend` no está `Up`, revisa sus logs con `docker compose logs backend`.

**Quiero empezar de cero porque algo quedó en mal estado**
```bash
docker compose down -v
docker compose up -d --build
docker compose exec backend sh -c "cd /app && PYTHONPATH=/app python -m scripts.seed_data"
```

---

## 9. Para ir más allá

Este README cubre solo cómo **correr** el proyecto. Si vas a desarrollar sobre el código (backend en Python/FastAPI, frontend en React con Module Federation), revisa:

- `backend/` — API en FastAPI, arquitectura hexagonal por dominio.
- `frontend/README.md` — detalles del monorepo de frontend (workspaces, cómo correr un remote individual fuera de Docker, tests).
- `docs/architecture/architecture.md` — diagramas de arquitectura y de base de datos.
