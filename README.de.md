# MyLight Systems

🌐 [English](README.md) | [Français](README.fr.md) | [Português](README.pt.md) | **Deutsch** | [Español](README.es.md)

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

[![hacs][hacsbadge]][hacs]
![Project Maintenance][maintenance-shield]

_Integration zur Verbindung mit [MyLight Systems][mylight_systems]._

> [!Warning]
>
> Diese Integration unterstützt derzeit nur den Kundenbereich **MyHome**. Der Kundenbereich **MyLight150** wird noch nicht unterstützt.

**Diese Integration richtet die folgenden Plattformen ein.**

## Bereitgestellte Entitäten

### Sensoren

| Entitäts-ID                                     | Beschreibung                                           | Einheit | Statusklasse       |
| ----------------------------------------------- | ------------------------------------------------------ | ------- | ------------------ |
| `sensor.total_solar_production`                 | Kumulierte Energie aus Solarmodulen                    | Wh      | `total_increasing` |
| `sensor.total_grid_consumption`                 | Netzbezug (mit virtueller Batterie)                    | Wh      | `total_increasing` |
| `sensor.total_grid_without_battery_consumption` | Netzbezug (ohne virtuelle Batterie)                    | Wh      | `total_increasing` |
| `sensor.total_autonomy_rate`                    | % des Verbrauchs gedeckt durch Solar + Batterie        | %       | `measurement`      |
| `sensor.total_self_conso`                       | % der Solarproduktion lokal verbraucht                 | %       | `measurement`      |
| `sensor.total_msb_charge`                       | Kumulierte Energie in die Smart Battery geladen        | Wh      | `total_increasing` |
| `sensor.total_msb_discharge`                    | Kumulierte Energie aus der Smart Battery entladen      | Wh      | `total_increasing` |
| `sensor.total_green_energy`                     | Solarenergie direkt vom Haushalt verbraucht            | Wh      | `total_increasing` |
| `sensor.battery_state`                          | Aktuell in der Smart Battery gespeicherte Energie      | kWh     | `measurement`      |
| `sensor.grid_returned_energy`                   | Solarenergie ins Netz eingespeist                      | Wh      | `total_increasing` |

### Schalter

| Entitäts-ID           | Beschreibung                                        | Hinweise                                          |
| --------------------- | --------------------------------------------------- | ------------------------------------------------- |
| `switch.master_relay` | Steuert das Hauptrelais Ihrer Installation          | Nur verfügbar, wenn ein Relais gekoppelt ist      |

## Installation

## Automatisch

[![Öffnen Sie Ihre Home Assistant-Instanz und öffnen Sie ein Repository im Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=acesyde&repository=hassio_mylight_integration&category=integration)

## Manuell

1. Öffnen Sie das Verzeichnis Ihrer HA-Konfiguration (dort wo sich `configuration.yaml` befindet).
2. Falls kein Verzeichnis `custom_components` vorhanden ist, erstellen Sie es.
3. Erstellen Sie in `custom_components` einen neuen Ordner namens `mylight_systems`.
4. Laden Sie _alle_ Dateien aus dem Verzeichnis `custom_components/mylight_systems/` dieses Repositories herunter.
5. Legen Sie die heruntergeladenen Dateien in den neu erstellten Ordner.
6. Starten Sie Home Assistant neu.
7. Gehen Sie in der HA-Oberfläche zu „Konfiguration" → „Integrationen", klicken Sie auf „+" und suchen Sie nach „MyLight Systems".

## Die Konfiguration erfolgt über die Benutzeroberfläche

## Architektur

Siehe [ARCHITECTURE.md](ARCHITECTURE.md) für das vollständige Komponentendiagramm und den Datenfluss.

## Fehlerbehebung

### „Relais-Schalter fehlt"

Die Entität `switch.master_relay` wird nur erstellt, wenn ein Relais (`sw`) mit Ihrer Installation gekoppelt ist. Ohne Relais erscheint diese Entität nicht.

### „Sensorwerte sind eingefroren / aktualisieren sich nicht"

Der Koordinator fragt die API alle 15 Minuten ab. Wenn sich die Werte nicht mehr aktualisieren:

1. Öffnen Sie **Einstellungen → Geräte und Dienste → MyLight Systems** und prüfen Sie, ob ein Fehlerbanner angezeigt wird.
2. Aktivieren Sie das Debug-Logging und prüfen Sie die Home Assistant-Protokolle:

```yaml
# configuration.yaml
logger:
  default: warning
  logs:
    custom_components.mylight_systems: debug
```

3. Suchen Sie nach `CommunicationError`- oder `UpdateFailed`-Einträgen — diese weisen auf ein Netzwerkproblem oder eine API-Änderung hin.

### „Authentifizierung fehlgeschlagen" nach Passwortänderung

Wenn Sie Ihr MyLight-Passwort extern geändert haben, zeigt die Integration einen Authentifizierungsfehler an. Gehen Sie zu **Einstellungen → Geräte und Dienste → MyLight Systems** und verwenden Sie die Option **Erneut authentifizieren**, um Ihre neuen Zugangsdaten einzugeben.

## Beiträge sind willkommen!

Wenn Sie beitragen möchten, lesen Sie bitte die [Beitragsrichtlinien](CONTRIBUTING.md).

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
