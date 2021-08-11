(function(){function r(e,n,t){function o(i,f){if(!n[i]){if(!e[i]){var c="function"==typeof require&&require;if(!f&&c)return c(i,!0);if(u)return u(i,!0);var a=new Error("Cannot find module '"+i+"'");throw a.code="MODULE_NOT_FOUND",a}var p=n[i]={exports:{}};e[i][0].call(p.exports,function(r){var n=e[i][1][r];return o(n||r)},p,p.exports,r,e,n,t)}return n[i].exports}for(var u="function"==typeof require&&require,i=0;i<t.length;i++)o(t[i]);return o}return r})()({1:[function(require,module,exports){
$(document).ready(function () {
    kodi_init();
});

window.kodi_init = function () {
    $(".btn-kodi-play").each(function () {
        var $this = $(this);
        $this.off("click").on("click", function () {
            var url_kodi_hosts = $this.data("kodi-hosts-url");
            var storage_path = $this.data("storage-path");
            var url_play = $this.data("play-url");

            $.ajax({
                method: "GET",
                url: url_kodi_hosts
            }).done(function( data ) {
                console.log( data );
                if (data && data["kodi_hosts"] && data["kodi_hosts"].length > 0) {
                    var $dialog = $(
                        '<div id="kodiPlayDialog" class="modal fade" data-backdrop="static" data-keyboard="false" tabindex="-1" role="dialog" aria-hidden="true">' +
                        '<div class="modal-dialog">' +
                        '<div class="modal-content">' +
                            '<div class="modal-header">' +
                                '<button type="button" class="close" data-dismiss="modal" aria-label="Cerrar"><span aria-hidden="true">&times;</span></button>' +
                            '</div>' +
                            '<div class="modal-body"><div class="list-group"></div></div>' +
                        '</div></div></div>'
                    );

                    var kodi_hosts = data["kodi_hosts"];
                    for (var i = 0; i < kodi_hosts.length; i++) {
                        var kodi_host = kodi_hosts[i];

                        $dialog.find(".modal-body .list-group").append(
                            $('<button type="button" class="list-group-item list-group-item-action"></button>').text(
                                kodi_host["name"]
                            ).data(
                                // PROBLEMA CON CORS EN KODI "url", kodi_host["jsonrpc_url"]
                                "host-id", kodi_host["id"]
                            ).on("click", function () {
                                var $this_btn = $(this);

                                $.ajax({
                                    url: url_play, 
                                    data: { 
                                        "host_id": $this_btn.data("host-id"), 
                                        "storage_path": storage_path
                                    }, 
                                    type:"GET",
                                    success: function (result) { 
                                        $dialog.modal("hide");
                                        console.log(result);
                                    },
                                    error: function (err, status, thrown) {
                                        alert("Error al enviar el medio a kodi.");
                                        console.log(err);
                                        console.log(status);
                                        console.log(thrown);
                                    }
                                });

                                /* 
                                PROBLEMA CON CORS EN KODI : (no podemos hacer esto ya que kodi no tiene modo de establecer politicas de cors)
                                $.ajax({
                                    url: $this_btn.data("url"), 
                                    data: JSON.stringify({ 
                                        "id": 1, 
                                        "jsonrpc": "2.0", 
                                        "method": "Player.Open", 
                                        "params": {
                                            "item": {
                                                "file": storage_path
                                            }
                                        }
                                    }), 
                                    type:"POST",
                                    dataType:"json",
                                    success: function (result) { 
                                        $dialog.modal("hide");
                                        console.log(result);
                                    },
                                    error: function (err, status, thrown) {
                                        alert("Error al enviar el medio a kodi.");
                                        console.log(err);
                                        console.log(status);
                                        console.log(thrown);
                                    }
                                });
                                */
                            })
                        );
                    }
                    
                    $dialog.modal("show");
                }
            });

            console.log(url_kodi_hosts + " " + storage_path);
        });
    });
};
},{}]},{},[1])

//# sourceMappingURL=kodi.js.map
