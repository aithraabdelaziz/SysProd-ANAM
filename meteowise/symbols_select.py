# Liste brute à traduire
ICONES_WEATHER = [
    "None", "clearsky_day", "clearsky_night", "clearsky_polartwilight", "cloudy", "fair_day", "fair_night",
    "fair_polartwilight", "fog", "heavyrain", "heavyrainandthunder", "heavyrainshowers_day", "heavyrainshowers_night",
    "heavyrainshowers_polartwilight", "heavyrainshowersandthunder_day", "heavyrainshowersandthunder_night",
    "heavyrainshowersandthunder_polartwilight", "heavysleet", "heavysleetandthunder", "heavysleetshowers_day",
    "heavysleetshowers_night", "heavysleetshowers_polartwilight", "heavysleetshowersandthunder_day",
    "heavysleetshowersandthunder_night", "heavysleetshowersandthunder_polartwilight", "heavysnow",
    "heavysnowandthunder", "heavysnowshowers_day", "heavysnowshowers_night", "heavysnowshowers_polartwilight",
    "heavysnowshowersandthunder_day", "heavysnowshowersandthunder_night", "heavysnowshowersandthunder_polartwilight", "lightrain",
    "lightrainandthunder", "lightrainshowers_day", "lightrainshowers_night", "lightrainshowers_polartwilight", "lightrainshowersandthunder_day",
    "lightrainshowersandthunder_night", "lightrainshowersandthunder_polartwilight", "lightsleet", "lightsleetandthunder",
    "lightsleetshowers_day", "lightsleetshowers_night", "lightsleetshowers_polartwilight", "lightsleetshowersandthunder_day",
    "lightsleetshowersandthunder_night", "lightsleetshowersandthunder_polartwilight", "lightsnow", "lightsnowandthunder",
    "lightsnowshowers_day", "lightsnowshowers_night", "lightsnowshowers_polartwilight", "lightsnowshowersandthunder_day",
    "lightsnowshowersandthunder_night", "lightsnowshowersandthunder_polartwilight", "np", "partlycloudy_day", "partlycloudy_night",
    "partlycloudy_polartwilight", "rain", "rainandthunder", "rainshowers_day", "rainshowers_night", "rainshowers_polartwilight",
    "rainshowersandthunder_day", "rainshowersandthunder_night", "rainshowersandthunder_polartwilight", "sleet", "sleetandthunder",
    "sleetshowers_day", "sleetshowers_night", "sleetshowers_polartwilight", "sleetshowersandthunder_day", "sleetshowersandthunder_night",
    "sleetshowersandthunder_polartwilight", "snow", "snowandthunder", "snowshowers_day", "snowshowers_night", "snowshowers_polartwilight",
    "snowshowersandthunder_day", "snowshowersandthunder_night", "snowshowersandthunder_polartwilight"
]

ICONES_WEATHER = ["np", "clearsky_day", "cloudy", "fair_day", 
    "fog","lightrain","rain", "heavyrain", "heavyrainandthunder", "heavyrainshowers_day", "rainshowers_day", 
    "heavyrainshowersandthunder_day", "rainandthunder",  "lightrainandthunder","lightrainshowers_day", 
    "heavysleet", "heavysleetandthunder", "heavysleetshowers_day", "heavysleetshowersandthunder_day",
    "lightrainshowersandthunder_day", "lightsleet", "lightsleetandthunder",
    "lightsleetshowers_day", "lightsleetshowersandthunder_day","partlycloudy_day",
    
    "rainshowersandthunder_day", "sleet", "sleetandthunder",
    "sleetshowers_day", "sleetshowersandthunder_day",


    "clearsky_night", "fair_night","heavyrainshowers_night","heavyrainshowersandthunder_night","heavysleetshowers_night", 
    "heavysleetshowersandthunder_night","lightrainshowers_night","lightrainshowersandthunder_night", 
    "lightsleetshowers_night","lightsleetshowersandthunder_night", "rainshowers_night", "rainshowersandthunder_night", 
    "sleetshowers_night", "partlycloudy_night", "sleetshowersandthunder_night","None"
]

