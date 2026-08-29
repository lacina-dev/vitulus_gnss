# vitulus_gnss configuration

Two u-blox ZED-F9P (ArduSimple) boards plus a fixed RTK base.

| board | role | notes |
|---|---|---|
| positioning rover (`/dev/gnss`) | RTK rover (DGNSSMODE=3), 5 Hz | consumes base RTCM, feeds navsat |
| heading rover (`/dev/gnss_heading`) | moving-base rover, 5 Hz | GNSS heading; 5 Hz needs the slim MSM4 stream (was 1 Hz) |
| RTK base (off-robot) | TMODE FIXED, 1 Hz | broadcasts RTCM 1005 + MSM4 1074/1084/1094/1124 + 1230 |

Both rovers use `config_on_startup: false` — the driver only opens the link; the
CFG is **flashed once** to each board (UBX CFG-VALSET). See
`F9P_CONFIG_AUDIT_2026-08-02.md` for the full key audit and the 5 Hz rationale.

## Base station position — you must set your own

The base's surveyed position is **not** distributed. Provide yours:

```bash
cp config/base_station.yaml.example config/base_station.local.yaml
# edit base_station.local.yaml (survey-in for a fresh base, or a known ARP)
python3 scripts/load_base_station.py     # prints the UBX CFG-TMODE values to flash
```

`base_station.local.yaml` is git-ignored and never leaves your machine. The
committed dumps (`base_config_dump_*.json`) have the coordinate fields zeroed
(`_SCRUBBED`); regenerate a full local dump from your own board if you need one.
