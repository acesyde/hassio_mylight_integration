# MyLight Systems

🌐 [English](README.en.md) | [Français](README.md) | [Português](README.pt.md) | [Deutsch](README.de.md) | **Español**

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

[![marketplace][marketplacebadge]][marketplace]
![Project Maintenance][maintenance-shield]

_Integración para conectar con [MyLight Systems][mylight_systems]._

> [!Warning]
>
> Esta integración actualmente solo es compatible con el área de cliente **MyHome**. Para soporte de **MyLight150**, una extensión dedicada está disponible en [Racailloux/mylight150_ha](https://github.com/Racailloux/mylight150_ha).

**Esta integración configurará las siguientes plataformas.**

## Entidades proporcionadas

### Sensores

| ID de entidad                                   | Descripción                                            | Unidad | Clase de estado    |
| ----------------------------------------------- | ------------------------------------------------------ | ------ | ------------------ |
| `sensor.total_solar_production`                 | Energía acumulada producida por los paneles solares    | Wh     | `total_increasing` |
| `sensor.total_grid_consumption`                 | Energía consumida de la red (con batería virtual)      | Wh     | `total_increasing` |
| `sensor.total_grid_without_battery_consumption` | Energía consumida de la red (sin batería virtual)      | Wh     | `total_increasing` |
| `sensor.total_autonomy_rate`                    | % del consumo cubierto por solar + batería             | %      | `measurement`      |
| `sensor.total_self_conso`                       | % de la producción solar consumida localmente          | %      | `measurement`      |
| `sensor.total_msb_charge`                       | Energía acumulada cargada en la Smart Battery          | Wh     | `total_increasing` |
| `sensor.total_msb_discharge`                    | Energía acumulada descargada de la Smart Battery       | Wh     | `total_increasing` |
| `sensor.total_green_energy`                     | Energía solar consumida directamente por su hogar      | Wh     | `total_increasing` |
| `sensor.battery_state`                          | Energía almacenada actualmente en la Smart Battery     | kWh    | `measurement`      |
| `sensor.grid_returned_energy`                   | Energía solar exportada a la red                       | Wh     | `total_increasing` |
| `sensor.grid_power`                             | Potencia instantánea de red (positiva: importación, negativa: exportación) | W | `measurement` |
| `sensor.grid_import_power`                      | Potencia importada de la red (instantánea) | W | `measurement` |
| `sensor.grid_export_power`                      | Potencia exportada a la red (instantánea) | W | `measurement` |
| `sensor.solar_power`                            | Potencia de producción solar | W | `measurement` |
| `sensor.consumption_power`                      | Potencia consumida por la vivienda | W | `measurement` |
| `sensor.grid_returned_power`                    | Potencia devuelta a la red (sin batería virtual) | W | `measurement` |
| `sensor.grid_net_power`                         | Potencia neta de la red (positiva: importación, negativa: exportación). Con batería virtual: «Potencia neta de la red facturada» | W | `measurement` |
| `sensor.msb_charge_power`                       | Potencia de carga de la batería virtual | W | `measurement` |
| `sensor.msb_discharge_power`                    | Potencia cubierta por la batería virtual | W | `measurement` |
| `sensor.msb_net_power`                          | Potencia neta de la batería virtual (positiva: descarga, negativa: carga) | W | `measurement` |
| `sensor.grid_billed_power`                      | Potencia importada facturada (batería virtual vacía) | W | `measurement` |

> `grid_power`, `grid_import_power`, `grid_export_power`: solo se crean si se detecta un único contador de red. Lectura puntual del contador en cada actualización: puede diferir del promedio del intervalo. Para el panel de Energía, prefiera las potencias calculadas de abajo.
>
> `solar_power`, `consumption_power`, `grid_net_power`, `grid_returned_power`: promedios sobre el intervalo de actualización, calculados a partir de los contadores de energía de MyLight, por lo que coinciden al Wh con los totales en kWh. Mantenga el intervalo por defecto de 5 minutos, el paso de medición de MyLight (intervalos más largos suavizan la curva). Sin valor durante el primer intervalo tras un arranque (se necesitan dos lecturas). Con una batería virtual, `grid_net_power` solo cuenta la importación facturada.
>
> `msb_charge_power`, `msb_discharge_power`, `msb_net_power`, `grid_billed_power`: mismo cálculo, disponibles solo si se detecta una batería virtual. `grid_returned_power` no se crea entonces: MyLight cuenta cada Wh exportado como carga, el retorno siempre vale 0. Por la misma razón, `grid_net_power` (renombrado «Potencia neta de la red facturada») y `grid_billed_power` tienen el mismo valor: el primero sirve para el modo de un único sensor con signo del panel de Energía, el segundo para el modo de dos sensores.

### Interruptores

| ID de entidad         | Descripción                                          | Notas                                                |
| --------------------- | ---------------------------------------------------- | ---------------------------------------------------- |
| `switch.master_relay` | Controla el relé principal de su instalación         | Solo disponible cuando un relé está emparejado       |

## Configurar el panel de Energía

En **Ajustes → Paneles de control → Energía**, indique para cada fuente sus contadores de energía y, para la potencia, **un único sensor con signo** (modo estándar: positivo cuando la energía entra en la vivienda, negativo cuando sale). Home Assistant ya no necesita crear sus propios sensores de potencia neta, y el gráfico «Fuentes de potencia» coincide exactamente con los totales en kWh.

Los ID de entidad reales incluyen el nombre de su dispositivo: busque los sensores por su nombre visible, indicado entre comillas abajo (en español), sin añadir nada.

| Fuente | Energía | Potencia (un único sensor) |
|---|---|---|
| Red, con batería virtual | Consumo: `total_grid_without_battery_consumption`. Retorno: `grid_returned_energy` | `grid_net_power`: «Potencia neta de la red facturada» |
| Red, sin batería virtual | Consumo: `total_grid_consumption`. Retorno: `grid_returned_energy` | `grid_net_power`: «Potencia neta de la red» |
| Solar | `total_solar_production` | `solar_power`: «Potencia solar» |
| Batería (solo batería virtual) | Descarga: `total_msb_discharge`. Carga: `total_msb_charge` | `msb_net_power`: «Potencia neta de la batería virtual» |

1. **Red**: edite (o añada) la fuente de red, elija los contadores anteriores y, en la parte de potencia, el modo de un único sensor con `grid_net_power`.
2. **Solar**: edite (o añada) la producción solar con `total_solar_production` y la potencia `solar_power`.
3. **Batería** (si tiene batería virtual): añada un almacenamiento con `total_msb_discharge` (energía que sale de la batería) y `total_msb_charge` (energía que entra en la batería), y la potencia `msb_net_power` en modo de un único sensor.

> **¿Por qué no `total_grid_consumption` ni `grid_power` con batería virtual?** MyLight cuenta la energía exportada como carga de la batería virtual y la importación cubierta por su crédito como descarga: solo la parte facturada es red. Los contadores anteriores siguen esa lógica; `grid_power` mide el flujo físico y contaría la batería como red.
>
> `consumption_power` no es necesario aquí: Home Assistant calcula el consumo a partir de las fuentes. Sirve para mostrarlo en otros lugares (tarjetas, automatizaciones).

## Instalación

## Marketplace de Home Assistant (2026.11+)

1. En Home Assistant, vaya a **Ajustes → Marketplace**.
2. Elija **Add from link**, pegue `https://github.com/acesyde/hassio_mylight_integration` y conecte su cuenta de GitHub si se le solicita.
3. Instale **MyLight Systems** y reinicie Home Assistant.

O haga clic en este botón:

[![Abra su instancia de Home Assistant y abra un repositorio en el Home Assistant Marketplace.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=acesyde&repository=hassio_mylight_integration&category=integration)

> Desde 2026.11, HACS está integrado en Home Assistant como Marketplace. Las instalaciones existentes de HACS se migran automáticamente.

## Manual

1. Abra el directorio de su configuración de HA (donde se encuentra `configuration.yaml`).
2. Si no tiene un directorio `custom_components`, créelo.
3. Dentro de `custom_components`, cree una nueva carpeta llamada `mylight_systems`.
4. Descargue _todos_ los archivos del directorio `custom_components/mylight_systems/` de este repositorio.
5. Coloque los archivos descargados en la nueva carpeta creada.
6. Reinicie Home Assistant.
7. En la interfaz de HA, vaya a "Configuración" → "Integraciones", haga clic en "+" y busque "MyLight Systems".

## La configuración se realiza desde la interfaz

## Arquitectura

Consulte [ARCHITECTURE.md](ARCHITECTURE.md) para el diagrama completo de componentes y el flujo de datos.

## Solución de problemas

### "Falta el interruptor de relé"

La entidad `switch.master_relay` solo se crea cuando un relé (`sw`) está emparejado a su instalación. Si no tiene un relé, esta entidad no aparecerá.

### "Los valores de los sensores están congelados / no se actualizan"

El coordinador consulta la API cada 5 minutos por defecto (ajustable en las opciones de la integración, mínimo 5 minutos). Si los valores dejan de actualizarse:

1. Abra **Ajustes → Dispositivos y servicios → MyLight Systems** y verifique si hay un aviso de error.
2. Active el registro de depuración y revise los registros de Home Assistant:

```yaml
# configuration.yaml
logger:
  default: warning
  logs:
    custom_components.mylight_systems: debug
```

3. Busque entradas `CommunicationError` o `UpdateFailed` — indican un problema de red o un cambio en la API.

### "Error de autenticación" tras cambiar la contraseña

Si cambió su contraseña de MyLight externamente, la integración mostrará un error de autenticación. Vaya a **Ajustes → Dispositivos y servicios → MyLight Systems** y use la opción **Volver a autenticar** para introducir sus nuevas credenciales.

## ¡Las contribuciones son bienvenidas!

Si desea contribuir, lea las [directrices de contribución](CONTRIBUTING.md).

---

[mylight_systems]: https://www.mylight-systems.com/
[commits-shield]: https://img.shields.io/github/commit-activity/y/acesyde/hassio_mylight_integration.svg?style=for-the-badge
[commits]: https://github.com/acesyde/hassio_mylight_integration/commits/main
[marketplace]: https://www.home-assistant.io/integrations/marketplace/#custom-repositories
[marketplacebadge]: https://img.shields.io/badge/Marketplace-Custom-orange.svg?style=for-the-badge
[license-shield]: https://img.shields.io/github/license/acesyde/hassio_mylight_integration.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-Pierre%20Emmanuel%20Mercier%20%40acesyde-blue.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/acesyde/hassio_mylight_integration.svg?style=for-the-badge
[releases]: https://github.com/acesyde/hassio_mylight_integration/releases
