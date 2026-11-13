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
| `sensor.grid_import_power`                      | Puissance soutirée du réseau (instantanée) | W | `measurement` |
| `sensor.grid_export_power`                      | Puissance injectée sur le réseau (instantanée) | W | `measurement` |
| `sensor.water_heater_energy`                    | Énergie cumulée du chauffe-eau | Wh | `total_increasing` |
| `sensor.water_heater_power`                     | Puissance du chauffe-eau (instantanée) | W | `measurement` |
| `sensor.solar_power`                            | Puissance solaire produite | W | `measurement` |
| `sensor.consumption_power`                      | Puissance consommée par le logement | W | `measurement` |
| `sensor.grid_returned_power`                    | Puissance réinjectée sur le réseau (sans batterie virtuelle) | W | `measurement` |
| `sensor.grid_net_power`                         | Puissance nette réseau (positive : soutirage, négative : réinjection). Avec batterie virtuelle : « Puissance nette réseau facturée » | W | `measurement` |
| `sensor.msb_charge_power`                       | Puissance de charge de la batterie virtuelle | W | `measurement` |
| `sensor.msb_discharge_power`                    | Puissance couverte par la batterie virtuelle | W | `measurement` |
| `sensor.msb_net_power`                          | Puissance nette de la batterie virtuelle (positive : décharge, négative : charge) | W | `measurement` |
| `sensor.grid_billed_power`                      | Puissance soutirée facturée (batterie virtuelle vide) | W | `measurement` |

> `grid_power`, `grid_import_power`, `grid_export_power` : disponibles uniquement si un compteur réseau unique est détecté. Valeur ponctuelle lue sur le compteur à chaque mise à jour : elle peut s'écarter de la moyenne de l'intervalle. Pour la vue Énergie, préférez les puissances calculées ci-dessous.
>
> `water_heater_energy`, `water_heater_power` : disponibles uniquement si un compteur chauffe-eau unique est détecté (appareil de type « Chauffe eau » : compteur `gmd` seul, identifiant en `_RS_01`, ou sous-compteur `cmp` rattaché à un compteur composite). L'énergie vient de `/api/measures/total` du compteur, la puissance (valeur ponctuelle) de `/api/states`.
>
> `solar_power`, `consumption_power`, `grid_net_power`, `grid_returned_power` : moyennes sur l'intervalle de mise à jour, calculées à partir des compteurs d'énergie MyLight, donc cohérentes au Wh près avec les totaux en kWh. Gardez l'intervalle par défaut de 5 minutes, celui des mesures MyLight (au-delà, la courbe est lissée). Pas de valeur pendant le premier intervalle après un démarrage (il faut deux relevés). Avec une batterie virtuelle, `grid_net_power` ne compte que le soutirage facturé.
>
> `msb_charge_power`, `msb_discharge_power`, `msb_net_power`, `grid_billed_power` : même calcul, disponibles uniquement si une batterie virtuelle est détectée. `grid_returned_power` n'est alors pas créé : MyLight compte toute l'énergie injectée comme une charge, la réinjection vaut toujours 0. Pour la même raison, `grid_net_power` (renommé « Puissance nette réseau facturée ») et `grid_billed_power` ont la même valeur : le premier sert au mode à un seul capteur signé de la vue Énergie, le second au mode à deux capteurs.

### Interrupteurs

| ID d'entité           | Description                                        | Remarques                                     |
| --------------------- | -------------------------------------------------- | --------------------------------------------- |
| `switch.master_relay` | Contrôle le relais principal de votre installation | Disponible uniquement si un relais est couplé |

## Configurer le tableau de bord Énergie

Dans **Paramètres → Tableaux de bord → Énergie**, renseignez pour chaque source ses compteurs d'énergie, puis, pour la puissance, **un seul capteur signé** (mode standard : positif quand l'énergie entre dans le logement, négatif quand elle en sort). Home Assistant n'a alors pas besoin de créer ses propres capteurs de puissance nette, et le graphique « Sources de puissance » correspond exactement aux totaux en kWh.

Les ID d'entité réels contiennent le nom de votre appareil : cherchez les capteurs par leur nom affiché, indiqué entre guillemets ci-dessous (en français), sans rien ajouter.

| Source | Énergie | Puissance (un seul capteur) |
|---|---|---|
| Réseau, avec batterie virtuelle | Consommation : `total_grid_without_battery_consumption`. Retour : `grid_returned_energy` | `grid_net_power` : « Puissance nette réseau facturée » |
| Réseau, sans batterie virtuelle | Consommation : `total_grid_consumption`. Retour : `grid_returned_energy` | `grid_net_power` : « Puissance nette réseau » |
| Solaire | `total_solar_production` | `solar_power` : « Puissance solaire » |
| Batterie (batterie virtuelle uniquement) | Décharge : `total_msb_discharge`. Charge : `total_msb_charge` | `msb_net_power` : « Puissance nette de la batterie virtuelle » |

1. **Réseau** : modifiez (ou ajoutez) la source réseau, choisissez les compteurs ci-dessus, puis dans la partie puissance le mode à un seul capteur avec `grid_net_power`.
2. **Solaire** : modifiez (ou ajoutez) la production solaire avec `total_solar_production` et la puissance `solar_power`.
3. **Batterie** (si vous avez une batterie virtuelle) : ajoutez un système de stockage avec `total_msb_discharge` (énergie sortant de la batterie) et `total_msb_charge` (énergie entrant dans la batterie), puis la puissance `msb_net_power` en mode à un seul capteur.

> **Pourquoi pas `total_grid_consumption` ni `grid_power` avec une batterie virtuelle ?** MyLight compte l'énergie injectée comme une charge de la batterie virtuelle et le soutirage couvert par votre crédit comme une décharge : seule la part facturée est du réseau. Les compteurs ci-dessus suivent cette logique ; `grid_power` mesure le flux physique et classerait la batterie en réseau.
>
> `consumption_power` n'est pas à renseigner : Home Assistant calcule la consommation à partir des sources. Il sert à l'afficher ailleurs (cartes, automatisations).

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
