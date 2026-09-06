## Why

El PRD (HU-004) exige que todo inquilino valide su identidad con cédula colombiana antes de poder iniciar una solicitud de arrendamiento formal, para sostener un proceso 100% digital sin visitas presenciales ni envío de documentos por canales externos. Hoy no existe ningún mecanismo de verificación de identidad en el sistema — es un prerrequisito bloqueante de HU-005/HU-006, que aún no existen en el código. Se construye ahora, aislado, con un adapter fake para no quedar bloqueados por la ausencia del flujo de arrendamiento.

## What Changes

- Nuevo dominio `identidad`: aggregate `ValidacionIdentidad` (cédula, estado pendiente/aprobado/rechazado, fecha, referencia externa del proveedor).
- Puerto `ProveedorValidacionIdentidadPort` con dos adapters: `FakeAdapter` (dev/test, siempre aprueba) y `TruoraAdapter` (prod, llama la API real de Truora).
- Endpoint que recibe cédula + imagen frente/dorso, actúa como proxy hacia el proveedor sin persistir las imágenes — solo se guarda el resultado y la referencia externa (minimización de datos, Ley 1581 de 2012).
- Campo nuevo `identidad_verificada: bool` (default `False`) en el aggregate `Usuario` existente, marcado `True` cuando la validación es aprobada.
- La validación se ejecuta una sola vez por cuenta; una validación ya aprobada no se repite.
- Se documenta como invariante de especificación (sin guard clause en código todavía) que ninguna solicitud de arrendamiento puede iniciarse sin `identidad_verificada = True` — el flujo de arrendamiento (HU-005/006) aplicará este guard cuando exista.

## Capabilities

### New Capabilities
- `identidad`: validación de identidad del inquilino vía cédula colombiana contra un proveedor externo (Truora), con resultado aprobado/rechazado registrado y sin persistencia de las imágenes del documento.

### Modified Capabilities
- `usuarios`: se añade el atributo `identidad_verificada` al aggregate `Usuario` y la regla de que la cuenta solo se marca verificada una vez, de forma permanente.

## Impact

- Backend: nuevo paquete `backend/identidad/` (domain/application/infrastructure, mismo patrón hexagonal que `agencias`/`inmuebles`/`usuarios`); migración Alembic para tabla `validaciones_identidad` y columna `identidad_verificada` en `usuarios`; nueva dependencia HTTP hacia Truora (solo en `TruoraAdapter`, no en dev/test).
- Frontend: sin cambio en esta iteración — no hay todavía pantalla de arrendamiento que consuma el flag; se documenta pero no se construye UI hasta que exista HU-005/006 (fuera de alcance de este change).
- Rollback: feature aislada y aditiva (nueva tabla + nueva columna con default `False`); revertir es dropear la migración y el paquete `identidad/` sin afectar dominios existentes, ya que ningún flujo actual depende de `identidad_verificada`.
