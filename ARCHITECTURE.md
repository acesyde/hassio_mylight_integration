# Architecture

The integration follows the standard Home Assistant coordinator pattern:

```mermaid
flowchart TD
    CF["Config Flow\nconfig_flow.py\n(credentials + device discovery)"]
    INIT["Entry Setup\n__init__.py\n(async_setup_entry)"]
    COORD["Coordinator\ncoordinator.py\n(polls every 15 min)"]
    CLIENT["API Client\napi/client.py\n(aiohttp)"]
    API["MyLight Systems\nCloud API"]
    SENSOR["Sensor Entities\nsensor.py\n(10 sensors)"]
    SWITCH["Switch Entity\nswitch.py\n(master relay)"]

    CF -->|"creates"| INIT
    INIT -->|"creates"| COORD
    INIT -->|"creates"| CLIENT
    COORD -->|"uses"| CLIENT
    CLIENT -->|"HTTPS"| API
    COORD -->|"pushes data"| SENSOR
    COORD -->|"pushes data"| SWITCH
```

**Data flow per update cycle:**
1. Coordinator calls `async_get_measures_grouping` (daily energy values) and `async_get_measures_total` (rates) sequentially
2. Optionally fetches battery state and relay state if devices are paired
3. Aggregated data is pushed to all sensor and switch entities
