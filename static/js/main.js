require("./inc/modal-ajax-form");

$(document).ready(function () {
    var $body = $("body");
    var body_classes = $body.attr("class").split(" ")

    // Activar opcion del menu en base a las clases de $body
    $("#main-navbar .nav-item").removeClass("active");
    for (var i in body_classes) {
        $("#main-navbar ." + body_classes[i]).addClass("active");
    }

    $('[data-toggle="tooltip"]').tooltip();

    user_tag_switcher_init();
    copy_storage_types_init();
    show_more_init();
    modal_ajax_form_init();

    window.setTimeout(resize_storage_types_info_init, 500);

    // init Infinite Scroll
    /*
    $('.search-results').infiniteScroll({
        path: '.pagination__next',
        append: '.movie-item',
        status: '.scroller-status',
        hideNav: '.pagination',
    });
    */

    if ($(".pagination").length) {
        var elem = document.querySelector('.search-results');
        var infScroll = new InfiniteScroll( elem, {
            // options
            path: '.pagination__next',
            append: '.movie-item',
            history: false,
        });

        if (infScroll) {
            $(".pagination").hide();
            infScroll.on( 'append', function( body, path, items, response ) {
                user_tag_switcher_init();
                copy_storage_types_init();
                resize_storage_types_info_init();
                // Un poco nyapa... :P
                if (window.kodi_init) {
                    window.kodi_init();
                }
                show_more_init();
                modal_ajax_form_init();
            });
        }
    }
});

function show_more_init() {
    $(".show-more").off("click").on("click", function () {
        var $this = $(this);

        $this.hide();
        $($this.data("selector")).show();
    });
}

function copy_storage_types_init() {
    $(".storage-types textarea.storage-type-info").off("focus").on("focus", function () {
        $(this).select();
    });
    
    $(".storage-types .storage-type-item").each(function () {
        var $btn_copy = $(this).find(".btn-copy");
        var $textarea = $(this).find("textarea.storage-type-info");
        var $btn_open_url = $(this).find(".btn-open-url");

        $btn_copy.off("click").on("click", function () {
            $textarea.focus();
            $textarea.select();

            try {
                var successful = document.execCommand('copy');
                var msg = successful ? 'successful' : 'unsuccessful';
                console.log('Copying text command was ' + msg);
              } catch (err) {
                console.log('Oops, unable to copy');
              }
        });

        $btn_open_url.off("click").on("click", function () {
            window.open($btn_open_url.data("url"), '_blank');
        });
    });
}

function resize_storage_types_info_init() {
    $(".storage-types textarea.storage-type-info").each(function () {
        if (!$(this).data("fixed")) {
            $(this).css("height", $(this).prop("scrollHeight") + 8 + "px");
            $(this).data("fixed", true);
        }
    });
}

function user_tag_switcher_init() {
    $(".user-tag-switcher").each(function () {
        var $link = $(this);
        var icon_on = $link.data("icon-on");
        var icon_off = $link.data("icon-off");

        $link.off("click").on("click", function () {
            $.ajax({
                method: "GET",
                url: $link.data("url")
            }).always(function() {
                var $icon = $link.find("em");

                if ($icon.hasClass(icon_on)) {
                    $icon.removeClass(icon_on).addClass(icon_off);
                } else {
                    $icon.removeClass(icon_off).addClass(icon_on);
                }
            });
        })
    });
}