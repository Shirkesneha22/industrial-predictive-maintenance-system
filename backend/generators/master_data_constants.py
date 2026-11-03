"""
Master Data Constants for Industrial Predictive Maintenance System.
Provides realistic pools of industrial asset configurations, Indian plant locations,
technician profiles, spare parts catalogs, and sensor specifications.
"""

from typing import List, Dict, Any

DEFAULT_RANDOM_SEED = 20261022

# 3 Target Plants in prominent Indian industrial manufacturing hubs
PLANTS_DATA: List[Dict[str, Any]] = [
    {
        "plant_code": "PLT-001",
        "name": "Ahmedabad Industrial Hydraulics & Pump Facility",
        "city": "Ahmedabad",
        "state": "Gujarat",
        "is_active": True,
    },
    {
        "plant_code": "PLT-002",
        "name": "Chennai Precision Engineering & Press Plant",
        "city": "Chennai",
        "state": "Tamil Nadu",
        "is_active": True,
    },
    {
        "plant_code": "PLT-003",
        "name": "Pune Heavy Machinery & Automotive Works",
        "city": "Pune",
        "state": "Maharashtra",
        "is_active": True,
    },
]

# 12 Target Production Lines (4 lines per plant)
PRODUCTION_LINES_DATA: List[Dict[str, Any]] = [
    # Ahmedabad Plant (PLT-001)
    {
        "line_code": "LINE-PLT-001-001",
        "plant_code": "PLT-001",
        "name": "Centrifugal Slurry & Water Pump Assembly Line",
        "is_active": True,
    },
    {
        "line_code": "LINE-PLT-001-002",
        "plant_code": "PLT-001",
        "name": "Industrial Rotary Compressor & Blower Line",
        "is_active": True,
    },
    {
        "line_code": "LINE-PLT-001-003",
        "plant_code": "PLT-001",
        "name": "High-Pressure Hydraulic Valve & Manifold Cell",
        "is_active": True,
    },
    {
        "line_code": "LINE-PLT-001-004",
        "plant_code": "PLT-001",
        "name": "Polymer Extrusion & Injection Molding Line",
        "is_active": True,
    },
    # Chennai Plant (PLT-002)
    {
        "line_code": "LINE-PLT-002-001",
        "plant_code": "PLT-002",
        "name": "Heavy Hydraulic Stamping & Press Line",
        "is_active": True,
    },
    {
        "line_code": "LINE-PLT-002-002",
        "plant_code": "PLT-002",
        "name": "Turbine Blade & Impeller Fabrication Line",
        "is_active": True,
    },
    {
        "line_code": "LINE-PLT-002-003",
        "plant_code": "PLT-002",
        "name": "Thermal Heat Treatment & Quenching Cell",
        "is_active": True,
    },
    {
        "line_code": "LINE-PLT-002-004",
        "plant_code": "PLT-002",
        "name": "Structural Heavy Plate Bending & Cutting Line",
        "is_active": True,
    },
    # Pune Plant (PLT-003)
    {
        "line_code": "LINE-PLT-003-001",
        "plant_code": "PLT-003",
        "name": "Automotive Chassis Fabrication Line",
        "is_active": True,
    },
    {
        "line_code": "LINE-PLT-003-002",
        "plant_code": "PLT-003",
        "name": "Transmission & Powertrain Machining Cell",
        "is_active": True,
    },
    {
        "line_code": "LINE-PLT-003-003",
        "plant_code": "PLT-003",
        "name": "High-Precision CNC Milling & Turning Line",
        "is_active": True,
    },
    {
        "line_code": "LINE-PLT-003-004",
        "plant_code": "PLT-003",
        "name": "Robotic Welding & Stamping Cell",
        "is_active": True,
    },
]

# Canonical 100 hierarchical machine codes across the 12 lines
ALL_MACHINE_CODES: List[str] = []
for _ln, _line in enumerate(PRODUCTION_LINES_DATA):
    _m_count = 9 if _ln < 4 else 8
    for _m_idx in range(1, _m_count + 1):
        ALL_MACHINE_CODES.append(f"MCH-{_line['line_code']}-{_m_idx:03d}")

