"""
Mathematical and Physics Modeling for Synthetic Telemetry Generation.
Provides deterministic seed derivation (SHA-256), IST operating shift modulation,
physics-correlated degradation curves, and distinct sensor fault injection.
"""

from datetime import datetime, timezone, timedelta
import hashlib
import math
from typing import Dict, Any, List, Optional, Tuple
import numpy as np

from backend.generators.telemetry_constants import (
    DEFAULT_TELEMETRY_SEED,
    WINDOW_START_UTC,
    SAMPLING_INTERVAL_MINUTES,
    READINGS_PER_SENSOR,
    IST_OFFSET,
    SENSOR_PHYSICS_PROFILES,
    SHIFT_LOAD_FACTORS,
    QUALITY_NORMAL,
    QUALITY_SENSOR_FAULT,
    QUALITY_INVALID,
    QUALITY_MISSING,
    PROB_MISSING,
    PROB_INVALID,
    PROB_SENSOR_FAULT,
)
try:
    from backend.generators.master_data_constants import MACHINE_CODE_TO_NUM
except ImportError:
    from generators.master_data_constants import MACHINE_CODE_TO_NUM


def get_machine_canonical(machine_id: int, machine_code: str) -> Tuple[int, str]:
    """Resolves machine ID and code to canonical machine number (1..100) and legacy code."""
    if machine_code in MACHINE_CODE_TO_NUM:
        m_num = MACHINE_CODE_TO_NUM[machine_code]
        return m_num, f"MCH-{m_num:03d}"
    if "-" in machine_code:
        suffix = machine_code.split("-")[-1]
        if suffix.isdigit():
            m_num = int(suffix)
            return m_num, f"MCH-{m_num:03d}"
    return machine_id, machine_code


def get_sensor_canonical(sensor_id: int, sensor_code: str) -> Tuple[int, str]:
    """Resolves sensor ID and code to canonical sensor number (1..500) and legacy code."""
    if sensor_code.startswith("SNS-MCH-"):
        parts = sensor_code.rsplit("-", 2)
        m_code = parts[0][4:]
        channel = parts[1]
        m_num, _ = get_machine_canonical(0, m_code)
        channel_map = {"VIB": 1, "TEMP": 2, "TMP": 2, "ACO": 3, "ACU": 3, "PRS": 4, "CUR": 5}
        c_num = channel_map.get(channel, 1)
        s_num = (m_num - 1) * 5 + c_num
        return s_num, f"SNS-{s_num:04d}"
    if sensor_code.startswith("SNS-") and sensor_code[4:].isdigit():
        s_num = int(sensor_code[4:])
        return s_num, sensor_code
    return sensor_id, sensor_code


def derive_sensor_seed(master_seed: int, sensor_id: int, sensor_code: str) -> int:
    """
    Derives an invariant, platform-independent 64-bit integer seed
    for an individual sensor's time-series RNG using SHA-256.
    Replaces Python's randomized hash() to guarantee cross-session reproducibility.
    """
    s_num, s_code = get_sensor_canonical(sensor_id, sensor_code)
    seed_str = f"{master_seed}:{s_num}:{s_code}"
    digest = hashlib.sha256(seed_str.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], byteorder="big", signed=False)


def derive_machine_degradation_profile(
    master_seed: int, machine_id: int, machine_code: str, total_steps: int = READINGS_PER_SENSOR
) -> Optional[Dict[str, Any]]:
    """
    Deterministically determines if a machine experiences a progressive mechanical
    degradation episode during the 90-day window (~15% of machines degrade).
    """
    # Normalize machine sequence to canonical 200-offset to guarantee cross-database reproducibility
    # regardless of whether a clean database or pre-existing database sequence is used.
    m_num, legacy_code = get_machine_canonical(machine_id, machine_code)
    effective_id = (200 + m_num) if isinstance(m_num, int) else machine_id

    seed_str = f"{master_seed}:degradation:{effective_id}:{legacy_code}"
    digest = hashlib.sha256(seed_str.encode("utf-8")).digest()
    m_seed = int.from_bytes(digest[:8], byteorder="big", signed=False)
    rng = np.random.default_rng(m_seed)

    # 15% probability of experiencing progressive degradation
    if rng.random() > 0.15:
        return None

    # Degradation episode lasts between 7 and 14 days (336 to 672 30-min steps)
    duration_steps = int(rng.integers(336, 672))
    # Starts between day 30 (step 1440) and day 75 (step 3600)
    start_step = int(rng.integers(1440, min(3600, total_steps - duration_steps)))

    failure_modes = ["bearing_wear", "thermal_overload", "hydraulic_leak", "motor_binding"]
    failure_mode = str(rng.choice(failure_modes))

    return {
        "start_step": start_step,
        "end_step": start_step + duration_steps,
        "duration_steps": duration_steps,
        "mode": failure_mode,
        "severity": float(rng.uniform(0.7, 1.0)),
    }


