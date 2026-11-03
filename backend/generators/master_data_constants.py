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
        "plant_code": "PLANT-PUN-01",
        "name": "Pune Heavy Machinery & Automotive Works",
        "city": "Pune",
        "state": "Maharashtra",
        "is_active": True,
    },
    {
        "plant_code": "PLANT-CHN-01",
        "name": "Chennai Precision Engineering & Press Plant",
        "city": "Chennai",
        "state": "Tamil Nadu",
        "is_active": True,
    },
    {
        "plant_code": "PLANT-AMD-01",
        "name": "Ahmedabad Industrial Hydraulics & Pump Facility",
        "city": "Ahmedabad",
        "state": "Gujarat",
        "is_active": True,
    },
]

# 12 Target Production Lines (4 lines per plant)
PRODUCTION_LINES_DATA: List[Dict[str, Any]] = [
    # Pune Plant (PLANT-PUN-01)
    {
        "line_code": "LINE-PUN-01",
        "plant_code": "PLANT-PUN-01",
        "name": "Automotive Chassis Fabrication Line",
        "is_active": True,
    },
    {
        "line_code": "LINE-PUN-02",
        "plant_code": "PLANT-PUN-01",
        "name": "Transmission & Powertrain Machining Cell",
        "is_active": True,
    },
    {
        "line_code": "LINE-PUN-03",
        "plant_code": "PLANT-PUN-01",
        "name": "High-Precision CNC Milling & Turning Line",
        "is_active": True,
    },
    {
        "line_code": "LINE-PUN-04",
        "plant_code": "PLANT-PUN-01",
        "name": "Robotic Welding & Stamping Cell",
        "is_active": True,
    },
    # Chennai Plant (PLANT-CHN-01)
    {
        "line_code": "LINE-CHN-01",
        "plant_code": "PLANT-CHN-01",
        "name": "Heavy Hydraulic Stamping & Press Line",
        "is_active": True,
    },
    {
        "line_code": "LINE-CHN-02",
        "plant_code": "PLANT-CHN-01",
        "name": "Turbine Blade & Impeller Fabrication Line",
        "is_active": True,
    },
    {
        "line_code": "LINE-CHN-03",
        "plant_code": "PLANT-CHN-01",
        "name": "Thermal Heat Treatment & Quenching Cell",
        "is_active": True,
    },
    {
        "line_code": "LINE-CHN-04",
        "plant_code": "PLANT-CHN-01",
        "name": "Structural Heavy Plate Bending & Cutting Line",
        "is_active": True,
    },
    # Ahmedabad Plant (PLANT-AMD-01)
    {
        "line_code": "LINE-AMD-01",
        "plant_code": "PLANT-AMD-01",
        "name": "Centrifugal Slurry & Water Pump Assembly Line",
        "is_active": True,
    },
    {
        "line_code": "LINE-AMD-02",
        "plant_code": "PLANT-AMD-01",
        "name": "Industrial Rotary Compressor & Blower Line",
        "is_active": True,
    },
    {
        "line_code": "LINE-AMD-03",
        "plant_code": "PLANT-AMD-01",
        "name": "High-Pressure Hydraulic Valve & Manifold Cell",
        "is_active": True,
    },
    {
        "line_code": "LINE-AMD-04",
        "plant_code": "PLANT-AMD-01",
        "name": "Polymer Extrusion & Injection Molding Line",
        "is_active": True,
    },
]

