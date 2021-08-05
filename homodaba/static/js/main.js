$(document).ready(function () {
    var $body = $("body");
    var body_classes = $body.attr("class").split(" ")

    // Activar opcion del menu en base a las clases de $body
    $("#main-navbar .nav-item").removeClass("active");
    for (var i in body_classes) {
        $("#main-navbar ." + body_classes[i]).addClass("active");
    }

    user_tag_switcher_init();
});

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