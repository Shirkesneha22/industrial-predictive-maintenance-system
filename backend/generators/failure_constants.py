"""
Failure and Maintenance Work Order Constants for Industrial Predictive Maintenance System.
Defines failure classifications, severity ratings, physical downtime ranges,
and realistic industrial corrective maintenance action templates.
"""

from datetime import datetime, timezone
from typing import Dict, Any, List

# Master Deterministic Random Seed
DEFAULT_FAILURE_SEED = 20261022

# Target generation volumes
TOTAL_FAILURE_COUNT = 150
TYPE_A_FAILURE_COUNT = 23
TYPE_B_FAILURE_COUNT = 127
TOTAL_MACHINES_COUNT = 100
ELIGIBLE_TYPE_B_MACHINES_COUNT = 77  # 100 total - 23 Type A immune machines

# Work Order Type Constants
WORK_TYPE_CORRECTIVE = "corrective"
WORK_TYPE_PREVENTIVE = "preventive"  # Disallowed in this generation phase

# Priority and Severity Constants
SEVERITY_LOW = "low"
SEVERITY_MEDIUM = "medium"
SEVERITY_HIGH = "high"
SEVERITY_CRITICAL = "critical"

# Work Order Statuses
STATUS_COMPLETED = "completed"
STATUS_IN_PROGRESS = "in_progress"
STATUS_PENDING = "pending"

# Type A Failure Specifications (Progressive Mechanical Degradation)
# Aligned directly with the telemetry degradation modes in telemetry_math.py
TYPE_A_FAILURE_SPECS: Dict[str, Dict[str, Any]] = {
    "bearing_wear": {
        "failure_type": "Bearing Mechanical Seizure & Wear",
        "severity": SEVERITY_CRITICAL,
        "min_downtime_minutes": 480,   # 8 hours
        "max_downtime_minutes": 1440,  # 24 hours
        "description_template": (
            "Terminal mechanical breakdown caused by progressive bearing raceway spalling and cage "
            "collapse. Severe vibration velocity exceeding ISO 10816 limits with high-frequency "
            "acoustic emission spikes culminating in drive spindle seizure."
        ),
        "work_order_description": (
            "[Corrective Overhaul] Emergency spindle bearing replacement. Dismantle front/rear bearing "
            "caps, extract seized SKF/NSK bearings, clean housing bore, install replacement matched "
            "bearing set with dynamic interference fit, repack with synthetic high-temp grease, and "
            "verify vibration baseline under stepped load."
        ),
        "required_specialization": "Vibration & Rotor Dynamics",
    },
    "hydraulic_leak": {
        "failure_type": "Hydraulic Pressure Loss & Seal Rupture",
        "severity": SEVERITY_HIGH,
        "min_downtime_minutes": 360,   # 6 hours
        "max_downtime_minutes": 1080,  # 18 hours
        "description_template": (
            "Loss of hydraulic circuit pressure due to progressive degradation and catastrophic extrusion "
            "of cylinder rod seals. Telemetry demonstrated gradual operating pressure drop with "
            "severe flow cavitation prior to functional clamp failure."
        ),
        "work_order_description": (
            "[Corrective Repair] Hydraulic cylinder overhaul and seal pack replacement. Isolate manifold "
            "blocks, depressurize accumulator, replace blown rod seals and Glyd rings, flush hydraulic "
            "lines, top up ISO VG 46 mineral oil, and perform 250 bar pressure holding test."
        ),
        "required_specialization": "Hydraulic & Pneumatic Systems",
    },
    "motor_binding": {
        "failure_type": "Drive Motor Mechanical Binding",
        "severity": SEVERITY_CRITICAL,
        "min_downtime_minutes": 420,   # 7 hours
        "max_downtime_minutes": 1320,  # 22 hours
        "description_template": (
            "Drive motor stator binding and rotor eccentricity caused by coupling wear. Telemetry "
            "exhibited exponential motor current draw and thermal rise leading to electronic overload "
            "tripping and mechanical stall."
        ),
        "work_order_description": (
            "[Corrective Alignment] Motor overhaul and flexible coupling replacement. Decouple drive "
            "motor from planetary reducer, replace sheared elastomeric spider element, perform laser "
            "shaft alignment within 0.05 mm tolerance, check winding insulation resistance, and verify "
            "phase current symmetry."
        ),
        "required_specialization": "Electrical Drives & Switchgear",
    },
    "thermal_overload": {
        "failure_type": "Thermal Runaway & Spindle Overheating",
        "severity": SEVERITY_HIGH,
        "min_downtime_minutes": 300,   # 5 hours
        "max_downtime_minutes": 960,   # 16 hours
        "description_template": (
            "Uncontrolled thermal runaway and spindle overheating resulting from internal coolant line "
            "blockage and bypass valve sticking. Operating temperature exceeded safe thermal cutoff "
            "threshold triggering protective emergency stoppage."
        ),
        "work_order_description": (
            "[Corrective Service] Spindle cooling circuit restoration. Flush contaminated coolant jacket, "
            "replace seized thermostatic bypass valve, clear particulate buildup from inline strainer, "
            "refill coolant emulsion to 8% concentration, and confirm thermal equilibrium under max RPM."
        ),
        "required_specialization": "Thermal Systems & Heat Exchangers",
    },
}

