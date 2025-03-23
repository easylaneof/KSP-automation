import time
import krpc

turn_start_altitude = 250
turn_end_altitude = 45000
target_altitude = 100000

conn = krpc.connect(name='Launch into orbit')
vessel = conn.space_center.active_vessel

ut = conn.add_stream(getattr, conn.space_center, 'ut')
altitude = conn.add_stream(getattr, vessel.flight(), 'mean_altitude')
apoapsis = conn.add_stream(getattr, vessel.orbit, 'apoapsis_altitude')
stage_2_resources = vessel.resources_in_decouple_stage(stage=2, cumulative=False)
srb_fuel = conn.add_stream(stage_2_resources.amount, 'SolidFuel')

vessel.control.sas = False
vessel.control.rcs = False
vessel.control.throttle = 1

print('3...')
time.sleep(1)
print('2...')
time.sleep(1)
print('1...')
time.sleep(1)
print('Launch!')

vessel.control.activate_next_stage()
vessel.auto_pilot.engage()
vessel.auto_pilot.target_pitch_and_heading(90, 90)

srbs_separated = False
turn_angle = 0
while True:
    if turn_start_altitude < altitude() < turn_end_altitude:
        frac = ((altitude() - turn_start_altitude) /
                (turn_end_altitude - turn_start_altitude))
        new_turn_angle = frac * 90
        if abs(new_turn_angle - turn_angle) > 0.5:
            turn_angle = new_turn_angle
            vessel.auto_pilot.target_pitch_and_heading(90 - turn_angle, 90)

    if not srbs_separated:
        if srb_fuel() < 0.1:
            vessel.control.activate_next_stage()
            srbs_separated = True

    if apoapsis() > target_altitude * 0.9:
        break

while apoapsis() < target_altitude:
    pass
vessel.control.throttle = 0.0

obr_frame = vessel.orbit.body.non_rotating_reference_frame
orb_speed = conn.add_stream(getattr, vessel.flight(obr_frame), 'speed')
altitude = conn.add_stream(getattr, vessel.flight(), 'surface_altitude')
srf_frame = vessel.orbit.body.reference_frame
srf_speed = conn.add_stream(getattr, vessel.flight(srf_frame), 'speed')

vessel.auto_pilot.disengage()

vessel.control.speed_mode = vessel.control.speed_mode.surface
vessel.auto_pilot.sas = True
time.sleep(1)
vessel.auto_pilot.sas_mode = vessel.auto_pilot.sas_mode.retrograde

while altitude() > 30000:
    time.sleep(1)

while altitude() > 1000:
    vessel.control.throttle = 0.7 if srf_speed() > 200 else 0
    time.sleep(1)

while altitude() > 50:
    if srf_speed() > altitude()/5:
        vessel.control.throttle = 1
    elif srf_speed() > altitude()/10:
        vessel.control.throttle = 0.5
    elif srf_speed() > altitude()/15:
        vessel.control.throttle = 0

while altitude() > 2:
    if srf_speed() > 7:
        vessel.control.throttle = 1
    else:
        vessel.control.throttle = 0

vessel.control.throttle = 0