# 20 Technicians with realistic Indian names, specializations, and unique corporate emails
TECHNICIANS_DATA: List[Dict[str, Any]] = [
    {"technician_code": "TECH-001", "name": "Rajesh Sharma", "specialization": "Vibration & Rotor Dynamics", "email": "rajesh.sharma@indus-pm.com"},
    {"technician_code": "TECH-002", "name": "Vikram Patel", "specialization": "Hydraulic & Pneumatic Systems", "email": "vikram.patel@indus-pm.com"},
    {"technician_code": "TECH-003", "name": "Priya Sundaram", "specialization": "Robotics & Automation Control", "email": "priya.sundaram@indus-pm.com"},
    {"technician_code": "TECH-004", "name": "Suresh Kumar", "specialization": "Electrical Drives & Switchgear", "email": "suresh.kumar@indus-pm.com"},
    {"technician_code": "TECH-005", "name": "Ananya Iyer", "specialization": "Predictive Analytics & Condition Monitoring", "email": "ananya.iyer@indus-pm.com"},
    {"technician_code": "TECH-006", "name": "Rahul Verma", "specialization": "CNC Machine Tools & Spindles", "email": "rahul.verma@indus-pm.com"},
    {"technician_code": "TECH-007", "name": "Sunita Rao", "specialization": "Industrial Instrumentation & Calibration", "email": "sunita.rao@indus-pm.com"},
    {"technician_code": "TECH-008", "name": "Amit Deshmukh", "specialization": "Mechanical Gearboxes & Transmissions", "email": "amit.deshmukh@indus-pm.com"},
    {"technician_code": "TECH-009", "name": "Kavita Nair", "specialization": "Thermal Systems & Heat Exchangers", "email": "kavita.nair@indus-pm.com"},
    {"technician_code": "TECH-010", "name": "Manoj Joshi", "specialization": "Lubrication Tribology & Oil Analysis", "email": "manoj.joshi@indus-pm.com"},
    {"technician_code": "TECH-011", "name": "Deepa Menon", "specialization": "Acoustic Emission Testing", "email": "deepa.menon@indus-pm.com"},
    {"technician_code": "TECH-012", "name": "Sanjay Kulkarni", "specialization": "High-Pressure Hydraulic Pumps", "email": "sanjay.kulkarni@indus-pm.com"},
    {"technician_code": "TECH-013", "name": "Pooja Gupta", "specialization": "PLC & SCADA Diagnostics", "email": "pooja.gupta@indus-pm.com"},
    {"technician_code": "TECH-014", "name": "Rakesh Reddy", "specialization": "Heavy Press Structural Maintenance", "email": "rakesh.reddy@indus-pm.com"},
    {"technician_code": "TECH-015", "name": "Swati Mukherjee", "specialization": "Centrifugal Pumps & Seals", "email": "swati.mukherjee@indus-pm.com"},
    {"technician_code": "TECH-016", "name": "Arvind Nambiar", "specialization": "Turbomachinery & Balancing", "email": "arvind.nambiar@indus-pm.com"},
    {"technician_code": "TECH-017", "name": "Sneha Patil", "specialization": "Rotary Compressors & Chillers", "email": "sneha.patil@indus-pm.com"},
    {"technician_code": "TECH-018", "name": "Dinesh Mehta", "specialization": "Laser Alignment & Geometric Calibration", "email": "dinesh.mehta@indus-pm.com"},
    {"technician_code": "TECH-019", "name": "Meera Pillai", "specialization": "Motor Current Signature Analysis (MCSA)", "email": "meera.pillai@indus-pm.com"},
    {"technician_code": "TECH-020", "name": "Alok Bhattacharya", "specialization": "Industrial Safety & Preventive Audits", "email": "alok.bhattacharya@indus-pm.com"},
]