MACHINE_CODE_TO_NUM: Dict[str, int] = {
    code: idx for idx, code in enumerate(ALL_MACHINE_CODES, start=1)
}
NUM_TO_MACHINE_CODE: Dict[int, str] = {
    idx: code for idx, code in enumerate(ALL_MACHINE_CODES, start=1)
}

# 20 Technicians with realistic Indian names, specializations, and unique corporate emails
TECHNICIANS_DATA: List[Dict[str, Any]] = [
    {"technician_code": f"TECH-{i:04d}", "name": name, "specialization": spec, "email": email}
    for i, (name, spec, email) in enumerate([
        ("Rajesh Sharma", "Vibration & Rotor Dynamics", "rajesh.sharma@indus-pm.com"),
        ("Vikram Patel", "Hydraulic & Pneumatic Systems", "vikram.patel@indus-pm.com"),
        ("Priya Sundaram", "Robotics & Automation Control", "priya.sundaram@indus-pm.com"),
        ("Suresh Kumar", "Electrical Drives & Switchgear", "suresh.kumar@indus-pm.com"),
        ("Ananya Iyer", "Predictive Analytics & Condition Monitoring", "ananya.iyer@indus-pm.com"),
        ("Rahul Verma", "CNC Machine Tools & Spindles", "rahul.verma@indus-pm.com"),
        ("Sunita Rao", "Industrial Instrumentation & Calibration", "sunita.rao@indus-pm.com"),
        ("Amit Deshmukh", "Mechanical Gearboxes & Transmissions", "amit.deshmukh@indus-pm.com"),
        ("Kavita Nair", "Thermal Systems & Heat Exchangers", "kavita.nair@indus-pm.com"),
        ("Manoj Joshi", "Lubrication Tribology & Oil Analysis", "manoj.joshi@indus-pm.com"),
        ("Deepa Menon", "Acoustic Emission Testing", "deepa.menon@indus-pm.com"),
        ("Sanjay Kulkarni", "High-Pressure Hydraulic Pumps", "sanjay.kulkarni@indus-pm.com"),
        ("Pooja Gupta", "PLC & SCADA Diagnostics", "pooja.gupta@indus-pm.com"),
        ("Rakesh Reddy", "Heavy Press Structural Maintenance", "rakesh.reddy@indus-pm.com"),
        ("Swati Mukherjee", "Centrifugal Pumps & Seals", "swati.mukherjee@indus-pm.com"),
        ("Arvind Nambiar", "Turbomachinery & Balancing", "arvind.nambiar@indus-pm.com"),
        ("Sneha Patil", "Rotary Compressors & Chillers", "sneha.patil@indus-pm.com"),
        ("Dinesh Mehta", "Laser Alignment & Geometric Calibration", "dinesh.mehta@indus-pm.com"),
        ("Meera Pillai", "Motor Current Signature Analysis (MCSA)", "meera.pillai@indus-pm.com"),
        ("Alok Bhattacharya", "Industrial Safety & Preventive Audits", "alok.bhattacharya@indus-pm.com"),
    ], start=1)
]

