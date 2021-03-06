module.exports = function(grunt) {

    var static = function( path ) { return '../static/' + ( ( path ) ? path : '' ); }

    grunt.initConfig( {

        pkg: grunt.file.readJSON('package.json'),

        less: {
            compile: {
                files: [
                    {
                      expand: true,
                      cwd: static(),
                      src: ['less/**/*.less'],
                      rename: function( dest, src ) {
                          return static('css/') + src.replace(/^less[\/]/, '');
                      },
                      ext: '.css'
                    }
                ]
            }
        },

        handlebars: {

            compile: {

                options: {
                    amd: "vendor/handlebars",
                    namespace: false,
                    /* remove newlines, white space text nodes from templates */
                    processContent: function(content, filepath) {
                        return content.replace(/[\r\n]/g, '')
                                      .replace(/\n/g, '')
                                      .replace(/>\s*</g, '><');
                    }
                },

                files: [
                    {
                      expand: true,
                      cwd: static(),
                      src: ['hbs/**/*.hbs'],
                      rename: function( dest, src ) {
                          return static('templates/') + src.replace(/^hbs[\/]/, '');
                      },
                      ext: '.js'
                    }
                ]
            }
        },

        watch: {
          handlebars: {
            files: [ static('hbs/**/*.hbs'), static('less/**/*.less') ],
            tasks: [ 'handlebars', 'less' ],
            options: {
              spawn: false,
            },
          },
        }
  } );

    grunt.loadNpmTasks('grunt-contrib-less');
    grunt.loadNpmTasks('grunt-contrib-handlebars');
    grunt.loadNpmTasks('grunt-contrib-watch');

    grunt.registerTask( 'build', [ 'handlebars', 'less' ] );
    grunt.registerTask( 'default', [ 'watch' ] );

};