# 50 Spare Parts spanning realistic industrial components across categories
SPARE_PARTS_DATA: List[Dict[str, Any]] = [
    # Bearings (1-10)
    {"part_code": "PART-BRG-001", "name": "Deep Groove Ball Bearing 6205-2RS", "manufacturer": "SKF", "description": "Sealed deep groove radial ball bearing for moderate speed shafts"},
    {"part_code": "PART-BRG-002", "name": "Spherical Roller Bearing 22212-E", "manufacturer": "SKF", "description": "High-load capacity double-row self-aligning spherical roller bearing"},
    {"part_code": "PART-BRG-003", "name": "Tapered Roller Bearing 32010-X", "manufacturer": "Timken", "description": "Single-row tapered roller bearing supporting heavy radial and axial thrust loads"},
    {"part_code": "PART-BRG-004", "name": "Angular Contact Ball Bearing 7208-B", "manufacturer": "NSK", "description": "High-precision 40-degree contact angle bearing for machine tool spindles"},
    {"part_code": "PART-BRG-005", "name": "Cylindrical Roller Bearing NU-210-ECP", "manufacturer": "FAG", "description": "High radial capacity cylindrical roller bearing with glass fiber cage"},
    {"part_code": "PART-BRG-006", "name": "Pillow Block Mounted Bearing UCP-208", "manufacturer": "NTN", "description": "Cast iron mounted pillow block housing with set-screw locking insert"},
    {"part_code": "PART-BRG-007", "name": "Thrust Ball Bearing 51206", "manufacturer": "SKF", "description": "Single direction axial thrust ball bearing for vertical drive shafts"},
    {"part_code": "PART-BRG-008", "name": "Needle Roller Bearing HK-2520", "manufacturer": "INA", "description": "Drawn cup needle roller bearing for compact high-load planetary gears"},
    {"part_code": "PART-BRG-009", "name": "Self-Aligning Ball Bearing 1209-ETN9", "manufacturer": "SKF", "description": "Double row self-aligning bearing accommodating angular shaft deflection"},
    {"part_code": "PART-BRG-010", "name": "Linear Motion Ball Bushing LBCR-25-D", "manufacturer": "THK", "description": "High-speed precision linear bushing for CNC guide rails"},

    # Seals & Gaskets (11-18)
    {"part_code": "PART-SEL-011", "name": "Mechanical Cartridge Seal Type 21", "manufacturer": "John Crane", "description": "Single cartridge mechanical seal with silicon carbide/carbon faces"},
    {"part_code": "PART-SEL-012", "name": "Viton Rotary Shaft Lip Seal 45x65x10", "manufacturer": "Freudenberg", "description": "Fluoroelastomer oil seal with stainless garter spring for high-temperature pumps"},
    {"part_code": "PART-SEL-013", "name": "PTFE Hydraulic Rod Seal Stepseal 2K", "manufacturer": "Trelleborg", "description": "Low-friction polyurethane/PTFE step seal for hydraulic cylinder rods"},
    {"part_code": "PART-SEL-014", "name": "Spiral Wound Flange Gasket 3-inch 300#", "manufacturer": "Garlock", "description": "316L SS spiral wound gasket with flexible graphite filler for thermal piping"},
    {"part_code": "PART-SEL-015", "name": "Nitrile O-Ring Kit Metric 70 Shore", "manufacturer": "Parker Hannifin", "description": "Assorted NBR O-rings for industrial hydraulic manifold blocks"},
    {"part_code": "PART-SEL-016", "name": "Labyrinth Non-Contact Bearing Isolator", "manufacturer": "Inpro/Seal", "description": "Bronze non-wearing bearing isolator protecting against coolant ingress"},
    {"part_code": "PART-SEL-017", "name": "High-Pressure Piston Seal Glyd Ring", "manufacturer": "Hallite", "description": "Double-acting bronze-filled PTFE piston ring for heavy hydraulic presses"},
    {"part_code": "PART-SEL-018", "name": "Split Case Pump Casing Gasket 0.8mm", "manufacturer": "Kirloskar", "description": "Precision die-cut aramid fiber gasket for split case centrifugal pump halves"},

    # Valves & Fluid Control (19-26)
    {"part_code": "PART-VLV-019", "name": "4/3 Solenoid Directional Control Valve 24V", "manufacturer": "Bosch Rexroth", "description": "Electrically operated spool valve D03/NG6 interface for hydraulic circuits"},
    {"part_code": "PART-VLV-020", "name": "Proportional Pressure Relief Valve 350 bar", "manufacturer": "Parker Hannifin", "description": "Direct-operated proportional relief valve for continuous pressure regulation"},
    {"part_code": "PART-VLV-021", "name": "Pneumatic 5/2 Solenoid Valve G1/4", "manufacturer": "Festo", "description": "High-cycle pneumatic directional valve with pilot assist for robotic actuators"},
    {"part_code": "PART-VLV-022", "name": "Pilot-Operated Hydraulic Check Valve", "manufacturer": "Danfoss", "description": "Zero-leakage load holding pilot check valve for hydraulic clamp cylinders"},
    {"part_code": "PART-VLV-023", "name": "Thermostatic Oil Mixing Bypass Valve 60C", "manufacturer": "AMOT", "description": "Self-actuating thermal control valve for compressor lube oil cooling"},
    {"part_code": "PART-VLV-024", "name": "Stainless Steel Ball Valve 1-inch Class 600", "manufacturer": "L&T Valves", "description": "Three-piece full bore stainless steel isolation valve with locking lever"},
    {"part_code": "PART-VLV-025", "name": "Pressure Compensated Flow Control Valve", "manufacturer": "Eaton Vickers", "description": "Restrictor flow control valve maintaining steady cylinder feed speed"},
    {"part_code": "PART-VLV-026", "name": "Thermodynamic High-Pressure Steam Trap", "manufacturer": "Spirax Sarco", "description": "Forged steel disc steam trap with built-in strainer for heat lines"},

    # Couplings, Belts & Drives (27-34)
    {"part_code": "PART-DRV-027", "name": "Flexible Jaw Coupling Element Hytrel 100", "manufacturer": "Lovejoy", "description": "High-torque elastomeric spider insert dampening torsional shock"},
    {"part_code": "PART-DRV-028", "name": "Curved-Tooth Steel Gear Coupling Sleeve", "manufacturer": "KTR", "description": "Precision nylon/steel gear coupling accommodating axial and angular misalignment"},
    {"part_code": "PART-DRV-029", "name": "Heavy Duty V-Belt Quad-Power 4 XPA-1800", "manufacturer": "Gates", "description": "Raw-edge cogged narrow section V-belt for heavy motor drives"},
    {"part_code": "PART-DRV-030", "name": "High-Torque Timing Belt Synchroflex AT10", "manufacturer": "Continental", "description": "Steel-cord reinforced polyurethane synchronous belt for CNC feed axis"},
    {"part_code": "PART-DRV-031", "name": "Steel Roller Chain ANSI 60-1 Simplex", "manufacturer": "Diamond Chain", "description": "Shot-peened roller chain link for high-load conveyor drive assemblies"},
    {"part_code": "PART-DRV-032", "name": "Taper Lock Bushing 2517-45mm Bore", "manufacturer": "Fenner", "description": "Machined ductile iron split taper bushing for pulley and sprocket mounting"},
    {"part_code": "PART-DRV-033", "name": "Disc Pack Metal Membrane Coupling", "manufacturer": "Rexnord", "description": "Zero-backlash torsionally rigid stainless disc coupling for turbopumps"},
    {"part_code": "PART-DRV-034", "name": "Planetary Gearhead Sun Gear Pinion 5:1", "manufacturer": "Neugart", "description": "Case-hardened helical sun pinion for servo motor speed reducer"},

    # Pumps, Impellers & Cylinders (35-42)
    {"part_code": "PART-CMP-035", "name": "Closed Impeller Cast Bronze 220mm", "manufacturer": "Kirloskar", "description": "Dynamically balanced enclosed centrifugal pump impeller for clear water"},
    {"part_code": "PART-CMP-036", "name": "Semi-Open Slurry Impeller High-Chrome", "manufacturer": "Weir Minerals", "description": "Abrasion-resistant 28% chrome iron impeller for slurry handling"},
    {"part_code": "PART-CMP-037", "name": "Heavy Duty Hydraulic Cylinder Rod 63mm", "manufacturer": "Wipro Hydraulics", "description": "Hard-chrome plated induction hardened piston rod for press clamp"},
    {"part_code": "PART-CMP-038", "name": "Rotary Screw Compressor Air-End Rotor Pair", "manufacturer": "Atlas Copco", "description": "Precision CNC machined male/female helical screw rotor set for 75kW compressor"},
    {"part_code": "PART-CMP-039", "name": "Hydraulic Vane Pump Cartridge Kit 45V", "manufacturer": "Eaton", "description": "Replaceable 12-vane cartridge kit for variable delivery hydraulic pumps"},
    {"part_code": "PART-CMP-040", "name": "Centrifugal Pump Stainless Shaft 316", "manufacturer": "Grundfos", "description": "Ground and polished centerless stainless steel shaft for inline vertical pump"},
    {"part_code": "PART-CMP-041", "name": "Pneumatic ISO Cylinder Bore 80mm Stroke 250", "manufacturer": "SMC", "description": "Double-acting magnetic piston pneumatic cylinder with adjustable cushioning"},
    {"part_code": "PART-CMP-042", "name": "Coolant Delivery Multi-Stage Impeller Stage", "manufacturer": "Wilo", "description": "Stainless steel stage chamber and diffuser for machine tool flood coolant"},

    # Electrical & Instrumentation (43-50)
    {"part_code": "PART-ELE-043", "name": "Motor Contactor 3-Pole 40A 24VDC Sirius", "manufacturer": "Siemens", "description": "Compact IEC contactor for heavy AC-3 induction motor starting"},
    {"part_code": "PART-ELE-044", "name": "Variable Frequency Drive Control Card", "manufacturer": "ABB", "description": "Microprocessor control module for ACS880 industrial drive inverter"},
    {"part_code": "PART-ELE-045", "name": "Solid State Overload Relay 10-40A", "manufacturer": "Schneider Electric", "description": "Electronic motor protection relay with thermal memory and phase loss guard"},
    {"part_code": "PART-ELE-046", "name": "Industrial Switching Power Supply 24V 20A", "manufacturer": "Phoenix Contact", "description": "DIN rail mounted regulated SMPS power supply unit for sensor arrays"},
    {"part_code": "PART-ELE-047", "name": "Ceramic Heaters Band 220V 1500W", "manufacturer": "Watlow", "description": "High watt density mica-insulated band heater for plastic injection barrels"},
    {"part_code": "PART-ELE-048", "name": "Precision Pressure Transmitter 4-20mA", "manufacturer": "WIKA", "description": "Piezoresistive stainless pressure sensor 0-250 bar with M12 connector"},
    {"part_code": "PART-ELE-049", "name": "Thermocouple Duplex Mineral Insulated Type-K", "manufacturer": "Omron", "description": "Inconel sheathed fast-response thermal sensor probe for high temp bearing wells"},
    {"part_code": "PART-ELE-050", "name": "Optical Rotary Encoder 1024 PPR Line Driver", "manufacturer": "Baumer", "description": "Incremental industrial shaft encoder for precision servo positioning"},
]