# Type B Failure Templates (Sudden / Stochastic Component Failures across 77 eligible machines)
TYPE_B_FAILURE_TEMPLATES: List[Dict[str, Any]] = [
    {
        "failure_type": "Pneumatic Solenoid Valve Sticking",
        "severity": SEVERITY_MEDIUM,
        "min_downtime": 90,
        "max_downtime": 300,
        "description": "Solenoid coil burnout and valve spool sticking in 5/2 pneumatic directional valve, causing transfer arm clamp cycle timeout.",
        "work_order_description": "[Corrective Maintenance] Replaced 24VDC pneumatic solenoid valve coil and valve subplate gasket. Calibrated pilot pressure to 6.2 bar and executed 40 automated cycle checks.",
        "required_specialization": "Hydraulic & Pneumatic Systems",
    },
    {
        "failure_type": "Electrical Contactor Auxiliary Contact Arc Failure",
        "severity": SEVERITY_HIGH,
        "min_downtime": 120,
        "max_downtime": 420,
        "description": "Transient line voltage spike caused auxiliary contact pitting and contactor welding on main feed motor starter, tripping breaker.",
        "work_order_description": "[Corrective Maintenance] Replaced 3-pole 40A motor contactor and auxiliary interlock block. Performed insulation Megger test (>60 MΩ) and verified control relay sequencing.",
        "required_specialization": "Electrical Drives & Switchgear",
    },
    {
        "failure_type": "Drive Transmission V-Belt Fatigue Snap",
        "severity": SEVERITY_MEDIUM,
        "min_downtime": 60,
        "max_downtime": 240,
        "description": "Sudden tensile fatigue rupture of cogged drive V-belt during high-feed milling operation, causing instantaneous spindle speed loss.",
        "work_order_description": "[Corrective Maintenance] Installed new matched pair of heavy duty Quad-Power V-belts. Verified pulley groove geometry, aligned sheaves, and calibrated belt tension using sonic meter.",
        "required_specialization": "Mechanical Gearboxes & Transmissions",
    },
    {
        "failure_type": "Optical Rotary Encoder Signal Loss",
        "severity": SEVERITY_HIGH,
        "min_downtime": 150,
        "max_downtime": 480,
        "description": "Loss of differential quadrature pulse train on Z-axis servo motor optical encoder, inducing servo tracking error and hard stop.",
        "work_order_description": "[Corrective Maintenance] Cleaned optical grating disc, replaced damaged M12 sensor connector cable, and recalibrated axis reference home position using laser calibration fixture.",
        "required_specialization": "Robotics & Automation Control",
    },
    {
        "failure_type": "Coolant Delivery Impeller Swarf Jam",
        "severity": SEVERITY_MEDIUM,
        "min_downtime": 90,
        "max_downtime": 360,
        "description": "Metallic swarf bypassed damaged chip conveyor screen, jamming centrifugal coolant impeller and tripping pump thermal breaker.",
        "work_order_description": "[Corrective Maintenance] Disassembled pump volute casing, cleared trapped metal shavings from bronze impeller, replaced intake suction strainer, and verified rated flood flow.",
        "required_specialization": "Centrifugal Pumps & Seals",
    },
    {
        "failure_type": "Hydraulic Proportional Pressure Relief Valve Drift",
        "severity": SEVERITY_HIGH,
        "min_downtime": 180,
        "max_downtime": 540,
        "description": "Particulate silt siltation jammed proportional pressure relief poppet, preventing hydraulic power pack from building required 210 bar.",
        "work_order_description": "[Corrective Maintenance] Replaced cartridge relief valve. Connected portable offline oil filtration unit to cycle reservoir to ISO 4406 15/13/10 cleanliness level.",
        "required_specialization": "High-Pressure Hydraulic Pumps",
    },
    {
        "failure_type": "PLC Fieldbus Communication Bus Fault",
        "severity": SEVERITY_CRITICAL,
        "min_downtime": 120,
        "max_downtime": 360,
        "description": "Intermittent electromagnetic interference caused communication dropouts on distributed I/O drop, activating safety PLC emergency stop.",
        "work_order_description": "[Corrective Maintenance] Inspected cable shielding integrity, replaced corroded bus termination resistor, routed communication cables away from VFD power leads, and verified zero bus errors.",
        "required_specialization": "PLC & SCADA Diagnostics",
    },
    {
        "failure_type": "Automated Lubrication Line Shear",
        "severity": SEVERITY_HIGH,
        "min_downtime": 90,
        "max_downtime": 300,
        "description": "Flexible high-pressure nylon lubrication line severed in cable drag chain, starving linear guideway carriages of EP-2 grease.",
        "work_order_description": "[Corrective Maintenance] Replaced severed 6mm polyamide lube hose with steel-braided hose. Manually primed progressive distributor block and verified oil delivery at all 8 guide blocks.",
        "required_specialization": "Lubrication Tribology & Oil Analysis",
    },
    {
        "failure_type": "Compressor Rotary Unloader Valve Sticking",
        "severity": SEVERITY_MEDIUM,
        "min_downtime": 120,
        "max_downtime": 360,
        "description": "Condensate sludge buildup jammed rotary compressor intake unloader valve in closed position, resulting in complete air delivery failure.",
        "work_order_description": "[Corrective Maintenance] Removed unloader valve, cleaned carbon/varnish deposits from piston bore, replaced Viton lip seals and return spring, and calibrated load/unload differential.",
        "required_specialization": "Rotary Compressors & Chillers",
    },
    {
        "failure_type": "Heavy Press Hydraulic Cylinder Tie-Rod Stretch",
        "severity": SEVERITY_CRITICAL,
        "min_downtime": 360,
        "max_downtime": 900,
        "description": "Loose tie-rod pre-tension caused flange seal gap extrusion and severe 180-bar hydraulic oil misting during high-tonnage stamping cycle.",
        "work_order_description": "[Corrective Maintenance] Replaced damaged polyurethane cylinder flange gasket. Used hydraulic bolt tensioner to re-torque cylinder tie-rods in cross-pattern to 1,850 Nm specified tension.",
        "required_specialization": "Heavy Press Structural Maintenance",
    },
]