def get_shift_load_and_diurnal(dt_utc: datetime) -> Tuple[float, float]:
    """
    Calculates operational load factor and ambient thermal swing based on
    Indian Standard Time (IST, UTC+05:30).
    """
    dt_ist = dt_utc + IST_OFFSET
    hour_ist = dt_ist.hour + dt_ist.minute / 60.0
    weekday_ist = dt_ist.weekday()  # Monday is 0, Sunday is 6

    # Planned maintenance on Sunday morning (00:00 to 08:00 IST)
    if weekday_ist == 6 and hour_ist < 8.0:
        return SHIFT_LOAD_FACTORS["maintenance"], -2.0

    # Diurnal ambient temperature swing (peaks around 15:00 IST, lowest around 05:00 IST)
    diurnal_temp = 4.0 * math.sin((hour_ist - 9.0) * math.pi / 12.0)

    # Operating shifts in IST:
    # Morning: 06:00 to 14:00 IST
    # Afternoon: 14:00 to 22:00 IST
    # Night: 22:00 to 06:00 IST next day
    if 6.0 <= hour_ist < 14.0:
        load = SHIFT_LOAD_FACTORS["morning"]
    elif 14.0 <= hour_ist < 22.0:
        load = SHIFT_LOAD_FACTORS["afternoon"]
    else:
        load = SHIFT_LOAD_FACTORS["night"]

    return load, diurnal_temp