# 50 Spare Parts spanning realistic industrial components across categories
SPARE_PARTS_DATA: List[Dict[str, Any]] = [
    # Bearings (1-10)
    {"part_code": "PRT-0001", "name": "Deep Groove Ball Bearing 6205-2RS", "manufacturer": "SKF", "description": "Sealed deep groove radial ball bearing for moderate speed shafts"},
    {"part_code": "PRT-0002", "name": "Spherical Roller Bearing 22212-E", "manufacturer": "SKF", "description": "High-load capacity double-row self-aligning spherical roller bearing"},
    {"part_code": "PRT-0003", "name": "Tapered Roller Bearing 32010-X", "manufacturer": "Timken", "description": "Single-row tapered roller bearing supporting heavy radial and axial thrust loads"},
    {"part_code": "PRT-0004", "name": "Angular Contact Ball Bearing 7208-B", "manufacturer": "NSK", "description": "High-precision 40-degree contact angle bearing for machine tool spindles"},
    {"part_code": "PRT-0005", "name": "Cylindrical Roller Bearing NU-210-ECP", "manufacturer": "FAG", "description": "High radial capacity cylindrical roller bearing with glass fiber cage"},
    {"part_code": "PRT-0006", "name": "Pillow Block Mounted Bearing UCP-208", "manufacturer": "NTN", "description": "Cast iron mounted pillow block housing with set-screw locking insert"},
    {"part_code": "PRT-0007", "name": "Thrust Ball Bearing 51206", "manufacturer": "SKF", "description": "Single direction axial thrust ball bearing for vertical drive shafts"},
    {"part_code": "PRT-0008", "name": "Needle Roller Bearing HK-2520", "manufacturer": "INA", "description": "Drawn cup needle roller bearing for compact high-load planetary gears"},
    {"part_code": "PRT-0009", "name": "Self-Aligning Ball Bearing 1209-ETN9", "manufacturer": "SKF", "description": "Double row self-aligning bearing accommodating angular shaft deflection"},
    {"part_code": "PRT-0010", "name": "Linear Motion Ball Bushing LBCR-25-D", "manufacturer": "THK", "description": "High-speed precision linear bushing for CNC guide rails"},

    # Seals & Gaskets (11-18)
    {"part_code": "PRT-0011", "name": "Mechanical Cartridge Seal Type 21", "manufacturer": "John Crane", "description": "Single cartridge mechanical seal with silicon carbide/carbon faces"},
    {"part_code": "PRT-0012", "name": "Viton Rotary Shaft Lip Seal 45x65x10", "manufacturer": "Freudenberg", "description": "Fluoroelastomer oil seal with stainless garter spring for high-temperature pumps"},
    {"part_code": "PRT-0013", "name": "PTFE Hydraulic Rod Seal Stepseal 2K", "manufacturer": "Trelleborg", "description": "Low-friction polyurethane/PTFE step seal for hydraulic cylinder rods"},
    {"part_code": "PRT-0014", "name": "Spiral Wound Flange Gasket 3-inch 300#", "manufacturer": "Garlock", "description": "316L SS spiral wound gasket with flexible graphite filler for thermal piping"},
    {"part_code": "PRT-0015", "name": "Nitrile O-Ring Kit Metric 70 Shore", "manufacturer": "Parker Hannifin", "description": "Assorted NBR O-rings for industrial hydraulic manifold blocks"},
    {"part_code": "PRT-0016", "name": "Labyrinth Non-Contact Bearing Isolator", "manufacturer": "Inpro/Seal", "description": "Bronze non-wearing bearing isolator protecting against coolant ingress"},
    {"part_code": "PRT-0017", "name": "High-Pressure Piston Seal Glyd Ring", "manufacturer": "Hallite", "description": "Double-acting bronze-filled PTFE piston ring for heavy hydraulic presses"},
    {"part_code": "PRT-0018", "name": "Split Case Pump Casing Gasket 0.8mm", "manufacturer": "Kirloskar", "description": "Precision die-cut aramid fiber gasket for split case centrifugal pump halves"},

    # Valves & Fluid Control (19-26)
    {"part_code": "PRT-0019", "name": "4/3 Solenoid Directional Control Valve 24V", "manufacturer": "Bosch Rexroth", "description": "Electrically operated spool valve D03/NG6 interface for hydraulic circuits"},
    {"part_code": "PRT-0020", "name": "Proportional Pressure Relief Valve 350 bar", "manufacturer": "Parker Hannifin", "description": "Direct-operated proportional relief valve for continuous pressure regulation"},
    {"part_code": "PRT-0021", "name": "Pneumatic 5/2 Solenoid Valve G1/4", "manufacturer": "Festo", "description": "High-cycle pneumatic directional valve with pilot assist for robotic actuators"},
    {"part_code": "PRT-0022", "name": "Pilot-Operated Hydraulic Check Valve", "manufacturer": "Danfoss", "description": "Zero-leakage load holding pilot check valve for hydraulic clamp cylinders"},
    {"part_code": "PRT-0023", "name": "Thermostatic Oil Mixing Bypass Valve 60C", "manufacturer": "AMOT", "description": "Self-actuating thermal control valve for compressor lube oil cooling"},
    {"part_code": "PRT-0024", "name": "Stainless Steel Ball Valve 1-inch Class 600", "manufacturer": "L&T Valves", "description": "Three-piece full bore stainless steel isolation valve with locking lever"},
    {"part_code": "PRT-0025", "name": "Pressure Compensated Flow Control Valve", "manufacturer": "Eaton Vickers", "description": "Restrictor flow control valve maintaining steady cylinder feed speed"},
    {"part_code": "PRT-0026", "name": "Thermodynamic High-Pressure Steam Trap", "manufacturer": "Spirax Sarco", "description": "Forged steel disc steam trap with built-in strainer for heat lines"},

    # Couplings, Belts & Drives (27-34)
    {"part_code": "PRT-0027", "name": "Flexible Jaw Coupling Element Hytrel 100", "manufacturer": "Lovejoy", "description": "High-torque elastomeric spider insert dampening torsional shock"},
    {"part_code": "PRT-0028", "name": "Curved-Tooth Steel Gear Coupling Sleeve", "manufacturer": "KTR", "description": "Precision nylon/steel gear coupling accommodating axial and angular misalignment"},
    {"part_code": "PRT-0029", "name": "Heavy Duty V-Belt Quad-Power 4 XPA-1800", "manufacturer": "Gates", "description": "Raw-edge cogged narrow section V-belt for heavy motor drives"},
    {"part_code": "PRT-0030", "name": "High-Torque Timing Belt Synchroflex AT10", "manufacturer": "Continental", "description": "Steel-cord reinforced polyurethane synchronous belt for CNC feed axis"},
    {"part_code": "PRT-0031", "name": "Steel Roller Chain ANSI 60-1 Simplex", "manufacturer": "Diamond Chain", "description": "Shot-peened roller chain link for high-load conveyor drive assemblies"},
    {"part_code": "PRT-0032", "name": "Taper Lock Bushing 2517-45mm Bore", "manufacturer": "Fenner", "description": "Machined ductile iron split taper bushing for pulley and sprocket mounting"},
    {"part_code": "PRT-0033", "name": "Disc Pack Metal Membrane Coupling", "manufacturer": "Rexnord", "description": "Zero-backlash torsionally rigid stainless disc coupling for turbopumps"},
    {"part_code": "PRT-0034", "name": "Planetary Gearhead Sun Gear Pinion 5:1", "manufacturer": "Neugart", "description": "Case-hardened helical sun pinion for servo motor speed reducer"},

    # Pumps, Impellers & Cylinders (35-42)
    {"part_code": "PRT-0035", "name": "Closed Impeller Cast Bronze 220mm", "manufacturer": "Kirloskar", "description": "Dynamically balanced enclosed centrifugal pump impeller for clear water"},
    {"part_code": "PRT-0036", "name": "Semi-Open Slurry Impeller High-Chrome", "manufacturer": "Weir Minerals", "description": "Abrasion-resistant 28% chrome iron impeller for slurry handling"},
    {"part_code": "PRT-0037", "name": "Heavy Duty Hydraulic Cylinder Rod 63mm", "manufacturer": "Wipro Hydraulics", "description": "Hard-chrome plated induction hardened piston rod for press clamp"},
    {"part_code": "PRT-0038", "name": "Rotary Screw Compressor Air-End Rotor Pair", "manufacturer": "Atlas Copco", "description": "Precision CNC machined male/female helical screw rotor set for 75kW compressor"},
    {"part_code": "PRT-0039", "name": "Hydraulic Vane Pump Cartridge Kit 45V", "manufacturer": "Eaton", "description": "Replaceable 12-vane cartridge kit for variable delivery hydraulic pumps"},
    {"part_code": "PRT-0040", "name": "Centrifugal Pump Stainless Shaft 316", "manufacturer": "Grundfos", "description": "Ground and polished centerless stainless steel shaft for inline vertical pump"},
    {"part_code": "PRT-0041", "name": "Pneumatic ISO Cylinder Bore 80mm Stroke 250", "manufacturer": "SMC", "description": "Double-acting magnetic piston pneumatic cylinder with adjustable cushioning"},
    {"part_code": "PRT-0042", "name": "Coolant Delivery Multi-Stage Impeller Stage", "manufacturer": "Wilo", "description": "Stainless steel stage chamber and diffuser for machine tool flood coolant"},

    # Electrical & Instrumentation (43-50)
    {"part_code": "PRT-0043", "name": "Motor Contactor 3-Pole 40A 24VDC Sirius", "manufacturer": "Siemens", "description": "Compact IEC contactor for heavy AC-3 induction motor starting"},
    {"part_code": "PRT-0044", "name": "Variable Frequency Drive Control Card", "manufacturer": "ABB", "description": "Microprocessor control module for ACS880 industrial drive inverter"},
    {"part_code": "PRT-0045", "name": "Solid State Overload Relay 10-40A", "manufacturer": "Schneider Electric", "description": "Electronic motor protection relay with thermal memory and phase loss guard"},
    {"part_code": "PRT-0046", "name": "Industrial Switching Power Supply 24V 20A", "manufacturer": "Phoenix Contact", "description": "DIN rail mounted regulated SMPS power supply unit for sensor arrays"},
    {"part_code": "PRT-0047", "name": "Ceramic Heaters Band 220V 1500W", "manufacturer": "Watlow", "description": "High watt density mica-insulated band heater for plastic injection barrels"},
    {"part_code": "PRT-0048", "name": "Precision Pressure Transmitter 4-20mA", "manufacturer": "WIKA", "description": "Piezoresistive stainless pressure sensor 0-250 bar with M12 connector"},
    {"part_code": "PRT-0049", "name": "Thermocouple Duplex Mineral Insulated Type-K", "manufacturer": "Omron", "description": "Inconel sheathed fast-response thermal sensor probe for high temp bearing wells"},
    {"part_code": "PRT-0050", "name": "Optical Rotary Encoder 1024 PPR Line Driver", "manufacturer": "Baumer", "description": "Incremental industrial shaft encoder for precision servo positioning"},
]

