## 0. Setup: Crear Feature Branch (OBLIGATORIO - PRIMER PASO)

- [x] 0.1 Crear y cambiar al branch `feature/frontend-flujo-arrendamiento` desde `main`
- [x] 0.2 Verificar la creación del branch y el estado del branch actual

## 1. Backend: `GET /identidad/estado`

- [x] 1.1 qa-expert (Red): tests unitarios de `consultar_estado_identidad` (application) — sin `ValidacionIdentidad` devuelve `no_iniciado`; con una devuelve su estado real, sin llamar al proveedor
- [x] 1.2 backend-expert (Green): `backend/identidad/application/consultar_estado_identidad.py`
- [x] 1.3 qa-expert (Red): test de integración `GET /identidad/estado` — requiere inquilino autenticado, forma de respuesta esperada en cada estado
- [x] 1.4 backend-expert (Green): endpoint en `backend/identidad/infrastructure/api/router.py` + `schemas.py`

## 2. Backend: `GET /seguro-arrendamiento/estado`

- [x] 2.1 qa-expert (Red): tests unitarios de `consultar_estado_seguro` (application) — sin `PolizaArrendamiento` devuelve `no_iniciado`; con una aprobada devuelve estado + `prima_mensual`
- [x] 2.2 backend-expert (Green): `backend/seguro_arrendamiento/application/consultar_estado_seguro.py`
- [x] 2.3 qa-expert (Red): test de integración `GET /seguro-arrendamiento/estado`
- [x] 2.4 backend-expert (Green): endpoint en `backend/seguro_arrendamiento/infrastructure/api/router.py` + `schemas.py`

## 3. Backend: `GET /firma-contrato/estado`

- [x] 3.1 qa-expert (Red): tests unitarios de `consultar_estado_firma` (application) — sin `Contrato` devuelve `no_iniciado`; con uno `firmado` devuelve estado + `arrendamiento_activo_id`
- [x] 3.2 backend-expert (Green): `backend/firma_contrato/application/consultar_estado_firma.py`
- [x] 3.3 qa-expert (Red): test de integración `GET /firma-contrato/estado`
- [x] 3.4 backend-expert (Green): endpoint en `backend/firma_contrato/infrastructure/api/router.py` + `schemas.py`

## 4. Backend: Revisar y Actualizar Unit Tests Existentes (OBLIGATORIO)

- [x] 4.1 Revisar suite completa de `backend/tests/` en busca de fixtures/tests afectados por los 3 endpoints nuevos (puramente aditivos, de solo lectura) — confirmar que no hace falta ningún cambio
- [x] 4.2 Confirmar que ningún test existente de `identidad`/`seguro_arrendamiento`/`firma_contrato`/`pagos`/`usuarios`/`agencias`/`inmuebles` se rompe

## 5. Backend: Correr Unit Tests y Verificar Estado de la Base de Datos (OBLIGATORIO)

- [x] 5.1 Capturar baseline de base de datos pre-test (conteos en `validaciones_identidad`, `polizas_arrendamiento`, `contratos`, `arrendamientos_activos`, `pagos` — no debe haber cambios de schema, solo endpoints nuevos)
- [x] 5.2 Correr los unit tests focalizados vía `docker compose exec backend pytest tests/identidad tests/seguro_arrendamiento tests/firma_contrato`
- [x] 5.3 Correr la suite completa vía `docker compose exec backend pytest`
- [x] 5.4 Verificar el estado post-test de la base de datos y restaurar si hace falta
- [x] 5.5 Crear el reporte `openspec/changes/frontend-flujo-arrendamiento/specs/reports/YYYY-MM-DD-step-5-unit-test-and-db-verification.md`
- [x] 5.6 Marcar este paso como completo solo después de que los tests pasen y el reporte exista

## 6. Backend: Testing Manual de Endpoints con curl (OBLIGATORIO - EL AGENTE DEBE EJECUTARLO)

