gds read /foss/designs/build/power-ring/power_ring.gds
load power_ring
select top cell
# Bond labels are physical RC measurement points, not extra logical LVS ports.
foreach {pin idx} {AVDD 1 AVSS 2} {
 catch {port $pin make $idx}
 port $pin index $idx
}
drc check
drc catchup
set drc_count [drc list count total]
puts "RING_DRC_COUNT=$drc_count"
if {$drc_count > 0} {puts "RING_DRC_DETAILS=[drc listall why]"}
quit -noprompt
