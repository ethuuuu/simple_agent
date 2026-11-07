def convert_flow(value, from_unit, to_unit):
    """
    Converts flow rates between m3/h, L/min, and GPM.
    
    Units:
    - 'm3/h': cubic meters per hour
    - 'L/min': liters per minute
    - 'GPM': US Gallons per minute
    """
    
    # Conversion factors to base unit (m3/h)
    # 1 L/min = 0.06 m3/h
    # 1 GPM = (3.78541 L / 1 min) * (1/1000 m3 / 1 min) * (1 h / 60 min) = 0.06309016666666667 m3/h
    
    factors_to_m3h = {
        'm3/h': 1.0,
        'L/min': 0.06,
        'GPM': 3.78541 / 60.0
    }
    
    if from_unit not in factors_to_m3h or to_unit not in factors_to_m3h:
        raise ValueError(f"Unsupported unit. Supported: {list(factors_to_m3h.keys())}")

    # Convert input to m3/h
    val_m3h = value * factors_to_m3h[from_unit]
    
    # Convert m3/h to target
    result = val_m3h / factors_to_m3h[to_unit]
    return result

def test_robust():
    # Conversion factors to m3/h
    f_to_m3h = {
        'm3/h': 1.0,
        'L/min': 0.06,
        'GPM': 3.78541 / 60.0
    }
    
    # Test cases: (value, from_unit, to_unit)
    test_cases = [
        (100, 'm3/h', 'L/min'),
        (100, 'm3/h', 'GPM'),
        (100, 'L/min', 'm3/h'),
        (100, 'L/min', 'GPM'),
        (100, 'GPM', 'm3/h'),
        (100, 'GPM', 'L/min'),
        (0, 'm3/h', 'L/min'),
        (0, 'L/min', 'GPM'),
        (0, 'GPM', 'm3/h'),
        (-10, 'm3/h', 'L/min'),
        (-5, 'L/min', 'GPM'),
        (-1, 'GPM', 'm3/h'),
    ]
    
    print(f"{'Input':<15} | {'From':<7} | {'To':<7} | {'Actual':<15}")
    print("-" * 50)
    
    for val, f_unit, t_unit in test_cases:
        actual = convert_flow(val, f_unit, t_unit)
        print(f"{str(val):<15} | {f_unit:<7} | {t_unit:<7} | {actual:<15.5f}")

if __name__ == "__main__":
    test_robust()