- [x] 6.1 `docker compose up` con rebuild del backend
- [x] 6.2 curl: construir la cadena completa (identidad→seguro→firma-contrato→arrendamiento activo) sobre una cuenta de prueba
- [x] 6.3 curl `GET /identidad/estado` en cada punto de la cadena (antes de validar, después de aprobado) — verificar `no_iniciado` y `aprobado`
- [x] 6.4 curl `GET /seguro-arrendamiento/estado` en cada punto — verificar `no_iniciado` y `aprobada` con `prima_mensual`
- [x] 6.5 curl `GET /firma-contrato/estado` en cada punto — verificar `no_iniciado` y `firmado` con `arrendamiento_activo_id`
- [x] 6.6 Documentar los resultados en `openspec/changes/frontend-flujo-arrendamiento/specs/reports/YYYY-MM-DD-step-6-manual-curl-testing.md`

## 7. Frontend: scaffold del remote `arrendamiento-app`

- [x] 7.1 frontend-expert: crear `frontend/arrendamiento-app/` (rspack.config.ts, package.json, tsconfig.json) — mismo patrón que `inmuebles-app`, puerto propio (ej. 3002), expuesto como `arrendamientoApp/ArrendamientoRoutes`
- [x] 7.2 frontend-expert: agregar el remote a `frontend/shell/rspack.config.ts` (`remotes.arrendamientoApp`)
- [x] 7.3 Correr `cd frontend/shell && npx jest` y `cd frontend/arrendamiento-app && npx jest` (aunque vacío aún) — confirmar 0 regresiones tras el scaffold
- [x] 7.4 (encontrado en QA de la sección 15) Agregar `frontend/arrendamiento-app/Dockerfile` + `nginx.conf` (mismo patrón que `inmuebles-app`) y su servicio en `docker-compose.yml` (puerto 3002), más `http://localhost:3002` en `CORS_ALLOWED_ORIGINS` del backend — el scaffold original no incluía despliegue en modo producción/Docker, causando un crash real (`dispatcher.getOwner is not a function`, mismatch de React singleton) al servir el remote en dev mode contra el `shell` de producción. Verificado con Playwright MCP: build real (`docker compose build arrendamiento-app`), stack completo levantado, wizard carga correctamente sin errores de consola contra los 3 servicios en modo producción

## 8. Frontend: servicios de API por dominio

- [x] 8.1 qa-expert (Red): tests de `identidadService.ts` — `obtenerEstado()`, `validarIdentidad(cedula, imagenFrente, imagenDorso)`
- [x] 8.2 frontend-expert (Green): `frontend/arrendamiento-app/src/services/identidad.api.ts`
- [x] 8.3 qa-expert (Red): tests de `seguroService.ts` — `obtenerEstado()`, `contratarSeguro(documentos)`
- [x] 8.4 frontend-expert (Green): `frontend/arrendamiento-app/src/services/seguro.api.ts`
- [x] 8.5 qa-expert (Red): tests de `firmaService.ts` — `obtenerEstado()`, `generarContrato(nombrePropietario)`
- [x] 8.6 frontend-expert (Green): `frontend/arrendamiento-app/src/services/firma.api.ts`
- [x] 8.7 qa-expert (Red): tests de `pagosService.ts` — `obtenerHistorial(arrendamientoActivoId)`, `iniciarPago(pagoId)`
- [x] 8.8 frontend-expert (Green): `frontend/arrendamiento-app/src/services/pagos.api.ts`

## 9. Frontend: wizard — paso 1 (identidad)

- [x] 9.1 qa-expert (Red): tests RTL de `ValidarIdentidadPage` — muestra formulario (cédula + upload frente/dorso) si estado es `no_iniciado`/`rechazado`; muestra confirmación y botón "Siguiente" si `aprobado`; envía el formulario y refleja el resultado
- [x] 9.2 frontend-expert (Green): `frontend/arrendamiento-app/src/pages/ValidarIdentidadPage.tsx`, usando `Input`/`Button` de `@rentame/ui`

## 10. Frontend: wizard — paso 2 (seguro)

- [x] 10.1 qa-expert (Red): tests RTL de `ContratarSeguroPage` — no accesible si `identidad.estado != aprobado` (redirige al paso 1); muestra formulario si `seguro.estado` es `no_iniciado`/`rechazada`; muestra prima y confirmación si `aprobada`
- [x] 10.2 frontend-expert (Green): `frontend/arrendamiento-app/src/pages/ContratarSeguroPage.tsx`

## 11. Frontend: wizard — paso 3 (firma)

