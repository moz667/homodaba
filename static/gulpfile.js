var gutils = require('./inc/utils');
var gulp = require('gulp');

/////////////
// OPTIONS //
/////////////

// enable extra debug information, when possible
var __DEBUG = true;
// enable sourcemaps for Browserify bundles and Sass
var __SOURCEMAPS = true;
// clean dist files before (re)builds
var __CLEAN = false;

///////////
// PATHS //
///////////

// SOURCE PATH OPTIONS
const __SRC_JS = [
    './js/main.js',
	'./js/kodi.js'
];
const __SRC_JS_THIRDPARTY = [
    './js/main.thirdparty.js'
];

// moz667: Solamente compilamos los archivos scss del sass que no empiecen
// por _
const __SRC_SASS = [
	'./css/main.scss'
];

const __SRC_SASS_THIRDPARTY = [
	'./css/main.thirdparty.scss'
];

// WATCH PATHS
const __WATCH_SASS = [
	'./css/*.scss',
	'./css/**/*.scss'
];

const __WATCH_SASS_THIRDPARTY = [
	'./css/*.thirdparty.scss',
	'./css/thirdparty/**/*.scss'
];

const __WATCH_JS = [
	'./js/*.js',
	'./js/**/*.js'
];

// DIST PATH OPTIONS
const __DIST = './build';
const __DIST_JS = __DIST + '/js';
const __DIST_CSS = __DIST + '/css';
const __DIST_FONT = __DIST + "/fonts";
const __DIST_IMG = __DIST + "/img";

const __COPY_FONT = [
    '@mdi/font/fonts/*'
];

/*
const __COPY_JS = [
	'file.js',
];
*/
const __COPY_IMG = [
    './img/**'
];

// Compile Sass
function sass_build(callback) {
	gutils.sass(__SRC_SASS, __DIST_CSS, callback);
}
gulp.task('sass', sass_build);

// Watch Sass
function sass_watch() {
	gutils.watch(__WATCH_SASS, function (callback) {
			sass_build(callback);
	});
}
gulp.task('sass:watch', sass_watch);

// Compile Sass
function sass_thirdparty_build(callback) {
	gutils.sass(__SRC_SASS_THIRDPARTY, __DIST_CSS, callback);
}
gulp.task('sass:thirdparty',sass_thirdparty_build);

// Watch Sass
function sass_thirdparty_watch() {
	gutils.watch(__WATCH_SASS_THIRDPARTY, function (callback) {
			sass_thirdparty_build(callback);
	});
}
gulp.task('sass:thirdparty:watch', sass_thirdparty_watch);

// Compile Browserify bundles
function browserify_build(callback) {
	gutils.compile_browserify(__SRC_JS, __DIST_JS, callback, true);
}
gulp.task('browserify', browserify_build);

function browserify_thirdparty_build(callback) {
    // OJO: Los thirdparty tienen que venir ya minimizados siempre
	gutils.compile_browserify(__SRC_JS_THIRDPARTY, __DIST_JS, callback, false);
}
gulp.task('browserify:thirdparty', browserify_thirdparty_build);

// Watch Browserify Bundles
function browserify_watch() {
	gutils.watch(__WATCH_JS, function (callback) {
			browserify_build(callback);
	});
}
gulp.task('browserify:watch', browserify_watch);

function browserify_thirdparty_watch() {
	gutils.watch(__SRC_JS_THIRDPARTY, function (callback) {
			browserify_thirdparty_build(callback);
	});
}
gulp.task('browserify:thirdparty:watch', browserify_thirdparty_watch);

// FONTS
function fonts_copy(callback) {
	gulp.src(__COPY_FONT, { cwd: 'node_modules/' })
		.pipe(gulp.dest(__DIST_FONT))
		.on('end', callback);
}
gulp.task('copy:fonts', fonts_copy);

/*
// JS
function copyjs_copy(callback) {
	gulp.src(__COPY_JS, { cwd: __SRC_JS })
 		.pipe(gulp.dest(__DIST_JS))
		.on('end', callback);
}
gulp.task('copy:copyjs', copyjs_copy);
*/

// IMGS
function imgs_copy(callback) {
	gulp.src(__COPY_IMG)
		.pipe(gulp.dest(__DIST_IMG))
		.on('end', callback);
}
gulp.task('copy:imgs', imgs_copy);

// Watchers
gulp.task('watch', function (callback) {
	sass_watch();
	sass_thirdparty_watch();
	browserify_watch();
	browserify_thirdparty_watch();
});

// Default
gulp.task( 'default', function (callback) {
	var finished = 0;
	var total = 2;

	var reportFinished = function () {
		finished++;
		// console.log(finished + '/' + total);
		if (finished == total) {
			callback();
		}
	};

	// Hemos sacado la generacion de thirdparty y la copia de fuentes porque
	// relentiza esta generacion y no cambia casi nunca...
	// hay que tenerlo en cuenta por lo que ponemos un mensaje comentandolo
	sass_build(reportFinished);
	// sass_thirdparty_build(reportFinished);
	browserify_build(reportFinished);
	// browserify_thirdparty_build(reportFinished);
	// fonts_copy(reportFinished);
    /*
    copyjs_copy(reportFinished);
	imgs_copy(reportFinished);
    */
	console.log("*****************************");
	console.log("OJO: No generamos ni thirdparty js ni thirdparty css ni copiamos fuentes...");
	console.log("Para poder hacer esto tendriamos que ejecutar:");
	console.log("# gulp browserify:thirdparty");
	console.log("# gulp sass:thirdparty");
	console.log("# gulp copy:fonts");
	console.log("*****************************");
});
