# ==============================================================
# Age Calculator Route
# POST /api/age/calculate  → { dob } → exact age breakdown
# ==============================================================

from flask import Blueprint, request, jsonify
from datetime import date, datetime

age_bp = Blueprint('age', __name__)

@age_bp.route('/calculate', methods=['POST'])
def calculate():
    data = request.get_json()
    dob_str = (data or {}).get('dob', '').strip()

    if not dob_str:
        return jsonify({'error': 'Date of birth provide karein (YYYY-MM-DD)'}), 400

    try:
        dob   = datetime.strptime(dob_str, '%Y-%m-%d').date()
        today = date.today()

        if dob > today:
            return jsonify({'error': 'Date of birth future mein nahi ho sakti'}), 400

        # Years
        years = today.year - dob.year
        if (today.month, today.day) < (dob.month, dob.day):
            years -= 1

        # Months since last birthday
        bday_this_year = dob.replace(year=today.year if (today.month, today.day) >= (dob.month, dob.day) else today.year - 1)
        months_total   = (today.year - dob.year) * 12 + (today.month - dob.month)
        if today.day < dob.day:
            months_total -= 1

        months = months_total % 12

        # Days since last month-anniversary
        try:
            last_month_ann = today.replace(day=dob.day)
        except ValueError:
            import calendar
            last_day = calendar.monthrange(today.year, today.month)[1]
            last_month_ann = today.replace(day=min(dob.day, last_day))

        if last_month_ann > today:
            if today.month == 1:
                prev_month = today.replace(year=today.year-1, month=12)
            else:
                prev_month = today.replace(month=today.month-1)
            try:
                last_month_ann = prev_month.replace(day=dob.day)
            except ValueError:
                import calendar
                last_day = calendar.monthrange(prev_month.year, prev_month.month)[1]
                last_month_ann = prev_month.replace(day=min(dob.day, last_day))

        days = (today - last_month_ann).days

        # Total calculations
        total_days   = (today - dob).days
        total_weeks  = total_days // 7
        total_months = months_total
        total_hours  = total_days * 24
        total_mins   = total_hours * 60

        # Next birthday
        try:
            next_bday = dob.replace(year=today.year)
        except ValueError:
            next_bday = dob.replace(year=today.year, day=28)
        if next_bday <= today:
            try:
                next_bday = dob.replace(year=today.year + 1)
            except ValueError:
                next_bday = dob.replace(year=today.year + 1, day=28)
        days_to_bday = (next_bday - today).days

        return jsonify({
            'years':          years,
            'months':         months,
            'days':           days,
            'total_days':     total_days,
            'total_weeks':    total_weeks,
            'total_months':   total_months,
            'total_hours':    total_hours,
            'total_minutes':  total_mins,
            'next_birthday':  next_bday.strftime('%B %d, %Y'),
            'days_to_birthday': days_to_bday,
            'birth_weekday':  dob.strftime('%A'),
            'today':          today.strftime('%B %d, %Y'),
        })

    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500
