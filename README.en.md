# MyLight Systems

🌐 **English** | [Français](README.md) | [Português](README.pt.md) | [Deutsch](README.de.md) | [Español](README.es.md)

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

[![marketplace][marketplacebadge]][marketplace]
![Project Maintenance][maintenance-shield]

_Integration to integrate with [MyLight Systems][mylight_systems]._

> [!Warning]
>
> This integration currently only supports the **MyHome** customer area. For **MyLight150** support, a dedicated extension is available at [Racailloux/mylight150_ha](https://github.com/Racailloux/mylight150_ha).

**This integration will set up the following platforms.**

## Provided Entities

### Sensors

| Entity ID                                       | Description                                         | Unit | State Class        |
| ----------------------------------------------- | --------------------------------------------------- | ---- | ------------------ |
| `sensor.total_solar_production`                 | Cumulative energy produced by solar panels          | Wh   | `total_increasing` |
| `sensor.total_grid_consumption`                 | Grid energy drawn (accounting for virtual battery)  | Wh   | `total_increasing` |
| `sensor.total_grid_without_battery_consumption` | Grid energy drawn (excluding virtual battery)       | Wh   | `total_increasing` |
| `sensor.total_autonomy_rate`                    | % of consumption covered by solar + battery         | %    | `measurement`      |
| `sensor.total_self_conso`                       | % of solar production consumed locally              | %    | `measurement`      |
| `sensor.total_msb_charge`                       | Cumulative energy charged into the Smart Battery    | Wh   | `total_increasing` |
| `sensor.total_msb_discharge`                    | Cumulative energy discharged from the Smart Battery | Wh   | `total_increasing` |
| `sensor.total_green_energy`                     | Solar energy consumed directly by your home         | Wh   | `total_increasing` |
| `sensor.battery_state`                          | Current energy stored in the Smart Battery          | kWh  | `measurement`      |
| `sensor.grid_returned_energy`                   | Solar energy exported back to the grid              | Wh   | `total_increasing` |
| `sensor.grid_power`                             | Instantaneous grid power (positive: import, negative: export) | W | `measurement` |
| `sensor.grid_import_power`                      | Power drawn from the grid (instantaneous) | W | `measurement` |
| `sensor.grid_export_power`                      | Power exported to the grid (instantaneous) | W | `measurement` |
| `sensor.solar_power`                            | Solar production power | W | `measurement` |
| `sensor.consumption_power`                      | Home consumption power | W | `measurement` |
| `sensor.grid_returned_power`                    | Power returned to the grid (without a virtual battery) | W | `measurement` |
| `sensor.grid_net_power`                         | Grid net power (positive: import, negative: export). With a virtual battery: "Billed grid net power" | W | `measurement` |
| `sensor.msb_charge_power`                       | Virtual battery charge power | W | `measurement` |
| `sensor.msb_discharge_power`                    | Power covered by the virtual battery | W | `measurement` |
| `sensor.msb_net_power`                          | Virtual battery net power (positive: discharge, negative: charge) | W | `measurement` |
| `sensor.grid_billed_power`                      | Billed grid import power (virtual battery empty) | W | `measurement` |

> `grid_power`, `grid_import_power`, `grid_export_power`: only created when a single grid meter is detected. Point reading taken from the meter at each update: it can differ from the interval average. For the Energy dashboard, prefer the computed powers below.
>
> `solar_power`, `consumption_power`, `grid_net_power`, `grid_returned_power`: averages over the update interval, computed from the MyLight energy counters, so they match the kWh totals to the Wh. Keep the default 5-minute interval, MyLight's measurement step (longer intervals smooth the curve). No value during the first interval after a startup (two readings are needed). With a virtual battery, `grid_net_power` only counts the billed import.
>
> `msb_charge_power`, `msb_discharge_power`, `msb_net_power`, `grid_billed_power`: same computation, available only when a virtual battery is detected. `grid_returned_power` is then not created: MyLight counts every exported Wh as a charge, so the return is always 0. For the same reason `grid_net_power` (renamed "Billed grid net power") and `grid_billed_power` have the same value: the first is for the Energy dashboard single signed sensor mode, the second for the two-sensor mode.

### Switches

| Entity ID             | Description                                    | Notes                                        |
| --------------------- | ---------------------------------------------- | -------------------------------------------- |
| `switch.master_relay` | Controls the master relay on your installation | Only available when a relay device is paired |

## Configure the Energy dashboard

In **Settings → Dashboards → Energy**, set each source's energy counters, then, for power, **a single signed sensor** (standard mode: positive when energy flows into the home, negative when it flows out). Home Assistant then does not need to create its own net power sensors, and the "Power sources" graph matches the kWh totals exactly.

Actual entity IDs include your device name: search the sensors by name (in parentheses below, in English).

| Source | Energy | Power (single sensor) |
|---|---|---|
| Grid | Consumption: `total_grid_without_battery_consumption` with a virtual battery, otherwise `total_grid_consumption`. Return: `grid_returned_energy` | `grid_net_power` (Grid net power, or Billed grid net power with a virtual battery) |
| Solar | `total_solar_production` | `solar_power` (Solar power) |
| Battery (virtual battery only) | Discharge: `total_msb_discharge`. Charge: `total_msb_charge` | `msb_net_power` (Virtual battery net power) |

1. **Grid**: edit (or add) the grid source, pick the counters above, then in the power part the single-sensor mode with `grid_net_power`.
2. **Solar**: edit (or add) the solar production with `total_solar_production` and the power `solar_power`.
3. **Battery** (if you have a virtual battery): add a battery storage with `total_msb_discharge` (energy coming out of the battery) and `total_msb_charge` (energy going into the battery), then the power `msb_net_power` in single-sensor mode.

> **Why not `total_grid_consumption` or `grid_power` with a virtual battery?** MyLight counts exported energy as a virtual battery charge and imports covered by your credit as a discharge: only the billed part is grid. The counters above follow that logic; `grid_power` measures the physical flow and would count the battery as grid.
>
> `consumption_power` is not needed here: Home Assistant computes consumption from the sources. Use it to display consumption elsewhere (cards, automations).

## Installation

## Home Assistant Marketplace (2026.11+)

1. In Home Assistant, go to **Settings → Marketplace**.
2. Choose **Add from link**, paste `https://github.com/acesyde/hassio_mylight_integration` and connect your GitHub account if asked.
3. Install **MyLight Systems**, then restart Home Assistant.

Or click this button:

[![Open your Home Assistant instance and open a repository inside the Home Assistant Marketplace.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=acesyde&repository=hassio_mylight_integration&category=integration)

> Since 2026.11, HACS is built into Home Assistant as the Marketplace. Existing HACS installs are migrated automatically.

## Manual

1. Using the tool of choice open the directory (folder) for your HA configuration (where you find `configuration.yaml`).
2. If you do not have a `custom_components` directory (folder) there, you need to create it.
   3In the `custom_components` directory (folder) create a new folder called `mylight_systems`.
3. Download _all_ the files from the `custom_components/mylight_systems/` directory (folder) in this repository.
4. Place the files you downloaded in the new directory (folder) you created.
5. Restart Home Assistant
6. In the HA UI go to "Configuration" -> "Integrations" click "+" and search for "MyLight Systems"

## Configuration is done in the UI

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for the full component diagram and data flow.

## Troubleshooting

### "Relay switch is missing"

The `switch.master_relay` entity is only created when a relay device (`sw` type) is paired to your installation. If you do not have a relay, this entity will not appear.

### "Sensor values are stuck / not updating"

The coordinator polls the API every 5 minutes by default (adjustable in the integration options, 5 minutes minimum). If values stop updating:

1. Open **Settings → Devices & Services → MyLight Systems** and check for an error banner.
2. Enable debug logging and check the Home Assistant logs:

```yaml
# configuration.yaml
logger:
  default: warning
  logs:
    custom_components.mylight_systems: debug
```

3. Look for `CommunicationError` or `UpdateFailed` entries — these indicate a network issue or an API change.

### "Authentication failed" after a password change

If you change your MyLight password externally, the integration will show an authentication error. Go to **Settings → Devices & Services → MyLight Systems** and use the **Re-authenticate** option to enter your new credentials.

## Contributions are welcome!

If you want to contribute to this please read the [Contribution guidelines](CONTRIBUTING.md)

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
