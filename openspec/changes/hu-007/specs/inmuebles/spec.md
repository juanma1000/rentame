## ADDED Requirements

### Requirement: Despublicación en cascada por revocación de agencia
Cuando una relación agencia-propietario pasa a estado revocada (por revocación explícita del propietario o por reemplazo automático al activar una nueva agencia), el sistema SHALL despublicar (cambiar a estado oculto) todos los inmuebles de ese propietario cuyo agente gestor pertenezca a la agencia revocada. Esta operación SHALL reutilizar la operación de cambio de disponibilidad ya existente de la capacidad `inmuebles`, sin modificar su contrato.

#### Scenario: Revocar la agencia despublica los inmuebles que gestionaba
- **GIVEN** un propietario con una relación activa con una agencia, y un inmueble de ese propietario en estado disponible gestionado por un agente de esa agencia
- **WHEN** la relación agencia-propietario pasa a estado revocada
- **THEN** el inmueble pasa a estado oculto sin acción manual del propietario

#### Scenario: Inmuebles publicados directamente por el propietario no se ven afectados
- **GIVEN** un propietario con una relación activa con una agencia, y un inmueble de ese propietario publicado directamente por él mismo (sin agente gestor)
- **WHEN** la relación agencia-propietario pasa a estado revocada
- **THEN** el estado de ese inmueble no cambia
