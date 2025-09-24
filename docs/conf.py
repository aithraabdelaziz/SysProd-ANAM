# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
import os
import sys
import django

# Ajouter le chemin vers la racine du projet
sys.path.insert(0, os.path.abspath('../'))  # ../ = dossier du projet

# Configuration Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "climforge.settings")
django.setup()

project = 'SysProd'
copyright = '2025, ANAM-OMM'
author = 'ANAM-OMM'
release = '0.1'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',
    'sphinx.ext.autosummary',
]

autosummary_generate = True

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store', '**/migrations/**']
language = 'fr'

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

