# HU-003 — Búsqueda de inmuebles disponibles

## Historia
Como inquilino,
quiero buscar y filtrar inmuebles disponibles con información actualizada en tiempo real,
para encontrar opciones reales de arrendamiento sin perder tiempo visitando o contactando inmuebles que ya fueron arrendados.

## Criterios de aceptación
- [x] El inquilino puede buscar inmuebles sin necesidad de estar registrado en la plataforma.
- [x] Los resultados muestran únicamente inmuebles con estado "Disponible".
- [ ] **[Diferido a iteración futura]** El inquilino puede filtrar resultados por al menos: ciudad/barrio, valor máximo mensual, número mínimo de habitaciones y tipo de inmueble. *(Fuera de alcance de esta v1: el listado público v1 no incluye filtros de búsqueda; queda pendiente para una iteración posterior.)*
- [x] Cada resultado muestra como mínimo: foto principal, dirección general (barrio/sector), valor mensual, número de habitaciones y número de baños.
- [x] Al completarse un arrendamiento, el inmueble desaparece de los resultados de búsqueda de forma automática, sin intervención manual del propietario o agente. *(Cumplido por diseño en v1: el listado público filtra siempre por `estado == disponible`. Cuando exista HU-005 y marque un inmueble como `no_disponible`, este desaparecerá del listado sin requerir cambios adicionales en esta HU.)*
- [x] El inquilino puede acceder al detalle completo de un inmueble (todas las fotos, descripción, datos del formulario de publicación).
- [ ] **[Diferido — bloqueado por HU-005]** Desde el detalle del inmueble, el inquilino puede iniciar el proceso de solicitud de arrendamiento (acción que requiere registro/login). *(No implementable en esta v1: depende del dominio de arrendamiento (HU-005), que todavía no existe.)*
- [x] El listado público (`/`) reemplaza el punto de entrada actual del shell (`EntradaPage` de HU-008); el header del listado incluye un botón "Publicar mi inmueble" (hacia `EntradaPage`, que se mantiene) y un link "Iniciar sesión" (hacia `LoginPage`, ya existente).

## Notas técnicas
- La disponibilidad en tiempo real depende del evento de cambio de estado que se dispara en el flujo de arrendamiento (coordinación con HU-001 / HU-005). Si el sistema usa consistencia eventual, debe quedar claro el SLA de actualización.
- El mecanismo de búsqueda y filtrado debe definirse en diseño técnico (búsqueda full-text, índices, o motor de búsqueda dedicado). *(No aplica a esta v1, al no incluir filtros; queda como insumo para la iteración futura que los implemente.)*
- El acceso sin registro es intencional para reducir la fricción de descubrimiento; el registro se solicita solo al momento de iniciar una solicitud.
- **Decisión de producto/UX (v1):** el listado público (`/`) pasa a ser el punto de entrada de la aplicación, reemplazando a `EntradaPage` (pantalla de elegir rol de HU-008) en ese rol. `EntradaPage` no se elimina: se accede a ella mediante el botón "Publicar mi inmueble" en el header del listado público. El header también incluye un link "Iniciar sesión" hacia `LoginPage` (ya existente).
- **Decisión técnica (v1):** el listado y el detalle público se implementan dentro de `frontend/inmuebles-app` (nuevo componente expuesto vía Module Federation), reutilizando `inmuebles.api.ts` ya existente — no se implementan en `shell`, para mantener todo el dominio `Inmueble` en un solo microfrontend. `shell` solo monta el header con las dos acciones ("Publicar mi inmueble" / "Iniciar sesión") alrededor del listado.
- **Endpoints nuevos (v1):** `GET /inmuebles/publicos` (listado) y `GET /inmuebles/publicos/{id}` (detalle), ambos sin autenticación, dentro del dominio `inmuebles` ya existente (no se crea un dominio nuevo).

## Prioridad
Alta

## Estimación
05 — Grande (8h) — v1 reduce alcance a 2 endpoints de solo lectura, 2 páginas de frontend sin formularios y reordenamiento del entry point (filtros y solicitud de arrendamiento quedan diferidos).