# Fonction de traduction simple basée sur des règles heuristiques
def traduire_icone(nom):
    base = nom.replace("_polartwilight", " (crépuscule polaire) ") \
              .replace("_day", " (jour) ") \
              .replace("_night", " (nuit) ")
    base = base.replace("clearsky", "Ciel clair ") \
               .replace("cloudy", "Couvert ") \
               .replace("fair", "Éclaircies ") \
               .replace("fog", "Brouillard ") \
               .replace("heavyrain", "Pluie forte ") \
               .replace("heavysleet", "Verglas fort ") \
               .replace("heavysnow", "Neige forte ") \
               .replace("lightrain", "Pluie légère ") \
               .replace("lightsleet", "Verglas léger ") \
               .replace("lightsnow", "Neige légère ") \
               .replace("rain", "Pluie ") \
               .replace("sleet", "Verglas ") \
               .replace("snow", "Neige ") \
               .replace("showersandthunder", " orageux ") \
               .replace("showers", " averses ") \
               .replace("andthunder", " et tonnerre ") \
               .replace("np", "Non Parvenu ") \
               .replace("None", "Non Parvenu ") \
               .replace("partlycloudy", "Partiellement nuageux ") \
               .replace("thunder", " orages ")
    return base.strip().capitalize()


def generer_select_icones_weather():
    traductions = {nom: traduire_icone(nom) for nom in ICONES_WEATHER}
    traductions_sorted = traductions #dict(sorted(traductions.items()))
    

    options = []
    for key, label in traductions.items():
        options.append(
            f'<option value="{key}">{label} <img src="/media/weathericons/{key}.png" style="height:20px;vertical-align:middle;"/></option>'
        )
    return f'<select name="icone_weather">\n' + "\n".join(options) + '\n</select>'

# def render_weather_icon_select(name="weather_icon", selected=None):
#     traductions = {nom: traduire_icone(nom) for nom in ICONES_WEATHER}
#     traductions_sorted = dict(sorted(traductions.items()))
    
#     html = f'<select name="{name}">\n'
#     for icon in ICONES_WEATHER:
#         label = traductions_sorted.get(icon, icon.replace("_", " ").capitalize())
#         is_selected = ' selected' if selected == icon else ''
#         html += f'<option value="{icon}"{is_selected}>{label} <img src="/media/weathericons/{icon}.png" style="height:20px;vertical-align:middle;"/></option>'
#         # html += f'  <option value="{icon}"{is_selected}>{label}</option>\n'
#     html += '</select>'
#     return html

def render_weather_icon_select(name="weather_icon", selected=None):
    traductions = {nom: traduire_icone(nom) for nom in ICONES_WEATHER}
    traductions_sorted = traductions #dict(sorted(traductions.items()))

    selected_label = traductions_sorted.get(selected, selected or "Sélectionner")
    selected_icon = f"/media/weathericons/{selected}.png" if selected else "/media/weathericons/None.png"

    html = f"""
        <div class="custom-select-box" onclick="toggleWeatherOptions_{name}()" style="border:1px solid #ccc; padding:5px; cursor:pointer; width:250px;">
          <div id="selected_{name}">
            <img src="{selected_icon}" height="20" style="vertical-align:middle;"> {selected_label}
          </div>
        </div>
        <div id="options_{name}" style="display:none; border:1px solid #ccc; width:250px; max-height:200px; overflow-y:auto; position:absolute; background:white; z-index:10;">
        """
    for icon in traductions_sorted:
        label = traductions_sorted[icon]
        html += f"""
          <div onclick="selectWeatherOption_{name}('{icon}', '{label}', '/media/weathericons/{icon}.png')" style="padding:5px; cursor:pointer;">
            <img src="/media/weathericons/{icon}.png" height="20" style="vertical-align:middle;"> {label}
          </div>
        """

    html += f"""
        </div>
        <input type="hidden" name="{name}" id="input_{name}" value="{selected or ''}">
        <script>
          function toggleWeatherOptions_{name}() {{
            var el = document.getElementById('options_{name}');
            el.style.display = (el.style.display === 'none' || el.style.display === '') ? 'block' : 'none';
          }}

          function selectWeatherOption_{name}(value, label, iconUrl) {{
            document.getElementById('input_{name}').value = value;
            document.getElementById('selected_{name}').innerHTML = '<img src="' + iconUrl + '" height="20" style="vertical-align:middle;"> ' + label;
            document.getElementById('options_{name}').style.display = 'none';
          }}

          // Optionally hide on click outside
          document.addEventListener('click', function(e) {{
            if (!e.target.closest('.custom-select-box') && !e.target.closest('#options_{name}')) {{
              document.getElementById('options_{name}').style.display = 'none';
            }}
          }});
        </script>
        """
    return html
