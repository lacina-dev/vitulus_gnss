# vitulus_gnss

GNSS package for the **Vitulus** autonomous lawn-mower robot
([lacina-dev/vitulus](https://github.com/lacina-dev/vitulus)). It brings up two
u-blox **ZED-F9P** receivers (ArduSimple boards) and turns their output into the
robot's position and heading:

- **positioning rover** — RTK rover on `/dev/gnss`, 5 Hz, corrected by a fixed
  base station over RTCM → NavSatFix.
- **heading rover** — moving-base rover on `/dev/gnss_heading`, 5 Hz → GNSS
  heading (dual-antenna).
- a **fixed RTK base** (off-robot) broadcasts RTCM corrections to both.

Both receivers run at **5 Hz** — see the audit for why (moving base needs a
matching base/rover rate, and the heading board only reaches 5 Hz once the base
sends a slimmed **MSM4** stream).

---

## Package layout

| path | what it is |
|---|---|
| `launch/vitulus_ardusimple_gnss.launch` | starts the positioning rover (`ublox_gps` + `config/ardusimple_gnss.yaml`) |
| `launch/vitulus_ardusimple_heading.launch` | starts the heading rover |
| `nodes/gnss_status` | read-only status of both receivers for the UI → `/gnss_status` (JSON, 1 Hz): fix, satellites, RTCM corrections, warm-up time to RTK, likely reason when not RTK; started by the positioning launch |
| `launch/mapviz.launch` | optional mapviz + origin init for visualisation |
| `config/ardusimple_gnss.yaml` | **driver** params for the positioning board (device, baud, rate) |
| `config/ardusimple_heading.yaml` | driver params for the heading board |
| `config/navsat.yaml` | `navsat_transform` params (declination, yaw offset, UTM broadcast) |
| `config/base_station.yaml.example` | **template** for your base station position — copy & fill in |
| `config/README.md` | how to set the base position + module roles |
| `scripts/load_base_station.py` | reads your base position, prints the UBX values to flash |
| `f9p_config_dump_20260802.json` | full VALGET dump of both **rover** boards — reference/audit |
| `base_config_dump_20260802.json` | VALGET dump of the **base** board — reference/audit (coordinates scrubbed) |
| `F9P_CONFIG_AUDIT_2026-08-02.md` | audit of every relevant CFG key and the tuning applied |

The JSON dumps are a **reference snapshot**, not something that gets applied
automatically — see *Board configuration* below.

---

## Requirements

- **ROS Noetic** (Ubuntu 20.04).
- The **`ublox_gps`** driver: `sudo apt install ros-noetic-ublox` (provides
  `ublox_gps`). `navsat_transform` from `robot_localization` if you use
  `config/navsat.yaml`.
- Hardware: two ArduSimple ZED-F9P boards on the robot (positioning + heading)
  and a third ZED-F9P as a fixed base broadcasting RTCM. The heading setup is
  dual-antenna (moving base + rover).
- **Serial symlinks**: the launch files expect `/dev/gnss` (positioning) and
  `/dev/gnss_heading` (heading). Create udev rules mapping your boards'
  USB serials to those names, or edit `device:` in the two config yamls.

---

## Bringing it up

```bash
# positioning board → /gnss/fix (sensor_msgs/NavSatFix) and related topics
roslaunch vitulus_gnss vitulus_ardusimple_gnss.launch

# heading board → GNSS heading
roslaunch vitulus_gnss vitulus_ardusimple_heading.launch
```

Both nodes `respawn`. Outputs are the standard `ublox_gps` topics (NavSatFix on
`/gnss/fix`, plus `navpvt`, `navrelposned` for heading, etc.). Feed `/gnss/fix`
into `navsat_transform` with `config/navsat.yaml` to get a UTM transform.

---

## Board configuration (important)

**The ROS driver does not configure the receivers.** Both config yamls set
`config_on_startup: false`, so `ublox_gps` only opens the serial link at the
given baud/rate and reads — it does **not** push any CFG to the board. The F9P
settings (dynamic model, constellations, message output, base fixed position,
RTCM, etc.) are **flashed once** onto each board and persist in its flash.

To reproduce this setup on your own boards:

1. Read `F9P_CONFIG_AUDIT_2026-08-02.md`. It documents every non-default CFG
   key that matters (dynamic model → *pedestrian*/robotic-mower, SBAS/QZSS off,
   `MINCNO`/`MINELEV` raised, 5 Hz on both boards, base RTCM
   1005 + MSM4 1074/1084/1094/1124 + 1230) and why.
2. The `*_config_dump_*.json` files are full **UBX CFG-VALGET** dumps (RAM
   layer) of the actual boards — use them as the authoritative key/value
   reference.
3. Apply the settings to **your** boards with **u-center** (Configuration View
   → Generation 9) or `ubxtool` over serial, and save to the **Flash** layer so
   they survive reboot. Firmware here: rovers **HPG 1.32**, base **HPG 1.30**.

> There is **no auto-apply script** in this package — configuration is a manual
> u-center/ubxtool step, done once per board. The dumps and audit are the
> reference for what to set.

---

## Base station position — set your own

The base's surveyed position is **never distributed** (it's a real-world
location). You must provide your own:

```bash
cp config/base_station.yaml.example config/base_station.local.yaml
# edit base_station.local.yaml — survey-in for a fresh base, or enter a known ARP
python3 scripts/load_base_station.py     # prints the UBX CFG-TMODE values to flash
```

`base_station.local.yaml` is git-ignored and stays on your machine. Full details
and the survey-in vs. known-ARP procedures are in **[config/README.md](config/README.md)**.
The committed base dump has its coordinate fields zeroed.

---

## Status & disclaimer

Personal robot project. These configs are a **working reference for these
specific boards and firmware** (rover FW 1.32, base FW 1.30) in a Central-European
back-garden environment — treat them as a starting point and adapt to your
hardware, firmware and site. Parameters and layout change without notice.

**License:** the `LICENSE` file is MIT; `package.xml` currently declares Apache 2.0
— they disagree and should be reconciled (treat MIT as intent per the LICENSE
file until fixed).
