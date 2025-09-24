# vigilance/services.py

from .models import VigimetProvinceAuto

def get_vigilance_data(param, forecast_date):
    rows = VigimetProvinceAuto.objects.filter(param=param, forecast_date=forecast_date)
    data = []

    for row in rows:
        details = row.details
        data.append({
            'province_id': row.province_id,
            'province_name': row.province_name,
            'value': details.get('value'),
            'level': details.get('level'),
            'smin': details.get('smin'),
            'smax': details.get('smax'),
            'comment': details.get('comment'),
        })

    return data
