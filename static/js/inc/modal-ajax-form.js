var $dialog = $(
    '<div id="modalForm" class="modal fade" data-backdrop="static" data-keyboard="false" tabindex="-1" role="dialog" aria-hidden="true" style="padding-top:15%; overflow-y:visible;">' +
    '<div class="modal-dialog">' +
    '<div class="modal-content">' +
        '<div class="modal-header">' +
            '<h5 class="modal-title" id="modalFormLabel"></h5>' +
            '<button type="button" class="close" data-dismiss="modal" aria-label="Cerrar"><span aria-hidden="true">&times;</span></button>' +
        '</div>' +
        '<div class="modal-body">' +
        '<div class="modal-body-form"></div>' +
        '</div>' +
        '<div class="modal-footer">' +
            '<button type="button" class="btn btn-primary" data-dismiss="modal">Aceptar</button>' +
            '<button type="button" class="btn btn-secondary" data-dismiss="modal">Cancelar</button>' +
        '</div>' +
    '</div></div></div>');
var $modal;

function load_ajax_form(url_form, target, modal_title, url_finish) {
    $(".modal").modal("hide");

    var custom_modal = target;

    $modal = custom_modal ? $(custom_modal) : $dialog;
    var $modal_body_form = $modal.find('.modal-body-form');
    var $ok_button = $modal.find('button.btn-primary');

    if (!custom_modal) {
        $modal.find(".modal-title").html(modal_title);
    } else {
        $modal.find(".modal-title").html("");
    }

    $modal.one('show.bs.modal', function (modal_show_event) {
        $( document ).ajaxError(function( event, jqxhr, settings, thrownError ) {
            // TODO: Quitar estas trazas una vez este estable el tema
            console.log(event);
            console.log(jqxhr);
            console.log(settings);
            console.log(thrownError);
            console.log("Error al cargar el contenido de : " + settings.url);
        });

        $modal_body_form.load(url_form + " .ajax-content", function(html) {
            var $ajax_content = $(html);
            var page_title = $(html).find(".form-title").text();
            $modal.find(".modal-title").text(page_title);

            if ($ajax_content.find(".modal-body-message").length > 0) {
                load_modal_message($modal, $ajax_content.find(".modal-body-message"));
            } else {
                $modal.find(".no-modal").hide();

                init_on_load_html(html);

                $modal_body_form.find('input').keydown(function(event){
                    if(event.keyCode == 13) {
                        event.preventDefault();

                        $modal.find('button.btn-primary').trigger( "click" );

                        return false;
                    }
                });
            }
        });

        $ok_button.off("click").on("click", function (e) {

            $ok_button.attr("disabled", true);
            // Para evitar que se manden muchos seguidos ^^^^
            e.preventDefault();
            var $form = $modal.find('form');
            var form_data = new FormData();

            if ($form.attr("enctype") == "multipart/form-data") {
                // OJO: Solo para mandar un archivo... si se tratara de un file
                // multiple hay que hacerlo de otra forma...
                // https://stackoverflow.com/questions/5392344/sending-multipart-formdata-with-jquery-ajax
                $form.find('input[type="file"]').each(function () {
                    var $file_input = $(this);
                    var file_list = $file_input[0].files;
                    if (file_list && file_list.length > 0) {
                        form_data.append($file_input.attr("name"), file_list[0]);
                    }
                });
            }

            var other_fields = $form.serializeArray();
            for (var i = 0; i < other_fields.length; i++) {
                form_data.append(other_fields[i].name, other_fields[i].value);
            }

            var form_action = $form.attr("action");

            if (!form_action) {
                form_action = url_form;
            }

            $.ajax({
                url: form_action,
                data: form_data,
                cache: false,
                contentType: false,
                processData: false,
                method: 'POST',
                type: 'POST',
                success: function(html){
                    on_success_submit(html, $modal, $ok_button, url_finish);
                }
            });
        });
    }).one("hide.bs.modal", function (modal_hide_event) {
        $modal.find('.modal-body-form').html("");
        $modal.find('.modal-footer').show();
        $ok_button.off("click").attr("disabled", false);
    }).modal("show");
}

function on_success_submit(html, $modal, $ok_button, url_finish) {
    var $content = $( html );
    var $modal_body_form = $modal.find('.modal-body-form');

    if ($content.find( ".non-field-errors" ).length > 0 || $content.find( ".field-errors" ).length) {
        $modal_body_form.html("").append($content.find("form")).find(".no-modal").hide();

        init_on_load_html(html);

        $modal_body_form.find('input[type="text"]').keydown(function(event){
            if(event.keyCode == 13) {
                event.preventDefault();
                return false;
            }
        });

        $ok_button.attr("disabled", false);
    } else if ($content.find(".modal-body-message").length > 0) {
        load_modal_message($modal, $content.find(".modal-body-message"));
    } else if (url_finish) {
        window.location = url_finish;
    } else {
        // No hacemos reload ya que en infinite se complica la cosa
        $modal.modal("hide");
    }
}

function load_modal_message($modal, $body_message) {
    $modal.find('.modal-footer').hide();
    $modal.find('.modal-body-form').html("").append($body_message);
}

function init_on_load_html(html) {
    // TODO: Cosas para hacer cuando cargue el contenido en el modal...
}

window.modal_ajax_form_init = function() {
    $(".modal-ajax-form").each(function (e) {
        var $data = $(this);
    
        $data.off("click").on("click", function (data_click) {
            data_click.preventDefault();
            
            load_ajax_form(
                $data.attr("href"), 
                $data.data("target"), 
                $data.text() ? $data.text() : $data.attr("title"), 
                $data.data("url-finish"));
        });
    });
}