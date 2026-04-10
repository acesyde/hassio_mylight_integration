# MyLight Systems

🌐 **English** | [Français](README.fr.md) | [Português](README.pt.md) | [Deutsch](README.de.md) | [Español](README.es.md)

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

[![hacs][hacsbadge]][hacs]
![Project Maintenance][maintenance-shield]

_Integration to integrate with [MyLight Systems][mylight_systems]._

> [!Warning]
>
> This integration currently only supports the **MyHome** customer area. The **MyLight150** customer area is not yet supported.

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

### Switches

| Entity ID             | Description                                    | Notes                                        |
| --------------------- | ---------------------------------------------- | -------------------------------------------- |
| `switch.master_relay` | Controls the master relay on your installation | Only available when a relay device is paired |

## Installation

## Automatic

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=acesyde&repository=hassio_mylight_integration&category=integration)

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

The coordinator polls the API every 15 minutes. If values stop updating:

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
[hacs]: https://github.com/hacs/integration
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge
[license-shield]: https://img.shields.io/github/license/acesyde/hassio_mylight_integration.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-Pierre%20Emmanuel%20Mercier%20%40acesyde-blue.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/acesyde/hassio_mylight_integration.svg?style=for-the-badge
[releases]: https://github.com/acesyde/hassio_mylight_integration/releases