# Machine Type Templates with realistic manufacturers, models, and compatible spare part prefixes
MACHINE_TYPES_POOL: List[Dict[str, Any]] = [
    {
        "type": "CNC 5-Axis Vertical Machining Center",
        "manufacturers": [("DMG MORI", "DMU 50 Gen3"), ("Bharat Fritz Werner", "Agni BMV 45+"), ("Haas Automation", "VF-4SS"), ("Mazak", "Variaxis i-600")],
        "compatible_part_codes": ["PRT-0001", "PRT-0004", "PRT-0010", "PRT-0012", "PRT-0030", "PRT-0042", "PRT-0050"],
    },
    {
        "type": "Heavy Hydraulic Stamping Press",
        "manufacturers": [("Schuler Presses", "TMB-1600-4"), ("Godrej & Boyce", "GHP-500-T"), ("Aida-America", "NC1-2000"), ("Komatsu", "H1F-300")],
        "compatible_part_codes": ["PRT-0002", "PRT-0013", "PRT-0015", "PRT-0017", "PRT-0019", "PRT-0020", "PRT-0037"],
    },
    {
        "type": "Industrial Centrifugal Slurry Pump",
        "manufacturers": [("Kirloskar Brothers", "DB-100-26"), ("Weir Minerals", "Warman AH 6/4"), ("KSB Pumps", "MegaCPK 050"), ("Grundfos", "CR-45-4")],
        "compatible_part_codes": ["PRT-0002", "PRT-0007", "PRT-0011", "PRT-0012", "PRT-0018", "PRT-0035", "PRT-0036", "PRT-0040"],
    },
    {
        "type": "Rotary Screw Industrial Air Compressor",
        "manufacturers": [("Atlas Copco", "GA-75-VSD+"), ("Ingersoll Rand", "R75i-Nirvana"), ("ELGi Equipments", "EG-55-Premium"), ("Kaeser", "CSD-105")],
        "compatible_part_codes": ["PRT-0002", "PRT-0005", "PRT-0012", "PRT-0023", "PRT-0029", "PRT-0038", "PRT-0048"],
    },
    {
        "type": "6-Axis Heavy Payload Articulated Robot",
        "manufacturers": [("FANUC", "M-710iC/50"), ("KUKA Robotics", "KR 210 R2700-2"), ("ABB Robotics", "IRB 6700-205"), ("Yaskawa Motoman", "GP180")],
        "compatible_part_codes": ["PRT-0004", "PRT-0008", "PRT-0028", "PRT-0034", "PRT-0021", "PRT-0041", "PRT-0050"],
    },
    {
        "type": "High-Speed Plastic Injection Molding Machine",
        "manufacturers": [("L&T Plastics", "Integra-250"), ("Milacron", "Magna-Toggle-300"), ("Engel", "e-victory-200"), ("Husky", "HyPET-HPP5")],
        "compatible_part_codes": ["PRT-0003", "PRT-0015", "PRT-0017", "PRT-0019", "PRT-0025", "PRT-0047", "PRT-0048"],
    },
    {
        "type": "Heavy Duty Industrial Lathe & Turning Center",
        "manufacturers": [("Ace Micromatic", "Super Jobber 500"), ("Bharat Fritz Werner", "Kalam TC-35"), ("Doosan Machine Tools", "Puma GT2600"), ("Okuma", "LB3000-EX")],
        "compatible_part_codes": ["PRT-0001", "PRT-0004", "PRT-0012", "PRT-0027", "PRT-0030", "PRT-0042", "PRT-0050"],
    },
    {
        "type": "Heavy Duty Industrial Conveyor Drive Station",
        "manufacturers": [("Rexnord", "Falk Quadrive 5307"), ("SEW-Eurodrive", "Movitrac MC07B"), ("Fenner India", "Torque-Arm TXT-7"), ("Siemens", "Flender FZG-200")],
        "compatible_part_codes": ["PRT-0006", "PRT-0009", "PRT-0016", "PRT-0027", "PRT-0029", "PRT-0031", "PRT-0032", "PRT-0043"],
    },
]

# 5 Sensor Configuration templates per machine
SENSOR_CONFIGURATIONS = [
    {
        "sensor_suffix": "VIB",
        "sensor_type": "Vibration",
        "unit": "mm/s",
        "name_prefix": "Bearing Vibration Velocity Sensor",
    },
    {
        "sensor_suffix": "TEMP",
        "sensor_type": "Temperature",
        "unit": "°C",
        "name_prefix": "Surface Thermal Probe",
    },
    {
        "sensor_suffix": "ACO",
        "sensor_type": "Acoustic",
        "unit": "dB",
        "name_prefix": "Ultrasonic Acoustic Emission Sensor",
    },
    {
        "sensor_suffix": "PRS",
        "sensor_type": "Pressure",
        "unit": "bar",
        "name_prefix": "Hydraulic/Pneumatic Fluid Pressure Sensor",
    },
    {
        "sensor_suffix": "CUR",
        "sensor_type": "Current",
        "unit": "A",
        "name_prefix": "Drive Motor Load Current Transducer",
    },
]
