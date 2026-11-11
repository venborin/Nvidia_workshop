# ahu_trend_2017-09-25_to_2017-10-08.csv: data dictionary

One row is one 5-minute trend reading from one air handling unit (AHU): the kind of export a building automation system gives you. Two weeks, Monday 2017-09-25 00:00 to Sunday 2017-10-08 23:55, local time. The building is simulated: the middle floor of the U.S. Department of Energy's large office reference building, with Chicago weather, from Lawrence Berkeley National Laboratory's fault detection data sets (see SOURCE.md). A missing value would be an empty field. Units are as the source documents them.

## The system

A single-duct variable-air-volume AHU serving one floor: five zones (one interior, four perimeter), each with a VAV box. Outdoor air and return air mix, pass a cooling coil (chilled water) and a supply fan, and go to the zones. The return fan follows the supply fan.

## How it is meant to run (the control sequence)

- Occupied: Monday to Friday 6:00 to 22:00, Saturday 6:00 to 18:00; unoccupied otherwise, including all of Sunday. SYS_CTL says which.
- Occupied, fans: the supply and return fans run continuously; the supply fan speed holds the duct static pressure at its setpoint (1.6 inches of water).
- Occupied, supply air temperature: held at a 55 F setpoint by the cooling coil valve when outdoor air is above 60 F or below 33.8 F. Between 33.8 and 60 F the economizer cools with outdoor air, and mechanical cooling is allowed only once the outdoor air damper is fully open; until then the cooling valve stays shut and the supply air temperature is not directly controlled, so it can drift from 55 F.
- Occupied, outdoor air damper: at a 10% minimum, except in economizer mode, where it modulates (with the return damper) to hold mixed air at 55 F.
- Occupied, zones: heating setpoint 70 F, cooling setpoint 75 F.
- Unoccupied: fans off, cooling valve and outdoor air damper closed; the system may cycle on to keep zones between 60 F and 80 F.

## Columns

- Datetime: date and time of the reading, YYYY-MM-DD HH:MM, local time, every 5 minutes.
- OA_TEMP: outdoor air temperature, F.
- RA_TEMP: return air temperature (air coming back from the zones), F.
- MA_TEMP: mixed air temperature (outdoor and return air after mixing, before the coil), F.
- SA_TEMP: supply air temperature (air leaving the unit, after the coil and fan), F.
- SA_TEMPSPT: supply air temperature setpoint, F (the 55 F setpoint, logged as 55.2).
- ZONE_TEMP_1 to ZONE_TEMP_5: air temperature in each of the five zones, F.
- SYS_CTL: occupancy mode, 1 occupied, 0 unoccupied.
- SF_SPD_DM: supply fan status, 1 on, 0 off.
- SF_CS: supply fan speed control signal, 0 to 1 (1 is full speed).
- SF_WAT: supply fan power, watts.
- SA_CFM: supply airflow, cubic feet per minute.
- OA_CFM: outdoor airflow, cubic feet per minute.
- OA_DMPR_DM: outdoor air damper command, 0 to 1 (0 should be fully closed, 1 fully open).
- OA_DMPR: outdoor air damper position (what the damper actually did), 0 to 1.
- CHWC_VLV_DM: cooling coil valve command, 0 to 1 (0 should be fully closed, 1 fully open). The valve's actual position is not logged.

Physical facts that help: mixed air lies between outdoor and return air temperature; air leaving a cooling coil is no warmer than the air entering it, and the supply fan adds only about 1 F; a damper or valve that works follows its command.
