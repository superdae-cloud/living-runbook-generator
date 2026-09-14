# OSPF + MTU + CORE-Router

*Auto-generated from 2 incident(s), 2024-05-19 → 2024-07-11. Do not hand-edit above the manual notes section — it will be overwritten next time this pipeline runs.*

## Symptom signature
- ospf
- mtu
- ospf mtu
- router ospf
- neighbor
- ospf neighbor
- Seen on: AGG3-NYC, CORE1-NYC

## Frequency
- 2 incident(s) matched this signature
- First seen: 2024-05-19
- Last seen: 2024-07-11

## Diagnostic steps seen across these incidents
- `show ip ospf neighbor` shows repeated state resets
- `show ip ospf interface` shows MTU of 1500 on this side, 9000 on the neighbor side
- Packet capture showed DBD packets being dropped silently
- `show ip ospf neighbor` shows the adjacency resetting every couple of minutes
- `show interfaces` revealed the replacement card came up with jumbo MTU (9000) by default while the peer stayed at 1500
- Packet capture confirmed DBD packets silently dropped, matching a pattern seen before

## Likely root cause(s)
- MTU mismatch between the two core router interfaces (jumbo frames enabled on one side only) caused DBD packet exchange to fail, preventing the neighbor from reaching Full state.
- MTU mismatch introduced by a hardware replacement — the new line card's default MTU didn't match the OSPF peer, breaking DBD exchange.

## Resolution steps that worked
- Set both interfaces to matching MTU (1500)
- Confirmed OSPF neighbor reached Full state within 30 seconds
- Set matching MTU (1500) on both sides of the link
- OSPF adjacency reached Full immediately
- Filed a note to add MTU verification to the post-hardware-replacement checklist

## Source incidents
- `INC-1023` (2024-05-19, CORE1-NYC) — `2024-05-19-inc-1023.md`
- `INC-1030` (2024-07-11, AGG3-NYC) — `2024-07-11-inc-1030.md`

## Manual notes
*Anything you write between the two markers below survives the next auto-regeneration.*

<!-- MANUAL NOTES START -->
(add engineer notes here)
<!-- MANUAL NOTES END -->