- [x] 11.1 qa-expert (Red): tests RTL de `GenerarContratoPage` — no accesible si `seguro.estado != aprobada` (redirige al paso 2); muestra formulario (nombre propietario) si `firma.estado` es `no_iniciado`; muestra estado `enviado_a_firma` mientras se espera; navega a "Mi arrendamiento" si `firmado`
- [x] 11.2 frontend-expert (Green): `frontend/arrendamiento-app/src/pages/GenerarContratoPage.tsx`

## 12. Frontend: "Mi arrendamiento"

- [x] 12.1 qa-expert (Red): tests RTL de `MiArrendamientoPage` — muestra historial completo (pendientes/completados/fallidos); botón "Pagar" visible solo si hay un `Pago` pendiente; al pagar, refleja el nuevo estado
- [x] 12.2 frontend-expert (Green): `frontend/arrendamiento-app/src/pages/MiArrendamientoPage.tsx`
- [x] 12.3 frontend-expert: `frontend/arrendamiento-app/src/ArrendamientoRoutes.tsx` — enruta los 3 pasos del wizard + "Mi arrendamiento", exponiéndolo vía Module Federation

## 13. Frontend: punto de entrada

- [x] 13.1 qa-expert (Red): tests RTL del botón "Solicitar arrendamiento" en `InmuebleDetallePublicoPage` — no visible si `rol != inquilino`; redirige a login/registro sin sesión; navega al wizard con sesión de inquilino
- [x] 13.2 frontend-expert (Green): agregar el botón en `frontend/inmuebles-app/src/pages/InmuebleDetallePublicoPage.tsx`, lazy-cargando `arrendamientoApp/ArrendamientoRoutes` desde el `shell`

## 14. Frontend: Revisar y Actualizar Unit Tests Existentes (OBLIGATORIO)

- [x] 14.1 Revisar suites de `shell`/`inmuebles-app`/`arrendamiento-app` en busca de tests afectados por el nuevo remote y el botón agregado
- [x] 14.2 Correr `cd frontend/shell && npx jest`, `cd frontend/inmuebles-app && npx jest`, `cd frontend/arrendamiento-app && npx jest` — confirmar 0 regresiones, documentar el conteo total de tests por paquete

## 15. Frontend: Testing E2E con Playwright MCP (OBLIGATORIO - EL AGENTE DEBE EJECUTARLO)

- [x] 15.1 Asegurar `docker compose up` corriendo con rebuild de `shell`/`inmuebles-app`/`arrendamiento-app`/backend
- [x] 15.2 E2E: inquilino sin sesión hace clic en "Solicitar arrendamiento" sobre un inmueble publicado — verificar redirección a login/registro
- [x] 15.3 E2E: inquilino autenticado completa el paso de identidad (con `FakeAdapter`, siempre aprueba) — verificar avance al paso de seguro
- [x] 15.4 E2E: completa el paso de seguro (`FakeAdapter`) — verificar avance al paso de firma
- [x] 15.5 E2E: completa el paso de firma (`FakeAdapter`, webhook simulado `firmado`) — verificar navegación a "Mi arrendamiento"
- [x] 15.6 E2E: en "Mi arrendamiento", verificar el `Pago` pendiente generado, iniciar el pago y simular el webhook `completado` — verificar que el historial refleja el pago completado
- [x] 15.7 E2E: propietario/agente no ve el botón "Solicitar arrendamiento" en el detalle del inmueble
- [x] 15.8 Restaurar el entorno (eliminar cuentas/datos de prueba creados durante el E2E)
- [x] 15.9 Documentar los escenarios y resultados en `openspec/changes/frontend-flujo-arrendamiento/specs/reports/YYYY-MM-DD-step-15-e2e-playwright.md`

## 16. Documentación (OBLIGATORIO)

- [x] 16.1 Actualizar `docs/architecture/architecture.md` con el nuevo remote `arrendamiento-app`, los 3 endpoints `GET /estado` nuevos, y el botón de entrada en `inmuebles-app`
- [x] 16.2 Actualizar `docs/user-stories/HU-004-validacion-identidad-inquilino.md`, `HU-005-analisis-riesgo-seguro-arrendamiento.md`, `HU-006-pago-mensual-renta.md` y `HU-009-firma-electronica-contrato-arrendamiento.md`, marcando los criterios de UI que quedaban pendientes ahora que existe frontend
