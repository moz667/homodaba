// TODO: UTILIZANDO MIN NO FUNCIONA MODAL DE BS!!!
window.$ = window.jQuery = require('jquery');

// Bootstrap
window.Popper = require('popper.js');
require('bootstrap/dist/js/bootstrap');

// Lib para jugar con fechas y horas y humanize
window.moment = require('moment/min/moment-with-locales');
window.moment.locale($("html").attr("lang"));

// Infinite scroll
window.InfiniteScroll = require('infinite-scroll');