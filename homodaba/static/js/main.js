$(document).ready(function () {
    var $body = $("body");
    var body_classes = $body.attr("class").split(" ")

    // Activar opcion del menu en base a las clases de $body
    $("#main-navbar .nav-item").removeClass("active");
    for (var i in body_classes) {
        $("#main-navbar ." + body_classes[i]).addClass("active");
    }
});
