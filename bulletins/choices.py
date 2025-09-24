from chartmet.utils import get_parameters, get_functions, get_parameters_decade
def get_model_choices():
    return [('gfs_model', 'GFS 0.25')]
def get_parametres_choices():
    return [
            (p["grib_variable"], p["parameter_name"])
            for p in get_parameters(schema='gfs_model').to_dict(orient='records')
        ]
def get_functions_choices():
    return [
            (f["function"], f["name"])
            for f in get_functions(schema='gfs_model').to_dict(orient='records')
        ]
def get_parametres_decades_choices():
    # from pprint import pprint
    # d = get_parameters_decade(schema='climat', table='parameters_decades').to_dict(orient='records')
    # pprint(d)
    return [
            (p['parameter'][0], p['parameter'][0])
            for p in get_parameters_decade(schema='climat', table='parameters_decades').to_dict(orient='records')
        ]