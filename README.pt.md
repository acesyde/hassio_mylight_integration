# MyLight Systems

🌐 [English](README.md) | [Français](README.fr.md) | **Português** | [Deutsch](README.de.md) | [Español](README.es.md)

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

[![hacs][hacsbadge]][hacs]
![Project Maintenance][maintenance-shield]

_Integração para conectar ao [MyLight Systems][mylight_systems]._

> [!Warning]
>
> Esta integração suporta atualmente apenas a área de cliente **MyHome**. A área de cliente **MyLight150** ainda não é suportada.

**Esta integração irá configurar as seguintes plataformas.**

## Entidades fornecidas

### Sensores

| ID da entidade                                  | Descrição                                         | Unidade | Classe de estado   |
| ----------------------------------------------- | ------------------------------------------------- | ------- | ------------------ |
| `sensor.total_solar_production`                 | Energia acumulada produzida pelos painéis solares | Wh      | `total_increasing` |
| `sensor.total_grid_consumption`                 | Energia consumida da rede (com bateria virtual)   | Wh      | `total_increasing` |
| `sensor.total_grid_without_battery_consumption` | Energia consumida da rede (sem bateria virtual)   | Wh      | `total_increasing` |
| `sensor.total_autonomy_rate`                    | % do consumo coberto por solar + bateria          | %       | `measurement`      |
| `sensor.total_self_conso`                       | % da produção solar consumida localmente          | %       | `measurement`      |
| `sensor.total_msb_charge`                       | Energia acumulada carregada na Smart Battery      | Wh      | `total_increasing` |
| `sensor.total_msb_discharge`                    | Energia acumulada descarregada da Smart Battery   | Wh      | `total_increasing` |
| `sensor.total_green_energy`                     | Energia solar consumida diretamente pela sua casa | Wh      | `total_increasing` |
| `sensor.battery_state`                          | Energia atualmente armazenada na Smart Battery    | kWh     | `measurement`      |
| `sensor.grid_returned_energy`                   | Energia solar exportada para a rede               | Wh      | `total_increasing` |

### Interruptores

| ID da entidade        | Descrição                                   | Notas                                             |
| --------------------- | ------------------------------------------- | ------------------------------------------------- |
| `switch.master_relay` | Controla o relé principal da sua instalação | Disponível apenas quando um relé está emparelhado |

## Instalação

## Automática

[![Abra a sua instância do Home Assistant e abra um repositório no Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=acesyde&repository=hassio_mylight_integration&category=integration)

## Manual

1. Abra o diretório da sua configuração do HA (onde se encontra o `configuration.yaml`).
2. Se não tiver um diretório `custom_components`, crie-o.
3. Dentro de `custom_components`, crie uma nova pasta chamada `mylight_systems`.
4. Baixe _todos_ os arquivos do diretório `custom_components/mylight_systems/` deste repositório.
5. Coloque os arquivos baixados na nova pasta criada.
6. Reinicie o Home Assistant.
7. Na interface do HA, vá em "Configuração" → "Integrações", clique em "+" e pesquise por "MyLight Systems".

## A configuração é feita pela interface

## Arquitetura

Consulte [ARCHITECTURE.md](ARCHITECTURE.md) para o diagrama completo de componentes e o fluxo de dados.

## Solução de problemas

### "O interruptor de relé está ausente"

A entidade `switch.master_relay` só é criada quando um relé (`sw`) está emparelhado à sua instalação. Se não tiver um relé, esta entidade não aparecerá.

### "Os valores dos sensores estão parados / não atualizam"

O coordenador consulta a API a cada 15 minutos. Se os valores pararem de atualizar:

1. Abra **Configurações → Dispositivos e Serviços → MyLight Systems** e verifique se há um aviso de erro.
2. Ative o log de depuração e verifique os logs do Home Assistant:

```yaml
# configuration.yaml
logger:
  default: warning
  logs:
    custom_components.mylight_systems: debug
```

3. Procure por entradas `CommunicationError` ou `UpdateFailed` — indicam um problema de rede ou uma mudança na API.

### "Falha de autenticação" após alteração de senha

Se você alterou sua senha do MyLight externamente, a integração exibirá um erro de autenticação. Vá em **Configurações → Dispositivos e Serviços → MyLight Systems** e use a opção **Re-autenticar** para inserir suas novas credenciais.

## Contribuições são bem-vindas!

Se quiser contribuir, leia as [diretrizes de contribuição](CONTRIBUTING.md).

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
