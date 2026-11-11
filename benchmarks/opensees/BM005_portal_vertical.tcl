# BM005 — single-bay, single-storey 2D rigid portal frame; vertical nodal load.
# Units: kN, m. Linear elastic, first-order, Euler-Bernoulli beam-column elements.
# Run: OpenSees.exe BM005_portal_vertical.tcl
wipe
model BasicBuilder -ndm 2 -ndf 3

# Geometry (m): 6.0 m bay, 3.0 m storey; top beam split at midspan.
node 1 0.0 0.0  ;# BL
node 2 6.0 0.0  ;# BR
node 3 0.0 3.0  ;# TL
node 4 3.0 3.0  ;# TM
node 5 6.0 3.0  ;# TR

# Material/section: E=200 GPa, A=0.020 m2, Iz=8.0e-5 m4.
set E 200000000.0
set A 0.020
set Iz 0.000080
geomTransf Linear 1
element elasticBeamColumn 1 1 3 $A $E $Iz 1
element elasticBeamColumn 2 2 5 $A $E $Iz 1
element elasticBeamColumn 3 3 4 $A $E $Iz 1
element elasticBeamColumn 4 4 5 $A $E $Iz 1

# Both column bases fixed: ux, uy, rz.
fix 1 1 1 1
fix 2 1 1 1

# 20 kN downward at top-middle node.
timeSeries Linear 1
pattern Plain 1 1 {
    load 4 0.0 -20.0 0.0
}

constraints Plain
numberer RCM
system BandGeneral
test NormDispIncr 1.0e-12 30
algorithm Linear
integrator LoadControl 1.0
analysis Static
set ok [analyze 1]
if {$ok != 0} { puts "ANALYSIS_FAILED,BM005,$ok"; exit 2 }
reactions

set out [open "BM005_opensees_results.csv" "w"]
puts $out "record,id,ux_mm,uy_mm,rz_rad,rx_kN,ry_kN,mz_kNm,local_force_vector"
foreach n {1 2 3 4 5} {
    set d [nodeDisp $n]
    set r [nodeReaction $n]
    puts $out [format "NODE,%s,%.12g,%.12g,%.12g,%.12g,%.12g,%.12g," $n [expr 1000.0*[lindex $d 0]] [expr 1000.0*[lindex $d 1]] [lindex $d 2] [lindex $r 0] [lindex $r 1] [lindex $r 2]]
}
foreach e {1 2 3 4} {
    set q [eleResponse $e localForce]
    puts $out "ELEMENT,$e,,,,,,,\"$q\""
}
close $out
puts "BM005_COMPLETE,BM005_opensees_results.csv"
wipe
