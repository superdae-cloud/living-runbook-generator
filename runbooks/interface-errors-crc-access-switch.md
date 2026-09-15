# Interface-Errors + CRC + Access-Switch

*Auto-generated from 1 incident(s), 2024-08-04 → 2024-08-04. Do not hand-edit above the manual notes section — it will be overwritten next time this pipeline runs.*

## Symptom signature
- crc
- switch
- errors crc
- crc access
- errors
- access switch
- Seen on: ACC7-ATL

## Frequency
- 1 incident(s) matched this signature
- First seen: 2024-08-04
- Last seen: 2024-08-04

## Diagnostic steps seen across these incidents
- `show interfaces Gi0/12` shows steadily climbing CRC and input error counters
- Swapped patch cable — no change
- Swapped SFP with a known-good spare — error counters stopped climbing

## Root cause
- Failing SFP transceiver on ACC7-ATL Gi0/12 was introducing CRC errors under load.

## Resolution steps that worked
- Replaced the failing SFP
- Monitored interface for 24 hours — zero new CRC errors

## Source incidents
- `INC-1041` (2024-08-04, ACC7-ATL) — `2024-08-04-inc-1041.md`

## Manual notes
*Anything you write between the two markers below survives the next auto-regeneration.*

<!-- MANUAL NOTES START -->
(add engineer notes here)
<!-- MANUAL NOTES END -->
