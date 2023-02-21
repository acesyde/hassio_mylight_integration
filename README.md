# MyLight Systems

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

[![hacs][hacsbadge]][hacs]
![Project Maintenance][maintenance-shield]

_Integration to integrate with [MyLight Systems][mylight_systems]._

**This integration will set up the following platforms.**

| Platform                                  | Description                                                      | Implemented        |
| ----------------------------------------- | ---------------------------------------------------------------- | ------------------ |
| `sensor.solar_production`                 | Current solar power production.                                  | :white_check_mark: |
| `sensor.grid_with_battery_consumption`    | Current power consumption from the grid with virtual battery.    | :white_check_mark: |
| `sensor.grid_without_battery_consumption` | Current power consumption from the grid without virtual battery. | :white_check_mark: |
| `sensor.autonomy_rate`                    | Autonomy rate.                                                   | :white_check_mark: |
| `sensor.self_conso`                       | Self consumption.                                                | :white_check_mark: |
| `sensor.virtual_battery_charge`           | Current virtual battery charge.                                  | :black_circle:     |
| `sensor.virtual_battery_discharge`        | Current virtual battery discharge.                               | :black_circle:     |

## Installation

1. Using the tool of choice open the directory (folder) for your HA configuration (where you find `configuration.yaml`).
1. If you do not have a `custom_components` directory (folder) there, you need to create it.
1. In the `custom_components` directory (folder) create a new folder called `mylight_systems`.
1. Download _all_ the files from the `custom_components/mylight_systems/` directory (folder) in this repository.
1. Place the files you downloaded in the new directory (folder) you created.
1. Restart Home Assistant
1. In the HA UI go to "Configuration" -> "Integrations" click "+" and search for "Integration blueprint"

## Configuration is done in the UI

<!---->

## Contributions are welcome!

If you want to contribute to this please read the [Contribution guidelines](CONTRIBUTING.md)

***

[mylight_systems]: https://www.mylight-systems.com/
[commits-shield]: https://img.shields.io/github/commit-activity/y/acesyde/hassio_mylight_integration.svg?style=for-the-badge
[commits]: https://github.com/acesyde/hassio_mylight_integration/commits/main
[hacs]: https://github.com/hacs/integration
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge
[license-shield]: https://img.shields.io/github/license/acesyde/hassio_mylight_integration.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-Pierre%20Emmanuel%20Mercier%20%40acesyde-blue.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/acesyde/hassio_mylight_integration.svg?style=for-the-badge
[releases]: https://github.com/acesyde/hassio_mylight_integration/releases
