def exclude_wagtail_admin_views(endpoints):
    """
    Filtre les endpoints pour exclure ceux de l'API admin Wagtail
    en détectant le préfixe des urls admin : /admin/api/
    """
    filtered = []
    for path, path_regex, method, view in endpoints:
        if not path.startswith('/admin/api/'):
            filtered.append((path, path_regex, method, view))
    return filtered