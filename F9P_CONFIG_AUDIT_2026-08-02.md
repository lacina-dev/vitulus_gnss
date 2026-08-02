# Audit konfigurace obou ZED-F9P — 2026-08-02
Dump: f9p_config_dump_20260802.json (VALGET všech 1475 klíčů, RAM vs. factory default;
čteno za běhu přes SIGSTOP driveru, NIC neměněno). Oba přijímače: FW **HPG 1.32**.

## Stav: konfigurace je funkční, ale je to "u-center 2021" — řada výchozích
hodnot nebyla nikdy laděna pro pomalou sekačku a multipath prostředí.

### Nálezy (seřazeno podle důležitosti)

1. **DYNMODEL = 0 (portable) — NIKDY nenastaven.** Generický model pro "cokoliv".
   Pro sekačku (0,3-0,75 m/s, žádné skoky) je na FW 1.32 vhodnější
   **pedestrian (3)** — nízká dynamika, těsnější filtr = klidnější pozice v
   multipathu. (Po upgrade FW na 1.50+ existuje přímo model **robotic lawn
   mower (11)**.) Platí pro OBA přijímače. Největší kandidát na zlepšení zdarma.

2. **SBAS zapnutý (default)** — s RTK je SBAS k ničemu (korekce máme z NTRIP),
   jen žere tracking kanály. Vypnout = víc kanálů pro GPS/GAL/BDS = lepší
   viditelnost na dvoře. Totéž QZSS (v ČR prakticky neviditelné, SLAS je Japonsko).

3. **MINCNO = 6 dBHz (default) — extrémně benevolentní.** Přijímač počítá i se
   signály, které jsou skoro jistě odrazy. Zvednout infil minCNO na ~20-25 dBHz
   = receiver-side obrana proti multipathu na dvoře (přesně to, co doporučila
   rešerše — jen na straně přijímače místo softwaru). MINELEV = 10° default;
   zvednout na ~15° pomůže proti nízkým odraženým satelitům (trade-off: méně
   satelitů — otestovat).

4. **Telemetrie, kterou chceme, není zapnutá:** NAV-SIG (per-signál C/N0),
   MON-RF (jamming/interference indikátory), NAV-DOP — vše na 0. Přitom je to
   přesně vstup pro C/N0 monitoring z rešerše a dá se zapnout POUZE konfigurací,
   bez FW upgradu. ITFM (interference monitor) také vypnutý — zapnout.

5. **RTCM pro moving-base teče přes hostitelský port.** Poziční přijímač vysílá
   RTCM 1077/1087/1097/1230/4072 na UART1 (= /dev/gnss, 460800), odkud to
   fyzicky odbočuje do heading UART2 (460800, INPROT jen RTCM). Funguje to, ale
   RTCM rámce v host streamu jsou nejspíš příčinou občasných ERROR "U-Blox
   message exceeds maximum payload length" v ROS driveru (viděno v runtime
   auditu 1.8.). Čistší by bylo vysílat moving-base RTCM z UART2 pozičního
   přijímače (vyžaduje přepojení drátu) — kosmetika, funguje to i takhle.

6. **NAVHPG_DGNSSMODE = 3 (RTK fixed)** — správně pro 1.32; konzervativní
   RTK_CAR mód na tomhle FW neexistuje (potvrzeno: potřebuje 1.50+).

7. Drobné: WKNROLLOVER 2188 (stale, kosmetika); INFMSG 0x0f na všech portech
   (zbytečně upovídané); NAV-SAT každých 20 epoch (4 s) OK; 5 Hz rate OK;
   TMODE vypnutý správně (rover) — diagnostická hláška "TMODE3: Not configured"
   je artefakt ROS driveru, ne chyba konfigurace.
8. **UBX-NAV-PL (Protection Level)**: dostupnost na HPG 1.32 nejistá — klíč
   MSGOUT pro NAV-PL v dumpu nebyl nalezen → téměř jistě až od 1.50+. Další
   argument pro FW upgrade.

