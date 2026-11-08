# MyLight Systems

🌐 [English](README.en.md) | **Français** | [Português](README.pt.md) | [Deutsch](README.de.md) | [Español](README.es.md)

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

[![marketplace][marketplacebadge]][marketplace]
![Project Maintenance][maintenance-shield]

_Intégration pour se connecter à [MyLight Systems][mylight_systems]._

> [!Warning]
>
> Cette intégration ne supporte actuellement que l'espace client **MyHome**. Pour le support **MyLight150**, une extension dédiée est disponible sur [Racailloux/mylight150_ha](https://github.com/Racailloux/mylight150_ha).

**Cette intégration configure les plateformes suivantes.**

## Entités fournies

### Capteurs

| ID d'entité                                     | Description                                              | Unité | Classe d'état      |
| ----------------------------------------------- | -------------------------------------------------------- | ----- | ------------------ |
| `sensor.total_solar_production`                 | Énergie cumulée produite par les panneaux solaires       | Wh    | `total_increasing` |
| `sensor.total_grid_consumption`                 | Énergie soutirée du réseau (avec batterie virtuelle)     | Wh    | `total_increasing` |
| `sensor.total_grid_without_battery_consumption` | Énergie soutirée du réseau (sans batterie virtuelle)     | Wh    | `total_increasing` |
| `sensor.total_autonomy_rate`                    | % de consommation couverte par le solaire + batterie     | %     | `measurement`      |
| `sensor.total_self_conso`                       | % de la production solaire consommée localement          | %     | `measurement`      |
| `sensor.total_msb_charge`                       | Énergie cumulée chargée dans la Smart Battery            | Wh    | `total_increasing` |
| `sensor.total_msb_discharge`                    | Énergie cumulée déchargée de la Smart Battery            | Wh    | `total_increasing` |
| `sensor.total_green_energy`                     | Énergie solaire consommée directement par votre domicile | Wh    | `total_increasing` |
| `sensor.battery_state`                          | Énergie actuellement stockée dans la Smart Battery       | kWh   | `measurement`      |
| `sensor.grid_returned_energy`                   | Énergie solaire réinjectée sur le réseau                 | Wh    | `total_increasing` |
| `sensor.grid_power`                             | Puissance réseau instantanée (positive : soutirage, négative : injection) | W | `measurement` |
| `sensor.grid_import_power`                      | Puissance soutirée du réseau | W | `measurement` |
| `sensor.grid_export_power`                      | Puissance injectée sur le réseau | W | `measurement` |
| `sensor.msb_discharge_power`                   | Puissance couverte par la batterie virtuelle | W | `measurement` |
| `sensor.grid_billed_power`                     | Puissance soutirée facturée (batterie virtuelle vide) | W | `measurement` |

> `grid_power`, `grid_import_power`, `grid_export_power` : Disponibles uniquement si un compteur réseau unique est détecté. MyLight fournit une moyenne sur 5 minutes : gardez l'intervalle de mise à jour par défaut de 5 minutes, sinon des mesures sont sautées.
>
> `msb_discharge_power`, `grid_billed_power` : Disponibles uniquement si une batterie virtuelle est détectée. Moyenne sur l'intervalle de mise à jour (gardez l'intervalle par défaut de 5 minutes, celui des mesures MyLight : au-delà, la courbe est lissée), calculée à partir des compteurs `total_msb_discharge` et `total_grid_without_battery_consumption` : à utiliser comme puissance de décharge (batterie) et de soutirage (réseau) dans le tableau de bord Énergie.

### Interrupteurs

| ID d'entité           | Description                                        | Remarques                                     |
| --------------------- | -------------------------------------------------- | --------------------------------------------- |
| `switch.master_relay` | Contrôle le relais principal de votre installation | Disponible uniquement si un relais est couplé |

## Installation

## Marketplace Home Assistant (2026.11+)

1. Dans Home Assistant, allez dans **Paramètres → Marketplace**.
2. Choisissez **Add from link**, collez `https://github.com/acesyde/hassio_mylight_integration` et connectez votre compte GitHub si demandé.
3. Installez **MyLight Systems**, puis redémarrez Home Assistant.

Ou cliquez sur ce bouton :

[![Ouvrez votre instance Home Assistant et ouvrez un dépôt dans le Home Assistant Marketplace.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=acesyde&repository=hassio_mylight_integration&category=integration)

> Depuis 2026.11, HACS est intégré à Home Assistant sous le nom de Marketplace. Les installations existantes via HACS sont migrées automatiquement.

## Manuel

1. Ouvrez le répertoire de votre configuration HA (là où se trouve `configuration.yaml`).
2. Si vous n'avez pas de répertoire `custom_components`, créez-le.
3. Dans `custom_components`, créez un nouveau dossier appelé `mylight_systems`.
4. Téléchargez _tous_ les fichiers du répertoire `custom_components/mylight_systems/` de ce dépôt.
5. Placez les fichiers téléchargés dans le nouveau dossier créé.
6. Redémarrez Home Assistant.
7. Dans l'interface HA, allez dans « Configuration » → « Intégrations », cliquez sur « + » et recherchez « MyLight Systems ».

## La configuration se fait via l'interface

## Architecture

Voir [ARCHITECTURE.md](ARCHITECTURE.md) pour le schéma des composants et le flux de données.

## Dépannage

### « Le relais principal est absent »

L'entité `switch.master_relay` n'est créée que si un relais (`sw`) est couplé à votre installation. Sans relais, cette entité n'apparaîtra pas.

### « Les valeurs des capteurs sont figées / ne se mettent pas à jour »

Le coordinateur interroge l'API toutes les 5 minutes par défaut (réglable dans les options de l'intégration, 5 minutes minimum). Si les valeurs ne se mettent plus à jour :

1. Allez dans **Paramètres → Appareils et services → MyLight Systems** et vérifiez s'il y a une bannière d'erreur.
2. Activez les logs de débogage et consultez les journaux Home Assistant :

```yaml
# configuration.yaml
logger:
  default: warning
  logs:
    custom_components.mylight_systems: debug
```

3. Recherchez les entrées `CommunicationError` ou `UpdateFailed` — elles indiquent un problème réseau ou un changement d'API.

### « Échec d'authentification » après un changement de mot de passe

Si vous avez modifié votre mot de passe MyLight en dehors de l'intégration, une erreur d'authentification apparaîtra. Allez dans **Paramètres → Appareils et services → MyLight Systems** et utilisez l'option **Ré-authentifier** pour saisir vos nouveaux identifiants.

## Les contributions sont les bienvenues !

Si vous souhaitez contribuer, veuillez lire les [directives de contribution](CONTRIBUTING.md).

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
