var gulp = require('gulp');
var autoprefexer = require('gulp-autoprefixer');
var sass = require('gulp-sass')(require('sass'));
var replace = require('gulp-replace');
var fontawesomeSubset = require('fontawesome-subset');
var del = require('del');
const purgecss = require('gulp-purgecss')
var cssnano = require('gulp-cssnano');
var concat = require('gulp-concat');
var rename = require('gulp-rename');
var uglify = require('gulp-uglify');

gulp.task('font:inter', function() {
  return gulp.src('node_modules/@fontsource/inter/**/*').pipe(replace(/\.\/files\//g, '/static/fonts/inter/files/')).pipe(gulp.dest('web/static/fonts/inter'))
});

gulp.task('font:rasa', function() {
  return gulp.src('node_modules/@fontsource/rasa/**/*').pipe(replace(/\.\/files\//g, '/static/fonts/rasa/files/')).pipe(gulp.dest('web/static/fonts/rasa'))
});


gulp.task('fontawesome', function(done) {
    del.sync('web/static/fonts/fontawesome/webfonts', {force:true});
    fontawesomeSubset.fontawesomeSubset({
      regular:['play-circle', 'question-circle'],
      solid: ['exclamation-triangle', 'angle-down', 'pause-circle', 'sign-in-alt', 'users','eye', 'eye-slash', 'external-link-alt', 'calendar', 'stop-circle','question-circle', 'circle-notch','times-circle', 'check-circle', 'angle-right', 'file-download', 'info-circle', 'search', 'edit', 'trash', 'backspace', 'sort', 'terminal', 'list', 'ban', 'toggle-on', 'toggle-off', 'plus', 'sync-alt', 'download', 'copy', 'check']
          }, 'web/static/fonts/fontawesome/webfonts')

    done();
});

gulp.task('sass', function() {
  return gulp.src("web/static/assets/**/*.scss")
    .pipe(sass().on('error', sass.logError))
    .pipe(
      purgecss({
        content: ['web/static/lib/**/*.js', 'web/static/js/**/*.js', 'web/templates/**/*.html.j2', 'runner/templates/**/*.html.j2', 'scheduler/templates/**/*.html.j2'],
        safelist: ['has-text-success', 'mr-3', 'has-text-warning'],
        whitelist: ['has-text-success', 'mr-3', 'has-text-warning']
      })
    )
    .pipe(autoprefexer({
        overrideBrowserslist: ['last 2 versions']
    }))
    .pipe(cssnano())
    .pipe(gulp.dest('web/static/css/'))
});

gulp.task('build', gulp.parallel('font:inter','font:rasa', gulp.series('fontawesome','sass')));

gulp.task('watch', gulp.series('build', function (cb) {
    gulp.watch('web/static/assets/**/*.scss', gulp.series('sass'));
    gulp.watch('web/fonts/fontawesome/**/*.scss', gulp.series('fontawesome','sass'));
    gulp.watch('web/**/*.html*', gulp.series('fontawesome', 'sass'));
    cb();
}));
