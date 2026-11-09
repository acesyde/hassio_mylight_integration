# MyLight Systems

🌐 [English](README.en.md) | [Français](README.md) | **Português** | [Deutsch](README.de.md) | [Español](README.es.md)

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

[![marketplace][marketplacebadge]][marketplace]
![Project Maintenance][maintenance-shield]

_Integração para conectar ao [MyLight Systems][mylight_systems]._

> [!Warning]
>
> Esta integração suporta atualmente apenas a área de cliente **MyHome**. Para suporte ao **MyLight150**, uma extensão dedicada está disponível em [Racailloux/mylight150_ha](https://github.com/Racailloux/mylight150_ha).

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
| `sensor.grid_power`                             | Potência instantânea da rede (positiva: importação, negativa: exportação) | W | `measurement` |
| `sensor.grid_import_power`                      | Potência importada da rede (instantânea) | W | `measurement` |
| `sensor.grid_export_power`                      | Potência exportada para a rede (instantânea) | W | `measurement` |
| `sensor.solar_power`                            | Potência de produção solar | W | `measurement` |
| `sensor.consumption_power`                      | Potência consumida pela habitação | W | `measurement` |
| `sensor.grid_returned_power`                    | Potência devolvida à rede (sem bateria virtual) | W | `measurement` |
| `sensor.grid_net_power`                         | Potência líquida da rede (positiva: importação, negativa: exportação). Com bateria virtual: «Potência líquida da rede faturada» | W | `measurement` |
| `sensor.msb_charge_power`                       | Potência de carga da bateria virtual | W | `measurement` |
| `sensor.msb_discharge_power`                    | Potência coberta pela bateria virtual | W | `measurement` |
| `sensor.msb_net_power`                          | Potência líquida da bateria virtual (positiva: descarga, negativa: carga) | W | `measurement` |
| `sensor.grid_billed_power`                      | Potência importada faturada (bateria virtual vazia) | W | `measurement` |

> `grid_power`, `grid_import_power`, `grid_export_power`: só criados se um único contador de rede for detetado. Leitura pontual do contador em cada atualização: pode diferir da média do intervalo. Para o painel de Energia, prefira as potências calculadas abaixo.
>
> `solar_power`, `consumption_power`, `grid_net_power`, `grid_returned_power`: médias no intervalo de atualização, calculadas a partir dos contadores de energia da MyLight, por isso coincidem ao Wh com os totais em kWh. Mantenha o intervalo padrão de 5 minutos, o passo de medição da MyLight (intervalos maiores suavizam a curva). Sem valor durante o primeiro intervalo após um arranque (são necessárias duas leituras). Com bateria virtual, `grid_net_power` só conta a importação faturada.
>
> `msb_charge_power`, `msb_discharge_power`, `msb_net_power`, `grid_billed_power`: mesmo cálculo, disponíveis apenas quando uma bateria virtual é detetada. `grid_returned_power` não é então criado: a MyLight conta cada Wh exportado como carga, o retorno vale sempre 0. Pela mesma razão, `grid_net_power` (renomeado «Potência líquida da rede faturada») e `grid_billed_power` têm o mesmo valor: o primeiro serve para o modo de um único sensor com sinal do painel de Energia, o segundo para o modo de dois sensores.

### Interruptores

| ID da entidade        | Descrição                                   | Notas                                             |
| --------------------- | ------------------------------------------- | ------------------------------------------------- |
| `switch.master_relay` | Controla o relé principal da sua instalação | Disponível apenas quando um relé está emparelhado |

## Configurar o painel de Energia

Em **Definições → Painéis → Energia**, indique para cada fonte os seus contadores de energia e, para a potência, **um único sensor com sinal** (modo padrão: positivo quando a energia entra na habitação, negativo quando sai). O Home Assistant deixa de precisar de criar os seus próprios sensores de potência líquida, e o gráfico «Fontes de potência» coincide exatamente com os totais em kWh.

Os IDs de entidade reais incluem o nome do seu dispositivo: procure os sensores pelo nome (entre parênteses abaixo, em português).

| Fonte | Energia | Potência (um único sensor) |
|---|---|---|
| Rede | Consumo: `total_grid_without_battery_consumption` com bateria virtual, senão `total_grid_consumption`. Retorno: `grid_returned_energy` | `grid_net_power` (Potência líquida da rede, ou Potência líquida da rede faturada com bateria virtual) |
| Solar | `total_solar_production` | `solar_power` (Potência solar) |
| Bateria (apenas bateria virtual) | Descarga: `total_msb_discharge`. Carga: `total_msb_charge` | `msb_net_power` (Potência líquida da bateria virtual) |

1. **Rede**: edite (ou adicione) a fonte de rede, escolha os contadores acima e, na parte de potência, o modo de um único sensor com `grid_net_power`.
2. **Solar**: edite (ou adicione) a produção solar com `total_solar_production` e a potência `solar_power`.
3. **Bateria** (se tiver bateria virtual): adicione um armazenamento com `total_msb_discharge` (energia que sai da bateria) e `total_msb_charge` (energia que entra na bateria), e a potência `msb_net_power` no modo de um único sensor.

> **Porquê não `total_grid_consumption` nem `grid_power` com bateria virtual?** A MyLight conta a energia exportada como carga da bateria virtual e a importação coberta pelo seu crédito como descarga: só a parte faturada é rede. Os contadores acima seguem essa lógica; `grid_power` mede o fluxo físico e contaria a bateria como rede.
>
> `consumption_power` não é necessário aqui: o Home Assistant calcula o consumo a partir das fontes. Serve para o mostrar noutros sítios (cartões, automatizações).

## Instalação

## Marketplace do Home Assistant (2026.11+)

1. No Home Assistant, vá a **Definições → Marketplace**.
2. Escolha **Add from link**, cole `https://github.com/acesyde/hassio_mylight_integration` e ligue a sua conta GitHub se for pedido.
3. Instale **MyLight Systems** e reinicie o Home Assistant.

Ou clique neste botão:

[![Abra a sua instância do Home Assistant e abra um repositório no Home Assistant Marketplace.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=acesyde&repository=hassio_mylight_integration&category=integration)

> Desde a 2026.11, o HACS está integrado no Home Assistant como Marketplace. As instalações existentes via HACS são migradas automaticamente.

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

O coordenador consulta a API a cada 5 minutos por padrão (ajustável nas opções da integração, mínimo 5 minutos). Se os valores pararem de atualizar:

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
[marketplace]: https://www.home-assistant.io/integrations/marketplace/#custom-repositories
[marketplacebadge]: https://img.shields.io/badge/Marketplace-Custom-orange.svg?style=for-the-badge
[license-shield]: https://img.shields.io/github/license/acesyde/hassio_mylight_integration.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-Pierre%20Emmanuel%20Mercier%20%40acesyde-blue.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/acesyde/hassio_mylight_integration.svg?style=for-the-badge
[releases]: https://github.com/acesyde/hassio_mylight_integration/releases
