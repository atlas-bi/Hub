import gulp from 'gulp';
import autoprefexer from 'gulp-autoprefixer';
import * as dartSass from 'sass';
import gulpSass from 'gulp-sass';
const sass = gulpSass(dartSass);
import postcss from 'gulp-postcss';
import replace from 'gulp-replace';
import fontawesomeSubset from 'fontawesome-subset';
import {deleteSync} from 'del';
import purgecss from 'gulp-purgecss';
import cssnano from 'cssnano';

gulp.task('font:inter', function() {
  return gulp.src('node_modules/@fontsource/inter/**/*', { removeBOM: false }).pipe(replace(/\.\/files\//g, '/static/fonts/inter/files/')).pipe(gulp.dest('web/static/fonts/inter'))
});

gulp.task('font:rasa', function() {
  return gulp.src('node_modules/@fontsource/rasa/**/*', { removeBOM: false }).pipe(replace(/\.\/files\//g, '/static/fonts/rasa/files/')).pipe(gulp.dest('web/static/fonts/rasa'))
});


gulp.task('fontawesome', function(done) {
    deleteSync('web/static/fonts/fontawesome/webfonts', {force:true});
    fontawesomeSubset.fontawesomeSubset({
      regular:['circle-play', 'circle-question'],
      solid: ['triangle-exclamation', 'angle-down', 'circle-pause', 'right-to-bracket', 'users','eye', 'eye-slash', 'arrow-up-right-from-square', 'calendar', 'circle-stop','circle-question', 'circle-notch','circle-xmark', 'circle-check', 'angle-right', 'file-arrow-down', 'circle-info', 'magnifying-glass', 'pen-to-square', 'trash', 'delete-left', 'sort', 'terminal', 'list', 'ban', 'toggle-on', 'toggle-off', 'plus', 'rotate', 'download', 'copy', 'check']
          }, 'web/static/fonts/fontawesome/webfonts')

    done();
});

gulp.task('sass', function() {
  const plugins = [
    cssnano({
      preset: ['default', { discardComments: true }],
    }),
  ];
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
    .pipe(postcss(plugins))
    .pipe(gulp.dest('web/static/css/'))
});

gulp.task('build', gulp.parallel('font:inter','font:rasa', gulp.series('fontawesome','sass')));

gulp.task('watch', gulp.series('build', function (cb) {
    gulp.watch('web/static/assets/**/*.scss', gulp.series('sass'));
    gulp.watch('web/fonts/fontawesome/**/*.scss', gulp.series('fontawesome','sass'));
    gulp.watch('web/**/*.html*', gulp.series('fontawesome', 'sass'));
    cb();
}));
