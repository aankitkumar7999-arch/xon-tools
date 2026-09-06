# ==============================================================
# Unit Converter Route
# POST /api/convert/unit → { value, from_unit, to_unit, category }
# ==============================================================

from flask import Blueprint, request, jsonify

converter_bp = Blueprint('converter', __name__)

# Conversion factors relative to base unit
UNITS = {
    'length': {
        'base': 'meter',
        'units': {
            'meter': 1, 'kilometer': 1000, 'centimeter': 0.01,
            'millimeter': 0.001, 'mile': 1609.344, 'yard': 0.9144,
            'foot': 0.3048, 'inch': 0.0254, 'nautical_mile': 1852,
        }
    },
    'weight': {
        'base': 'kilogram',
        'units': {
            'kilogram': 1, 'gram': 0.001, 'milligram': 0.000001,
            'tonne': 1000, 'pound': 0.453592, 'ounce': 0.0283495,
            'stone': 6.35029,
        }
    },
    'temperature': {
        'special': True,  # Handled separately
        'units': ['celsius', 'fahrenheit', 'kelvin']
    },
    'speed': {
        'base': 'mps',
        'units': {
            'mps': 1, 'kph': 0.277778, 'mph': 0.44704, 'knot': 0.514444,
        }
    },
    'area': {
        'base': 'sq_meter',
        'units': {
            'sq_meter': 1, 'sq_kilometer': 1e6, 'sq_centimeter': 0.0001,
            'sq_foot': 0.092903, 'sq_inch': 0.00064516,
            'acre': 4046.86, 'hectare': 10000,
        }
    },
    'volume': {
        'base': 'liter',
        'units': {
            'liter': 1, 'milliliter': 0.001, 'cubic_meter': 1000,
            'gallon_us': 3.78541, 'gallon_uk': 4.54609,
            'fluid_ounce': 0.0295735, 'cup': 0.236588, 'pint': 0.473176,
        }
    },
    'data': {
        'base': 'byte',
        'units': {
            'byte': 1, 'kilobyte': 1024, 'megabyte': 1048576,
            'gigabyte': 1073741824, 'terabyte': 1099511627776,
            'bit': 0.125, 'kilobit': 128, 'megabit': 131072,
        }
    },
}


def convert_temperature(value, from_u, to_u):
    # Convert to Celsius first
    if from_u == 'celsius':
        c = value
    elif from_u == 'fahrenheit':
        c = (value - 32) * 5 / 9
    elif from_u == 'kelvin':
        c = value - 273.15
    else:
        raise ValueError(f'Unknown temperature unit: {from_u}')

    # Then to target
    if to_u == 'celsius':
        return c
    elif to_u == 'fahrenheit':
        return c * 9 / 5 + 32
    elif to_u == 'kelvin':
        return c + 273.15
    else:
        raise ValueError(f'Unknown temperature unit: {to_u}')


@converter_bp.route('/unit', methods=['POST'])
def convert():
    data      = request.get_json()
    value     = float((data or {}).get('value', 0))
    from_unit = (data or {}).get('from_unit', '').lower().strip()
    to_unit   = (data or {}).get('to_unit', '').lower().strip()
    category  = (data or {}).get('category', '').lower().strip()

    if category not in UNITS:
        return jsonify({'error': f'Category nahi mila: {category}'}), 400

    cat_data = UNITS[category]

    try:
        if cat_data.get('special'):
            result = convert_temperature(value, from_unit, to_unit)
        else:
            units = cat_data['units']
            if from_unit not in units:
                return jsonify({'error': f'Unit nahi mila: {from_unit}'}), 400
            if to_unit not in units:
                return jsonify({'error': f'Unit nahi mila: {to_unit}'}), 400
            # Convert via base unit
            base_value = value * units[from_unit]
            result     = base_value / units[to_unit]

        return jsonify({
            'input':     value,
            'result':    round(result, 8),
            'from_unit': from_unit,
            'to_unit':   to_unit,
            'category':  category,
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@converter_bp.route('/categories', methods=['GET'])
def categories():
    result = {}
    for cat, data in UNITS.items():
        if data.get('special'):
            result[cat] = list(data['units'])
        else:
            result[cat] = list(data['units'].keys())
    return jsonify(result)
