 setTimeout(function() {
            var geojsonLayer = null;
            var foliumMap = null;
            const param = window.vigilanceContext?.param;
            const forecastDate = window.vigilanceContext?.forecast_date;

            // On récupère la couche GeoJson après création de la carte
            for (var key in window) {
                if (window.hasOwnProperty(key)) {
                    var obj = window[key];
                    if (obj && obj instanceof L.Map) {
                        obj.eachLayer(function(layer) {
                            if (layer instanceof L.GeoJSON) {
                                geojsonLayer = layer;
                            }
                            if (obj instanceof L.Map) {
                                foliumMap = obj;
                            }
                        });
                    }
                }
            }

            jQuery(document).ready(function() {
                jQuery(document).on('click', '.save-btn', function(e) {
                    e.preventDefault();
                    var $popup = jQuery(this).closest('.popup-content');
                    var provinceId = $popup.find('.color-buttons-container').data('province-id');
                    var vigilance = $popup.find('.color-btn.selected').data('level');
                    var comment = $popup.find('.comment-textarea').val();
                    var val = $popup.find('#val').val();
                    var start_datetime = $popup.find('#start-datetime').val();
                    var end_datetime = $popup.find('#end-datetime').val();
                    var zone = $popup.find('#zone').val();
                    var param = $('.param').val();
                    var forecast_date = $('.forecast_date').val();
                    console.log(param);

                    jQuery.ajax({
                        url: '/vigilance/edit_vigilance/',
                        type: 'POST',
                        contentType: 'application/json',
                        headers: {'X-CSRFToken': getCookie('csrftoken')},
                        data: JSON.stringify({
                            province_id: provinceId,
                            vigilance: vigilance,
                            comment: comment,
                            param: param,
                            forecast_date: forecast_date,
                            val: val,
                            start_datetime: start_datetime,
                            end_datetime: end_datetime,
                            zone: zone,
                            status: 2
                        }),
                        success: function(response) {
                            $popup.find('.status-msg').text("Données enregistrées avec succès.").css("color", "green");
                            
                            if (geojsonLayer) {
                                geojsonLayer.eachLayer(function(layer) {
                                    if (layer.feature && layer.feature.properties && layer.feature.properties.province_id == provinceId) {
                                        if(vigilance==0){
                                            layer.setStyle({fillColor: '#00FF00'});
                                        }else if(vigilance==1){
                                            layer.setStyle({fillColor: '#FFFF00'});
                                        }else if(vigilance==2){
                                            layer.setStyle({fillColor: '#FFA500'});
                                        }else if(vigilance==3){
                                            layer.setStyle({fillColor: '#FF0000'});
                                        }
                                    }
                                });
                            }
                        },
                        error: function() {
                            $popup.find('.status-msg').text("Erreur lors de l'enregistrement.").css("color", "red");
                        }
                    });
                });
foliumMap.on('draw:created', function(e) {
    var layer = e.layer;
    layer.addTo(foliumMap);

    var popupContent = `
        <div class="popup-content" data-zone-id="custom">
            <div>
                <label><b>Zone:</b></label>
                <input type="text" class="editable-value" id="zone" value="Zone personnalisée">
            </div>  
            <div>
                <label><b>Valeur:</b></label>
                <input type="text" class="editable-value" id="value" value="0.0"/>
            </div>            
            <div>
                <label><b>Date début:</b></label>
                <input type="datetime-local" class="start-datetime editable-value" id="start-datetime" value="">
            </div>
            
            <div>
                <label><b>Date fin:</b></label>
                <input type="datetime-local" class="end-datetime editable-value" id="end-datetime" value="">
            </div>
            <div class="color-buttons-container" data-zone-id="custom">
                <div class="color-btn" style="background-color: #00FF00;" data-level="0" title="Niveau 0"></div>
                <div class="color-btn" style="background-color: #FFFF00;" data-level="1" title="Niveau 1"></div>
                <div class="color-btn" style="background-color: #FFA500;" data-level="2" title="Niveau 2"></div>
                <div class="color-btn" style="background-color: #FF0000;" data-level="3" title="Niveau 3"></div>
            </div>

            <textarea id="comment" class="comment-textarea" placeholder="Ajouter un commentaire..."></textarea>
            <button class="save-btn-personalized">Enregistrer</button>
            <div class="status-msg"></div>
        </div>
    `;

    layer.bindPopup(popupContent).openPopup();

    // Sélection de couleur
    layer.getPopup().getElement().querySelectorAll('.color-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            layer.getPopup().getElement().querySelectorAll('.color-btn').forEach(b => b.classList.remove('selected'));
            this.classList.add('selected');
        });
    });

    // Enregistrement
    layer.getPopup().getElement().querySelector('.save-btn-personalized').addEventListener('click', function() {
        var popupEl = layer.getPopup().getElement();
        var selectedBtn = popupEl.querySelector('.color-btn.selected');
        var zone = $(popupEl).find('#zone').val();
        var value = $(popupEl).find('#value').val();
        var startdatetime = $(popupEl).find('#start-datetime').val();
        var enddatetime = $(popupEl).find('#end-datetime').val();
        var vigilanceColor = selectedBtn ? selectedBtn.style.backgroundColor : '#00FF00'; // par défaut : vert
        var level = selectedBtn ? selectedBtn.dataset.level : '0'; // data-level
        var comment = $(popupEl).find('#comment').val();

        layer.setStyle({
            fillColor: vigilanceColor,
            fillOpacity: 1,
            color: 'black',
            weight: 2
        });

        layer.closePopup();
function refreshGeoJsonMap(forecastDate, param) {

            foliumMap.removeLayer(layer);
        
    $.ajax({
        url: '/vigilance/get_vigilance/',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({
            forecastDate: forecastDate,
            param: param
        }),
        success: function(data) {
            console.log('GeoJSON reçu:', data);

            // Supprimer l'ancien calque s’il existe
            if (typeof geojsonLayer !== 'undefined' && foliumMap.hasLayer(geojsonLayer)) {
                foliumMap.removeLayer(geojsonLayer);
            }

            // Ne garder que les polygones
            const polygonFeatures = {
                type: "FeatureCollection",
                features: data.features.filter(f =>
                    f.geometry.type === "Polygon" || f.geometry.type === "MultiPolygon"
                )
            };

            // Fonction pour choisir la couleur selon le niveau
            function getColorByLevel(level) {
                console.log(level)
                switch (level) {
                    case 0: return '#00FF00'; // vert
                    case 1: return '#FFFF00'; // jaune
                    case 2: return '#FFA500'; // orange
                    case 3: return '#FF0000'; // rouge
                    default: return 'blue'; // gris (inconnu)
                }
            }

            // Ajouter le nouveau calque
            geojsonLayer = L.geoJSON(polygonFeatures, {
                style: function (feature) {
                    var level = parseInt(feature.properties.details?.level || 0);
                    console.log(level,feature)
                    return {
                        color: '#000000',
                        weight: 1,
                        opacity: 1,
                        fillColor: getColorByLevel(level),
                        fillOpacity: 1
                    };
                }
            }).addTo(foliumMap);

            // Zoom sur les polygones
            if (geojsonLayer.getBounds().isValid()) {
                foliumMap.fitBounds(geojsonLayer.getBounds());
            }
        },
        error: function(xhr, status, error) {
            console.error('Erreur lors de la récupération du GeoJSON:', error);
        }
    });
}
        var drawnGeoJSON = layer.toGeoJSON();
jQuery.ajax({
                        url: '/vigilance/add_vigilance/',
                        type: 'POST',
                        contentType: 'application/json',
                        headers: {'X-CSRFToken': getCookie('csrftoken')},
                        data: JSON.stringify({
                            forecastDate: forecastDate,
                            param: param,
                            geom: drawnGeoJSON.geometry,
                            level: level,
                            value: value,
                            zone: zone,
                            startdatetime: startdatetime,
                            enddatetime: enddatetime,
                            comment: comment,
                            status: 1
                        }),
                        success: function(response) {
                            
                        },
                        error: function() {
                            $popup.find('.status-msg').text("Erreur lors de l'enregistrement.").css("color", "red");
                        }
                    });
    });
});





            });
            jQuery(document).on('click', '.color-btn', function() {
                var $this = jQuery(this);
                var $container = $this.closest('.color-buttons-container');
                $container.find('.color-btn').removeClass('selected');
                $this.addClass('selected');
            });

            function getCookie(name) {
                let cookieValue = null;
                if (document.cookie && document.cookie !== '') {
                    let cookies = document.cookie.split(';');
                    for (let i = 0; i < cookies.length; i++) {
                        let cookie = cookies[i].trim();
                        if (cookie.substring(0, name.length + 1) === (name + '=')) {
                            cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                            break;
                        }
                    }
                }
                return cookieValue;
            }
        }, 1000);