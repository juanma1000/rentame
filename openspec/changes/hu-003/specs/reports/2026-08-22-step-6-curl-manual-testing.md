# Reporte Paso 6 - Testing Manual de Endpoints con curl

- Fecha: 2026-08-22
- Cambio: hu-003
- Agente: Claude Code

Ejecutado con `docker compose exec backend curl ...` contra el backend real, usando los inmuebles ya sembrados por `backend/scripts/seed_data.py` (3 `disponible`, 1 `oculto`).

## 1. `GET /inmuebles/publicos`
```
curl "http://localhost:8000/inmuebles/publicos"
```
→ `200`, array con los 3 inmuebles `disponible` (Calle 10 # 5-30, Carrera 45 # 12-08, Avenida 80 # 34-21), cada uno con `id`, `foto_principal`, `direccion`, `barrio`, `ciudad`, `valor_mensual`, `habitaciones`, `banos`. El inmueble `oculto` (Calle 33 # 70-15) **no aparece** en la respuesta.

## 2. `GET /inmuebles/publicos/{id}` — disponible
```
curl "http://localhost:8000/inmuebles/publicos/cdd99627-7808-48d8-a77b-57b24d2e1e10"
```
→ `200`, incluye `tipo`, `area_m2`, `descripcion`, y `fotos` con las 2 fotos ordenadas (`orden` 1 y 2, la primera con `es_principal: true`).

## 3. `GET /inmuebles/publicos/{id}` — oculto
```
curl "http://localhost:8000/inmuebles/publicos/30d3da9a-2dcc-4cf8-9bef-21533d05eb75"
```
→ `404`, `{"detail":"Inmueble no encontrado"}` — mismo mensaje que un id inexistente, no revela que el inmueble existe pero está oculto.

## 4. `GET /inmuebles/publicos/{id}` — id inexistente
```
curl "http://localhost:8000/inmuebles/publicos/00000000-0000-0000-0000-000000000000"
```
→ `404`, mismo body que el caso anterior.

## Restauración de la base de datos
No se creó ningún dato de prueba nuevo — todas las pruebas fueron lecturas (`GET`) contra los datos ya sembrados. No requiere limpieza.

## Resultado
- Estado del Paso 6: PASS
- Issues bloqueantes: ninguno
