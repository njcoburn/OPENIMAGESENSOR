from pathlib import Path
import klayout.db as k
root=Path('/foss/designs');l=k.Layout();l.read(str(root/'build/power-ring/ring_sensor_power.gds'));c=l.cell('ring_sensor_power')
for z in [36,42,46]:
 r=k.Region(c.begin_shapes_rec(l.layer(z,0))).merged()
 clip=k.Region(k.Box(350000,350000,490000,485000));r=r&clip
 print(z,'width .28um',r.width_check(280).count(),'space .28um',r.space_check(280).count(),flush=True)
 for e in r.width_check(280).each():print(str(e))