# Machine Type Templates with realistic manufacturers, models, and compatible spare part prefixes
MACHINE_TYPES_POOL: List[Dict[str, Any]] = [
    {
        "type": "CNC 5-Axis Vertical Machining Center",
        "manufacturers": [("DMG MORI", "DMU 50 Gen3"), ("Bharat Fritz Werner", "Agni BMV 45+"), ("Haas Automation", "VF-4SS"), ("Mazak", "Variaxis i-600")],
        "compatible_part_codes": ["PART-BRG-001", "PART-BRG-004", "PART-BRG-010", "PART-SEL-012", "PART-DRV-030", "PART-CMP-042", "PART-ELE-050"],
    },
    {
        "type": "Heavy Hydraulic Stamping Press",
        "manufacturers": [("Schuler Presses", "TMB-1600-4"), ("Godrej & Boyce", "GHP-500-T"), ("Aida-America", "NC1-2000"), ("Komatsu", "H1F-300")],
        "compatible_part_codes": ["PART-BRG-002", "PART-SEL-013", "PART-SEL-015", "PART-SEL-017", "PART-VLV-019", "PART-VLV-020", "PART-CMP-037"],
    },
    {
        "type": "Industrial Centrifugal Slurry Pump",
        "manufacturers": [("Kirloskar Brothers", "DB-100-26"), ("Weir Minerals", "Warman AH 6/4"), ("KSB Pumps", "MegaCPK 050"), ("Grundfos", "CR-45-4")],
        "compatible_part_codes": ["PART-BRG-002", "PART-BRG-007", "PART-SEL-011", "PART-SEL-012", "PART-SEL-018", "PART-CMP-035", "PART-CMP-036", "PART-CMP-040"],
    },
    {
        "type": "Rotary Screw Industrial Air Compressor",
        "manufacturers": [("Atlas Copco", "GA-75-VSD+"), ("Ingersoll Rand", "R75i-Nirvana"), ("ELGi Equipments", "EG-55-Premium"), ("Kaeser", "CSD-105")],
        "compatible_part_codes": ["PART-BRG-002", "PART-BRG-005", "PART-SEL-012", "PART-VLV-023", "PART-DRV-029", "PART-CMP-038", "PART-ELE-048"],
    },
    {
        "type": "6-Axis Heavy Payload Articulated Robot",
        "manufacturers": [("FANUC", "M-710iC/50"), ("KUKA Robotics", "KR 210 R2700-2"), ("ABB Robotics", "IRB 6700-205"), ("Yaskawa Motoman", "GP180")],
        "compatible_part_codes": ["PART-BRG-004", "PART-BRG-008", "PART-DRV-028", "PART-DRV-034", "PART-VLV-021", "PART-CMP-041", "PART-ELE-050"],
    },
    {
        "type": "High-Speed Plastic Injection Molding Machine",
        "manufacturers": [("L&T Plastics", "Integra-250"), ("Milacron", "Magna-Toggle-300"), ("Engel", "e-victory-200"), ("Husky", "HyPET-HPP5")],
        "compatible_part_codes": ["PART-BRG-003", "PART-SEL-015", "PART-SEL-017", "PART-VLV-019", "PART-VLV-025", "PART-ELE-047", "PART-ELE-048"],
    },
    {
        "type": "Heavy Duty Industrial Lathe & Turning Center",
        "manufacturers": [("Ace Micromatic", "Super Jobber 500"), ("Bharat Fritz Werner", "Kalam TC-35"), ("Doosan Machine Tools", "Puma GT2600"), ("Okuma", "LB3000-EX")],
        "compatible_part_codes": ["PART-BRG-001", "PART-BRG-004", "PART-SEL-012", "PART-DRV-027", "PART-DRV-030", "PART-CMP-042", "PART-ELE-050"],
    },
    {
        "type": "Heavy Duty Industrial Conveyor Drive Station",
        "manufacturers": [("Rexnord", "Falk Quadrive 5307"), ("SEW-Eurodrive", "Movitrac MC07B"), ("Fenner India", "Torque-Arm TXT-7"), ("Siemens", "Flender FZG-200")],
        "compatible_part_codes": ["PART-BRG-006", "PART-BRG-009", "PART-SEL-016", "PART-DRV-027", "PART-DRV-029", "PART-DRV-031", "PART-DRV-032", "PART-ELE-043"],
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
        "sensor_suffix": "TMP",
        "sensor_type": "Temperature",
        "unit": "°C",
        "name_prefix": "Surface Thermal Probe",
    },
    {
        "sensor_suffix": "ACU",
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
