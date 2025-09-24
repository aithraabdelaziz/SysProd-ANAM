"""from django import template

register = template.Library()

@register.simple_tag
def get_item(dictionary, key):
    return dictionary.get(key)
"""

from django import template
from django.template.defaultfilters import stringfilter
from datetime import timedelta
register = template.Library()

@register.filter
@stringfilter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter(name='add_days')
def add_days(value, n_days):
    if value and isinstance(n_days, int):
        return value + timedelta(days=n_days)
    return value

@register.filter
def replace_none(value, replacement="-"):
    if value in [None, "None", "null", "", " "]:
        return replacement
    return value

@register.filter
def getV(d, key):
    return d.get(key)


from bs4 import BeautifulSoup
import re


@register.filter
def html_to_whatsapp(text):
    soup = BeautifulSoup(text, "html.parser")

    # Supprimer les balises vides ou redondantes
    for tag in soup.find_all():
        if tag.name in ["strong", "b", "em", "i", "s", "code"] and not tag.text.strip():
            tag.decompose()

    def apply_style(tag_names, symbol):
        for tag in soup.find_all(tag_names):
            if tag.string and tag.string.strip():  # Ne pas styliser vide
                tag.string.replace_with(f"{symbol}{tag.string}{symbol}")
            else:
                # Pour le contenu complexe : utiliser wrap
                tag.insert_before(symbol)
                tag.insert_after(symbol)

    apply_style(["b", "strong"], "*")
    apply_style(["i", "em"], "_")
    apply_style(["s"], "~")
    apply_style(["code"], "`")

    # Titres (mise en forme simple)
    for tag in soup.find_all(["h1", "h2", "h3"]):
        tag.insert_before("\n\n*")
        tag.insert_after("*\n")
    for tag in soup.find_all(["h4", "h5", "h6"]):
        tag.insert_before("\n_")
        tag.insert_after("_\n")

    # Paragraphes, sauts de ligne, blocs
    for tag in soup.find_all(["p", "div", "br"]):
        tag.insert_before("\n")
        tag.insert_after("\n")

    # Listes
    for li in soup.find_all("li"):
        li.insert_before("- ")
        li.insert_after("\n")
    for tag in soup.find_all(["ul", "ol"]):
        tag.insert_before("\n")
        tag.insert_after("\n")

    # Liens : texte suivi de l’URL
    for tag in soup.find_all("a"):
        href = tag.get("href", "")
        if href and tag.text:
            tag.insert_after(f" ({href})")

    result = soup.get_text()

    # Nettoyage des doublons de styles
    result = re.sub(r'(\*{2,})', '*', result)
    result = re.sub(r'(_{2,})', '_', result)
    result = re.sub(r'(~{2,})', '~', result)
    result = re.sub(r'(`{2,})', '`', result)

    # Nettoyage des multiples sauts de ligne
    result = re.sub(r'\n{3,}', '\n\n', result)

    # Nettoyage d’espaces superflus autour des styles
    result = re.sub(r'([*_~`])\s+([^\s])', r'\1\2', result)
    result = re.sub(r'([^\s])\s+([*_~`])', r'\1\2', result)

    return result.strip()