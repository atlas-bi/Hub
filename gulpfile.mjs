import pkg from 'gulp';
const { src, dest, task, parallel,series } = pkg;
import autoprefexer from 'gulp-autoprefixer';
import * as dartSass from 'sass';
import gulpSass from 'gulp-sass';
const sass = gulpSass(dartSass);
import postcss from 'gulp-postcss';
import replace from 'gulp-replace';
import {fontawesomeSubset} from 'fontawesome-subset';
import {deleteSync} from 'del';
import purgecss from 'gulp-purgecss';
import cssnano from 'cssnano';

task('font:inter', function() {
  return src('node_modules/@fontsource/inter/**/*', { removeBOM: false })
  .pipe(replace(/\.\/files\//g, '/static/fonts/inter/files/'))
  .pipe(dest('web/static/fonts/inter'))
});

task('font:rasa', function() {
  return src('node_modules/@fontsource/rasa/**/*', { removeBOM: false })
  .pipe(replace(/\.\/files\//g, '/static/fonts/rasa/files/'))
  .pipe(dest('web/static/fonts/rasa'))
});


task('fontawesome', function(done) {
    deleteSync('web/static/fonts/fontawesome/webfonts', {force:true});
    fontawesomeSubset({
      regular:['circle-play', 'circle-question'],
      solid: ['triangle-exclamation'
          , 'angle-down'
          , 'circle-pause'
          , 'right-to-bracket'
          , 'users'
          , 'eye'
          , 'eye-slash'
          , 'arrow-up-right-from-square'
          , 'calendar'
          , 'circle-stop'
          , 'circle-question'
          , 'circle-notch'
          , 'circle-xmark'
          , 'circle-check'
          , 'angle-right'
          , 'file-arrow-down'
          , 'circle-info'
          , 'magnifying-glass'
          , 'pen-to-square'
          , 'trash'
          , 'delete-left'
          , 'sort'
          , 'terminal'
          , 'list'
          , 'ban'
          , 'toggle-on'
          , 'toggle-off'
          , 'plus'
          , 'rotate'
          , 'download'
          , 'copy'
          , 'check']
          }, 'web/static/fonts/fontawesome/webfonts')

    done();
});

task('sass', function() {
  const plugins = [
    cssnano({
      preset: ['default', { discardComments: true }],
    }),
  ];
  return src("web/static/assets/**/*.scss")
    .pipe(sass().on('error', sass.logError))
    .pipe(postcss(plugins))
    .pipe(
      purgecss({
        content: ['web/static/lib/**/*.js'
          , 'web/static/js/**/*.js'
          , 'web/templates/**/*.html.j2'
          , 'runner/templates/**/*.html.j2'
          , 'scheduler/templates/**/*.html.j2'
          , 'web/web/*.py'],
        safelist: [],
        whitelist: []
      })
    )
    .pipe(autoprefexer())
    .pipe(dest('web/static/css/'))
});

task('build', parallel('font:inter','font:rasa', series('fontawesome','sass')));

task('watch', series('build', function (cb) {
    watch('web/static/assets/**/*.scss', series('sass'));
    watch('web/fonts/fontawesome/**/*.scss', series('fontawesome','sass'));
    watch('web/**/*.html*', series('fontawesome', 'sass'));
    cb();
}));
