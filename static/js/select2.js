$(document).ready(function() {
    $('.select2').select2({
        width: '100%',
        placeholder: 'Select options',
        allowClear: true,
        templateSelection: function (data, container) {
            var $container = $(container);
            var selectedOptions = $(data.element).parent().find(':selected');
            var text = '';

            if (selectedOptions.length > 3) {
                var firstOption = $(selectedOptions[0]).text();
                text = '-';
                // $container.attr('title', 'Selected: ' + selectedOptions.map(function (i, el) {
                //     return $(el).text();
                // }).get().join(', '));
            } else {
                text = $(data.element).text();
            }
            // alert($container.html());
            return text;
        }
    });
});

$(document).ready(function() {
    $('#datepicker').datepicker({
      dateFormat: 'yy-mm-dd',  // Format ISO pour la date
       maxDate: 0
    });
  });

$(document).ready(function() {
    $('#id_geographic_areas').select2({
        templateResult: function(state) {
            // Vérifie si l'élément a l'attribut "data-category"
            if (!state.id) {
                return state.text; // retourne le texte par défaut pour les optgroups
            }

            var category = $(state.element).data('category');
            var $state = $(state.element);
            
            // Crée un élément avec un style personnalisé
            var $result = $('<span></span>');
            $result.text(state.text);

            // Modifie la taille de la police pour la catégorie
            if (category) {
                $result.prepend('<span style="font-size: 0.8em; color: gray;">(' + category + ') </span>');
            }

            return $result;
        }
    });
});