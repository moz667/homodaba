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

var del = require('del');
var $ = require('gulp-load-plugins')();
var browserify = require('browserify');
var watchify = require('watchify');
var source = require('vinyl-source-stream');
var buffer = require('vinyl-buffer');
var globby = require('globby');
var path = require('path');
var assign = require('lodash.assign');

const colors = require('ansi-colors');
var log = require('fancy-log');

var prettyHrtime = require('pretty-hrtime');
var _startTime;

class BundleLogger {
	constructor(action, filename, path, color) {
		this.startTime = process.hrtime();
		this.action = action;
		// console.log(filename);
		this.filepath = filename + (path != undefined && path ? " → " + path : "");
		this.color = color;

		log.info('INI (' + this.action + ') ' + this.color(this.filepath) + ' ...');
	}

	end(text) {
		var taskTime = process.hrtime(this.startTime);
		var prettyTime = prettyHrtime(taskTime);

		if (text != undefined && text) {
			log.info('MSG (' + this.action + ') ' + this.color(text));
		}

		log.info('FIN (' + this.action + ') ' + this.color.bold(this.filepath) + ' in ' + colors.magenta(prettyTime));
	}
}

module.exports = {

	/////////////////
	/////////////////

	warning_svn_del: function () {
		console.log("****************************************************************");
		console.log("*  OJO!!! para borrar correctamente hay que borrar de repo!!!  *");
		console.log("****************************************************************");
	},

	////////////////
	// SASS TASKS //
	////////////////

	sass: function (src, dist, callback) {
		var bundleLoggerSass = new BundleLogger("sass build", src, dist, colors.cyan);

		return gulp.src(src)
			// (optional) sourcemaps
			.pipe($.sourcemaps.init())
			// Compile Sass
			.pipe($.sass({
				// Resolve Sass file imports from node_modules
				importer: require('sass-importer-npm')
			})
			// Handle errors
			.on('error', $.sass.logError))
			// Post CSS
			.pipe($.postcss([
				// autoprefixer
				require('autoprefixer')({ overrideBrowserslist: ['last 2 versions'] })
			]))
			// also save non minified version
			.pipe($.rename({ extname: '.css' }))
			.pipe(gulp.dest(dist))
			// (optional) Write .map file
			.pipe($.sourcemaps.write('./'))
			// Write CSS file
			.pipe(gulp.dest(dist))
			.on('end', function () {
				bundleLoggerSass.end();
				if (callback != undefined) {
					callback();
				}
			});
		/*
		TODO: El map minimizado no funciona asi que quitamos por ahora la generacion
		del minimizado y el mapa del mismo

		return gulp.src(src)
			// (optional) sourcemaps
			.pipe($.sourcemaps.init())
			// Compile Sass
			.pipe($.sass({
				// Resolve Sass file imports from node_modules
				importer: require('sass-importer-npm')
			})
			// Handle errors
			.on('error', $.sass.logError))
			// Post CSS
			.pipe($.postcss([
				// autoprefixer
				require('autoprefixer')({ browsers: ['last 2 versions'] })
			]))
			// (optional) Minify CSS
			.pipe($.rename({ extname: '.min.css' }))
			.pipe($.cleanCss())
			// (optional) Write .map file
			.pipe($.sourcemaps.write('./'))
			// Write CSS file
			.pipe(gulp.dest(dist))
			*/
	},

	////////////////
	// BROWSERIFY //
	////////////////

	compile_browserify: function (src, dist, callback, _uglify) {
		globby(src).then(function (bundles) {

			var bundleQueue = bundles.length * 2;
			bundles = bundles.map(function (bundle) {
				return {
					src: bundle,
					dest: dist,
					// queue: bundles.length * 2,
					bundleName: path.basename(bundle),
					uglify: _uglify
				}
			});

			var browserifyThis = function (bundleConfig) {
				var opts = assign({}, watchify.args, {
					// Specify the entry point of your app
					entries: bundleConfig.src,
					// Enable source maps!
					debug: __DEBUG,
					paths: [
						// TODO: Esto de __dirname no parece que este bien... investigar
						// Resolve files from node_modules
						path.resolve(__dirname, 'node_modules')
					]
				});

				// Log when bundling starts
				var bundleLogger = new BundleLogger(
					"js build",
					bundleConfig.bundleName,
					bundleConfig.dest,
					colors.green
				);

				var bundler = browserify(opts);

				var bundle = function () {
					bundler
						.bundle()
						// Report compile errors
						.on('error', log.error)
						// Use vinyl-source-stream to make the
						// stream gulp compatible. Specifiy the
						// desired output filename here.
						.pipe(source(bundleConfig.bundleName))
						// buffer file contents
						.pipe(buffer())
						// (optional) sourcemaps
						// loads map from browserify file
						.pipe($.sourcemaps.init({ loadMaps: true }))
						.pipe($.rename({ extname: '.js' }))
						// (optional) Write .map file
						.pipe($.sourcemaps.write('./'))
						// Write JS file
						.pipe(gulp.dest(bundleConfig.dest))
						.on('end', reportFinished);

					var current_pipe = bundler
						.bundle()
						// Report compile errors
						.on('error', log.error)
						// Use vinyl-source-stream to make the
						// stream gulp compatible. Specifiy the
						// desired output filename here.
						.pipe(source(bundleConfig.bundleName))
						// buffer file contents
						.pipe(buffer())
						// (optional) sourcemaps
						// loads map from browserify file
						.pipe($.sourcemaps.init({ loadMaps: true }))
						// Add transformation tasks to the pipeline here.
						// (optional) Minify JS
						.pipe($.rename({ extname: '.min.js' }));

					if (bundleConfig.uglify) {
						current_pipe = current_pipe.pipe($.uglify());
					}

					return current_pipe
						.pipe($.sourcemaps.write('./'))
						// Write JS file
						.pipe(gulp.dest(bundleConfig.dest))
						.on('end', reportFinished);
/*
					return bundler
						.bundle()
						// Report compile errors
						.on('error', log.error)
						// Use vinyl-source-stream to make the
						// stream gulp compatible. Specifiy the
						// desired output filename here.
						.pipe(source(bundleConfig.bundleName))
						// buffer file contents
						.pipe(buffer())
						// (optional) sourcemaps
						// loads map from browserify file
						.pipe($.sourcemaps.init({ loadMaps: true }))
						// Add transformation tasks to the pipeline here.
						// (optional) Minify JS
						.pipe($.rename({ extname: '.min.js' }))
						// .pipe($.uglify())
						// (optional) Write .map file
						.pipe($.sourcemaps.write('./'))
						// Write JS file
						.pipe(gulp.dest(bundleConfig.dest))
						.on('end', reportFinished)
*/
				};

				if (global.__WATCHING) {
					// Wrap with watchify and rebundle on changes
					bundler = watchify(bundler);
					// Rebundle on update
					bundler.on('update', bundle);
				}

				var reportFinished = function () {
					// Log when bundling completes
					bundleLogger.end();

					if (bundleQueue) {
						bundleQueue --;
						if (bundleQueue === 0) {
							/*
							console.log("================================================");
							console.log("bundle : " + bundleConfig.bundleName);
							console.log("bundleQueue : " + bundleQueue);
							*/
							// If queue is empty, tell gulp the task is complete.
							// https://github.com/gulpjs/gulp/blob/master/docs/API.md#accept-a-callback
							callback();
						}
					}
				};

				return bundle();
			};

			// Start bundling source files with Browserify
			bundles.forEach(browserifyThis);
		});
	},

	watch: function(pattern, handler) {
		global.__WATCHING = true

		gulp.watch(pattern, function (callback) {
			return handler(callback);
		});
	},
/* NO FUNCIONA!
	task: function(task_name, handler) {
		gulp.task(task_name, function (callback) {
			return handler(callback);
		});
	},
*/
	del: function(pattern, clean, callback) {
		var bundleLogger = new BundleLogger(
			"del",
			pattern, false,
			colors.red
		);

		if (callback != undefined) {
			if (!clean) {
				bundleLogger.end("!clean con callback");
				return callback();
			}

			return del(pattern).then(function () {
				bundleLogger.end();
				callback();
			});
		} else {
			if (!clean) {
				bundleLogger.end("!clean sin callback");
				return;
			}

			return del(pattern).then(function () {
				bundleLogger.end();
			});
		}
	},

	get_gulp_instance: function () {
		return gulp;
	}/*,

	test: function () {
		console.log("XXX");
	}*/
}
