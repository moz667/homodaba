(function(){function r(e,n,t){function o(i,f){if(!n[i]){if(!e[i]){var c="function"==typeof require&&require;if(!f&&c)return c(i,!0);if(u)return u(i,!0);var a=new Error("Cannot find module '"+i+"'");throw a.code="MODULE_NOT_FOUND",a}var p=n[i]={exports:{}};e[i][0].call(p.exports,function(r){var n=e[i][1][r];return o(n||r)},p,p.exports,r,e,n,t)}return n[i].exports}for(var u="function"==typeof require&&require,i=0;i<t.length;i++)o(t[i]);return o}return r})()({1:[function(require,module,exports){
$(document).ready(function () {
    var $body = $("body");
    var body_classes = $body.attr("class").split(" ")

    // Activar opcion del menu en base a las clases de $body
    $("#main-navbar .nav-item").removeClass("active");
    for (var i in body_classes) {
        $("#main-navbar ." + body_classes[i]).addClass("active");
    }

    user_tag_switcher_init();
    copy_storage_types_init();

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

    var elem = document.querySelector('.search-results');
    var infScroll = new InfiniteScroll( elem, {
        // options
        path: '.pagination__next',
        append: '.movie-item',
        history: false,
    });

    infScroll.on( 'append', function( body, path, items, response ) {
        user_tag_switcher_init();
        copy_storage_types_init();
        resize_storage_types_info_init();
    });
});

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

        $link.off("click").on("click", function () {
            $.ajax({
                method: "GET",
                url: $link.data("url")
            }).always(function() {
                var $icon = $link.find("em");

                if ($icon.hasClass("mdi-star")) {
                    $icon.removeClass("mdi-star").addClass("mdi-star-outline");
                } else {
                    $icon.removeClass("mdi-star-outline").addClass("mdi-star");
                }
            });
        })
    });
}
},{}]},{},[1])

//# sourceMappingURL=main.js.map
