# MyLight Systems

🌐 [English](README.en.md) | [Français](README.md) | [Português](README.pt.md) | **Deutsch** | [Español](README.es.md)

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

[![marketplace][marketplacebadge]][marketplace]
![Project Maintenance][maintenance-shield]

_Integration zur Verbindung mit [MyLight Systems][mylight_systems]._

> [!Warning]
>
> Diese Integration unterstützt derzeit nur den Kundenbereich **MyHome**. Für **MyLight150**-Support steht eine separate Erweiterung unter [Racailloux/mylight150_ha](https://github.com/Racailloux/mylight150_ha) zur Verfügung.

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
| `sensor.grid_power`                             | Momentane Netzleistung (positiv: Bezug, negativ: Einspeisung) | W | `measurement` |
| `sensor.grid_import_power`                      | Aus dem Netz bezogene Leistung (momentan) | W | `measurement` |
| `sensor.grid_export_power`                      | Ins Netz eingespeiste Leistung (momentan) | W | `measurement` |
| `sensor.solar_power`                            | Solare Erzeugungsleistung | W | `measurement` |
| `sensor.consumption_power`                      | Verbrauchsleistung des Haushalts | W | `measurement` |
| `sensor.grid_returned_power`                    | Ins Netz zurückgespeiste Leistung (ohne virtuelle Batterie) | W | `measurement` |
| `sensor.grid_net_power`                         | Netto-Netzleistung (positiv: Bezug, negativ: Einspeisung). Mit virtueller Batterie: „Abgerechnete Netto-Netzleistung“ | W | `measurement` |
| `sensor.msb_charge_power`                       | Ladeleistung der virtuellen Batterie | W | `measurement` |
| `sensor.msb_discharge_power`                    | Von der virtuellen Batterie gedeckte Leistung | W | `measurement` |
| `sensor.msb_net_power`                          | Nettoleistung der virtuellen Batterie (positiv: Entladung, negativ: Ladung) | W | `measurement` |
| `sensor.grid_billed_power`                      | Abgerechnete Netzbezugsleistung (virtuelle Batterie leer) | W | `measurement` |

> `grid_power`, `grid_import_power`, `grid_export_power`: nur bei genau einem erkannten Netzzähler vorhanden. Punktueller Zählerwert bei jeder Aktualisierung: kann vom Mittelwert des Intervalls abweichen. Für das Energie-Dashboard die unten berechneten Leistungen bevorzugen.
>
> `solar_power`, `consumption_power`, `grid_net_power`, `grid_returned_power`: Mittelwerte über das Aktualisierungsintervall, berechnet aus den MyLight-Energiezählern, daher auf die Wh genau mit den kWh-Summen übereinstimmend. Standardintervall von 5 Minuten beibehalten, entspricht dem Messschritt von MyLight (längere Intervalle glätten die Kurve). Im ersten Intervall nach einem Start kein Wert (zwei Messwerte nötig). Mit virtueller Batterie zählt `grid_net_power` nur den abgerechneten Bezug.
>
> `msb_charge_power`, `msb_discharge_power`, `msb_net_power`, `grid_billed_power`: gleiche Berechnung, nur verfügbar, wenn eine virtuelle Batterie erkannt wird. `grid_returned_power` wird dann nicht angelegt: MyLight zählt jede eingespeiste Wh als Ladung, die Rückspeisung ist immer 0. Aus demselben Grund haben `grid_net_power` (umbenannt in „Abgerechnete Netto-Netzleistung“) und `grid_billed_power` denselben Wert: das erste ist für den Einzelsensor-Modus (vorzeichenbehaftet) des Energie-Dashboards, das zweite für den Zwei-Sensoren-Modus.

### Schalter

| Entitäts-ID           | Beschreibung                                        | Hinweise                                          |
| --------------------- | --------------------------------------------------- | ------------------------------------------------- |
| `switch.master_relay` | Steuert das Hauptrelais Ihrer Installation          | Nur verfügbar, wenn ein Relais gekoppelt ist      |

## Energie-Dashboard konfigurieren

Unter **Einstellungen → Dashboards → Energie** für jede Quelle die Energiezähler eintragen und für die Leistung **einen einzelnen vorzeichenbehafteten Sensor** wählen (Standardmodus: positiv, wenn Energie ins Haus fließt, negativ, wenn sie hinausfließt). Home Assistant muss dann keine eigenen Nettoleistungssensoren anlegen, und das Diagramm „Leistungsquellen“ entspricht genau den kWh-Summen.

Die tatsächlichen Entitäts-IDs enthalten Ihren Gerätenamen: Sensoren nach ihrem Anzeigenamen suchen, unten in Anführungszeichen (auf Deutsch), ohne etwas hinzuzufügen.

| Quelle | Energie | Leistung (einzelner Sensor) |
|---|---|---|
| Netz, mit virtueller Batterie | Bezug: `total_grid_without_battery_consumption`. Rückspeisung: `grid_returned_energy` | `grid_net_power`: „Abgerechnete Netto-Netzleistung“ |
| Netz, ohne virtuelle Batterie | Bezug: `total_grid_consumption`. Rückspeisung: `grid_returned_energy` | `grid_net_power`: „Netto-Netzleistung“ |
| Solar | `total_solar_production` | `solar_power`: „Solarleistung“ |
| Batterie (nur virtuelle Batterie) | Entladung: `total_msb_discharge`. Ladung: `total_msb_charge` | `msb_net_power`: „Nettoleistung der virtuellen Batterie“ |

1. **Netz**: Netzquelle bearbeiten (oder hinzufügen), obige Zähler wählen, dann im Leistungsteil den Einzelsensor-Modus mit `grid_net_power`.
2. **Solar**: Solarproduktion mit `total_solar_production` und der Leistung `solar_power` bearbeiten (oder hinzufügen).
3. **Batterie** (bei virtueller Batterie): Batteriespeicher mit `total_msb_discharge` (Energie aus der Batterie) und `total_msb_charge` (Energie in die Batterie) hinzufügen, dann die Leistung `msb_net_power` im Einzelsensor-Modus.

> **Warum nicht `total_grid_consumption` oder `grid_power` mit virtueller Batterie?** MyLight zählt eingespeiste Energie als Ladung der virtuellen Batterie und durch Ihr Guthaben gedeckten Bezug als Entladung: nur der abgerechnete Teil ist Netz. Die obigen Zähler folgen dieser Logik; `grid_power` misst den physischen Fluss und würde die Batterie als Netz zählen.
>
> `consumption_power` wird hier nicht benötigt: Home Assistant berechnet den Verbrauch aus den Quellen. Es dient zur Anzeige an anderer Stelle (Karten, Automatisierungen).

## Installation

## Home Assistant Marketplace (2026.11+)

1. Gehen Sie in Home Assistant zu **Einstellungen → Marketplace**.
2. Wählen Sie **Add from link**, fügen Sie `https://github.com/acesyde/hassio_mylight_integration` ein und verbinden Sie bei Aufforderung Ihr GitHub-Konto.
3. Installieren Sie **MyLight Systems** und starten Sie Home Assistant neu.

Oder klicken Sie auf diese Schaltfläche:

[![Öffnen Sie Ihre Home Assistant-Instanz und öffnen Sie ein Repository im Home Assistant Marketplace.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=acesyde&repository=hassio_mylight_integration&category=integration)

> Seit 2026.11 ist HACS als Marketplace in Home Assistant integriert. Bestehende HACS-Installationen werden automatisch migriert.

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

Der Koordinator fragt die API standardmäßig alle 5 Minuten ab (in den Integrationsoptionen einstellbar, mindestens 5 Minuten). Wenn sich die Werte nicht mehr aktualisieren:

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
[marketplace]: https://www.home-assistant.io/integrations/marketplace/#custom-repositories
[marketplacebadge]: https://img.shields.io/badge/Marketplace-Custom-orange.svg?style=for-the-badge
[license-shield]: https://img.shields.io/github/license/acesyde/hassio_mylight_integration.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-Pierre%20Emmanuel%20Mercier%20%40acesyde-blue.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/acesyde/hassio_mylight_integration.svg?style=for-the-badge
[releases]: https://github.com/acesyde/hassio_mylight_integration/releases