### Doporučený balíček změn (AŽ ŘEKNEŠ — nic nezměněno)
Bez FW upgradu, čistá konfigurace, vratné: DYNMODEL→pedestrian, SBAS+QZSS off,
MINCNO→20, MINELEV→15 (A/B otestovat na dvoře), zapnout NAV-SIG+MON-RF+NAV-DOP
+ITFM a parsovat do telemetrie. S FW upgradem na 1.51 navíc: lawn-mower dynmodel,
RTK_CAR, NAV-PL protection level.

---
# STAV ZMĚN 2026-08-02 večer (vlna 1 aplikována, persist Flash)
- OBA: DYNMODEL=3 (pedestrian), SBAS+QZSS OFF, MINCNO=20, MINELEV=15, ITFM=1,
  NAV-SIG/MON-RF/NAV-DOP telemetrie zapnuta. Zálohy: f9p_config_dump_20260802.json
  + ardusimple_*.yaml.bak_10hz_20260802.
- POZICE: 10 Hz ŽIVĚ OVĚŘENO (/gnss/fix ~10.0 Hz). MB RTCM output zředěn na 5 Hz
  (divisor 2) proti saturaci UART1.
- HEADING: **NÁLEZ — naviguje na 1 Hz a dělal to už PŘED změnami** (ranní diag
  "Frequency too low"; wire-measure: všechny NAV zprávy 1 Hz, RXM-RTCM 25 Hz OK).
  RATE_MEAS=200 ACKnut, ale MB rover nav rate zůstává 1 Hz — pravděpodobně MB
  omezení FW/chybějící klíč; ArduSimple 5/10Hz MB configy to řeší → NEXT: stáhnout
  jejich config file (post "new-zed-f9p-5hz-and-10hz-rover-and-moving-base-
  configuration-files"), diff proti dumpu, aplikovat chybějící klíč. Heading yaml
  vrácen na rate:5. Heading anchor v2 funguje i při 1 Hz (jen pomalejší okno).
- FLASH HPG 1.51: ODLOŽEN — bez ověřeného Linux flasheru + FW .bin (user může
  stáhnout z u-blox portálu; u-center cesta = přepojit desky do notebooku).
- BASE: listener na robotu :7002 čeká na socat z notebooku (TCP:192.168.0.1:7002
  /dev/ttyACM0,b115200,raw,echo=0) → pak dump+audit stejně jako rovery.

---
# BASE STATION AUDIT (2026-08-02 večer, dump přes TCP most z notebooku)
Dump: base_config_dump_20260802.json. ZED-F9P, FW HPG 1.30. NIC neměněno.

**Co je správně:** TMODE=FIXED (pevná surveyed pozice <YOUR_BASE_LAT>N <YOUR_BASE_LON>E <YOUR_BASE_HEIGHT>m — žádný survey-in při každém bootu ✓), DYNMODEL=stationary ✓, RTCM out:
1005 + MSM4 (1074 GPS / 1084 GLO / 1094 GAL) + **1230 GLONASS biasy ✓** (bez ní
by GLONASS ambiguity nešly fixnout), rate 1 Hz (standard pro base ✓), MSM4
místo MSM7 = úsporné ✓.

**Nálezy:**
1. **CHYBÍ RTCM 1124 (BeiDou MSM4)** — base BDS přijímá, ale korekce nevysílá
   → rovery nemohou BDS použít v RTK řešení = zbytečně méně satelitů. Přidání
   1124 = víc RTK satelitů zadarmo — největší přínos právě pro dvůr s omezeným
   výhledem na oblohu. DOPORUČUJI PŘIDAT (1 klíč, UART2+USB).
2. TMODE_FIXED_POS_ACC = 0.7 m — deklarovaná přesnost surveyed pozice base.
   Celá zahrada tak může být absolutně posunutá až o ~0.7 m (relativní cm
   přesnost to NEovlivňuje — vše je vůči stejné base). Pro sekání irelevantní;
   kdyby někdy vadilo (srovnání s katastrem/ortofoto), přesurveyovat base přes
   NTRIP od CZEPOS/jiného referenta.
3. Drobné jako u roverů: SBAS+QZSS zapnuté (vypnout), MINCNO=6/MINELEV=10
   (zvednout ~15° podle horizontu base), ITFM vypnutý (zapnout pro telemetrii).
4. FW HPG 1.30 — starší než rovery (1.32), pro funkci base OK, flash netřeba.

**UPDATE 2026-08-02 ~20:45: RTCM 1124 PŘIDÁNA na base** (UART2+USB, RAM+Flash,
ACK+readback ověřeno přes TCP most). Rovery od teď dostávají BeiDou korekce —
ověřit při příští RTK session (RXM-RTCM na roveru musí ukazovat 1124, více
satelitů v RTK FIXED). Ostatní base drobnosti (SBAS/QZSS off, minELEV, ITFM)
zůstávají NEaplikované — čekají na pokyn.

**FLASH POKUS 2026-08-02 večer — ODLOŽEN, HW v pořádku.** FW HPG 1.51 stažen a
MD5 ověřen (~/Downloads, kopie C:\fw151.bin ve wine prefixu). Flash tool
ubxfwupdate.exe (u-center 22.05, wine) zprovozněn vč. FTD2XX.dll (z Arduino
balíku) — ale wine 5.0 (Ubuntu 20.04) má ROZBITOU sériovou vrstvu: tool nezapíše
ani bajt (ověřeno PTY bridge logem), baud mapuje špatně. 3 cesty selhaly stejně
(přímý port, tichá linka, PTY most). Poziční přijímač vrácen resetem do flash
konfigurace, driver respawnut, 10 Hz OK. CESTY DÁL: (a) skutečné Windows
s u-center GUI — 10 min práce, nejjistější; (b) novější wine (8+) — vyžaduje
instalaci (sudo); (c) nechat na později — 1.51 přínosy (RTK_CAR, NAV-PL,
lawnmower model) nejsou blokující. COM mapping + fw151.bin zůstávají připravené.

---
# HEADING 1 Hz — VYŘEŠENO (2026-08-02 pozdě večer) — z 1 Hz na 5 Hz!
KOŘEN (Integration Manual §Moving base): MB rover latence korekcí musí být
< perioda−50 ms; při překročení se rover SÁM degraduje až na 1 Hz. Naše MB
korekce (MSM7 1077/1087/1097+1230+4072.0) jedou po UART1 tee SMÍCHANÉ s plnou
UBX telemetrií → latence nad limit → heading byl 1 Hz ODJAKŽIVA (ranní diag
"Frequency too low" to potvrzovala dávno před dnešními změnami).
FIX: MB stream zeštíhlen na MSM4 GPS+GAL (1074/1094/4072.0; GLONASS+1230 z MB
streamu pryč — POZOR: pozice RTK vs. base station dál používá VŠECHNY
konstelace přes NTRIP, tohle je jen heading baseline) + ořez UBX telemetrie
(POSECEF/CLOCK/SAT off, RXM-RTCM div 5) + reset headingu (degradace je sticky).
10/10 test SELHAL (latence <50 ms na tee nejde) → FINÁL 5/5 dle manuálu
(base+rover musí mít shodné raty). Persist Flash obě desky, yamly rate: 5.
ŽIVĚ: /gnss/fix 5.0 Hz, /gnss_heading/navheading 5.0 Hz. Pozice se vrátila
z 10 na 5 Hz — vědomý trade (heading 5× > pozice 2×). Budoucí cesta na 10/10:
fyzický drát position UART2 → heading UART2 (dedikovaná linka, kit ho nemá).