def generate_sensor_chunk_readings(
    sensor_id: int,
    sensor_code: str,
    sensor_type: str,
    machine_id: int,
    machine_code: str,
    chunk_start_step: int,
    chunk_num_steps: int,
    master_seed: int = DEFAULT_TELEMETRY_SEED,
) -> List[Tuple[int, datetime, Optional[float], str, datetime]]:
    """
    Generates a deterministic block of telemetry events for a single sensor.
    Returns list of tuples: (sensor_id, recorded_at, value, quality_status, created_at)
    """
    # 1. Deterministic RNG for this sensor
    sensor_seed = derive_sensor_seed(master_seed, sensor_id, sensor_code)
    # Advance RNG state to the chunk offset
    # PCG64 supports fast seed + step jumping
    rng = np.random.default_rng(np.random.PCG64(sensor_seed))
    # If starting after step 0, jump RNG forward to maintain chunk independence
    if chunk_start_step > 0:
        # Advance by consuming a deterministic number of draws per step (approx 6 draws per step)
        rng.bit_generator.advance(chunk_start_step * 10)

    # 2. Sensor Profile
    profile = SENSOR_PHYSICS_PROFILES.get(
        sensor_type, SENSOR_PHYSICS_PROFILES["Vibration"]
    )
    nominal_mean = profile["nominal_mean"]
    nominal_std = profile["nominal_std"]
    precision = profile["precision"]
    min_physical = profile["min_physical"]
    max_physical = profile["max_physical"]

    # 3. Machine Degradation Profile (multivariable correlation)
    deg_profile = derive_machine_degradation_profile(master_seed, machine_id, machine_code)

    now_utc = datetime.now(timezone.utc)
    records: List[Tuple[int, datetime, Optional[float], str, datetime]] = []

    # Pre-draw random uniforms for quality status masks
    quality_dice = rng.random(chunk_num_steps)
    gaussian_noise = rng.standard_normal(chunk_num_steps)
    fault_values = rng.uniform(min_physical * 0.5, max_physical * 1.5, chunk_num_steps)

    # Sensor-fault flatline simulation variable
    is_flatlined = False
    flatline_val = nominal_mean
    flatline_remaining = 0

    for i in range(chunk_num_steps):
        global_step = chunk_start_step + i
        recorded_at = WINDOW_START_UTC + timedelta(minutes=SAMPLING_INTERVAL_MINUTES * global_step)

        load_factor, diurnal_temp = get_shift_load_and_diurnal(recorded_at)

        # Baseline physical signal
        base_val = nominal_mean * load_factor + gaussian_noise[i] * nominal_std
        if sensor_type == "Temperature":
            base_val += diurnal_temp

        # Apply genuine machine degradation if active
        if deg_profile is not None:
            deg_start = deg_profile["start_step"]
            deg_end = deg_profile["end_step"]
            if deg_start <= global_step <= deg_end:
                progress = (global_step - deg_start) / (deg_end - deg_start)
                # Exponential wear curve
                wear_factor = math.exp(progress * 2.2) - 1.0  # from 0.0 to ~8.0
                mode = deg_profile["mode"]

                # Multivariable physics correlation
                if sensor_type == "Vibration":
                    # Major spike on bearing wear and motor binding
                    mult = 1.2 if mode in ["bearing_wear", "motor_binding"] else 0.4
                    base_val += wear_factor * 1.3 * mult
                elif sensor_type == "Temperature":
                    # Thermal drift occurs on all friction failures
                    base_val += wear_factor * 3.5
                elif sensor_type == "Acoustic":
                    # High cavitation / wear acoustics
                    mult = 1.3 if mode in ["bearing_wear", "hydraulic_leak"] else 0.5
                    base_val += wear_factor * 2.4 * mult
                elif sensor_type == "Pressure":
                    if mode == "hydraulic_leak":
                        # Pressure drops under seal degradation
                        base_val -= wear_factor * 6.5
                    else:
                        base_val += wear_factor * 0.8
                elif sensor_type == "Current":
                    # Motor works harder under mechanical binding
                    mult = 1.4 if mode == "motor_binding" else 0.6
                    base_val += wear_factor * 1.8 * mult

        # Ensure base physical signal remains within physics envelope
        base_val = max(min_physical, base_val)

        # 4. Data Quality and Fault Injection
        q_rand = quality_dice[i]

        if q_rand < PROB_MISSING:
            # Missing reading: NULL value with quality_status = 'missing'
            records.append((sensor_id, recorded_at, None, QUALITY_MISSING, now_utc))

        elif q_rand < (PROB_MISSING + PROB_INVALID):
            # Invalid reading: Physically impossible out-of-scale value
            if sensor_type in ["Vibration", "Pressure", "Current"]:
                # Negative reading (physically impossible)
                val = -round(abs(fault_values[i]) * 0.5 + 2.0, precision)
            else:
                # Extreme out-of-range spike
                val = round(max_physical * 1.8, precision)
            records.append((sensor_id, recorded_at, val, QUALITY_INVALID, now_utc))

        elif q_rand < (PROB_MISSING + PROB_INVALID + PROB_SENSOR_FAULT):
            # Sensor fault: Localized instrumentation error
            # Sub-types: flatline stuck (50%), high-frequency noise burst (30%), calibration offset (20%)
            fault_mode_dice = (q_rand - (PROB_MISSING + PROB_INVALID)) / PROB_SENSOR_FAULT
            if fault_mode_dice < 0.5:
                # Flatline stuck sensor
                val = round(nominal_mean * 1.05, precision)
            elif fault_mode_dice < 0.8:
                # Noise burst
                val = round(base_val + (fault_values[i] % 15.0), precision)
            else:
                # Calibration drift
                val = round(base_val + (nominal_mean * 0.45), precision)
            records.append((sensor_id, recorded_at, val, QUALITY_SENSOR_FAULT, now_utc))

        else:
            # Normal reading (including genuine asset degradation)
            val = round(base_val, precision)
            records.append((sensor_id, recorded_at, val, QUALITY_NORMAL, now_utc))

    return records
