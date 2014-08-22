/* require js configuration file */
require.config( {

    /* base path when looking for files ( preferably modules )
       e.g. : require( [ 'dir/myFile' ], function(myFile) { }
       looks here: $DOMAIN/static/js/dir/myFile.js */
    baseUrl: '/static/js',

    /* essentially symlinks for paths (still use baseUrl) */
    paths: {
        styles: '../css',
        templates: '../templates',
        jquery: 'vendor/jquery',

        font: 'vendor/font',
        propertyParser : 'vendor/propertyParser'
    },

    /* not all files executed by require need to be in AMD 
       ( asynchronous modular definition ) format, those files
       are spelled out here so require knows what to do with them */
    shim: {

        'vendor/jquery-ui': {
            deps: [ 'jquery' ]
        },

        'vendor/backbone': {
            deps: [ 'vendor/underscore', 'jquery' ],
            exports: 'Backbone'
        },

        'vendor/underscore': {
            exports: '_'
        },

        'vendor/handlebars': {
            exports: 'Handlebars'
        },
        
        'vendor/bootstrap.min': {
            deps: [ 'jquery' ]
        },
        
        'vendor/bootstrap3-typeahead': {
            deps: [ 'jquery' ]
        },
        
        'vendor/d3': {
            exports: [ 'd3' ]
        },

        /* these two files should probably be made into AMD
           so this nonsense isn't needed */ 
        'extendBackbone': {
            deps: [ 'vendor/backbone', 'vendor/underscore', 'jquery' ],
            init: function( Backbone, _, $ ) { return Backbone; }
        },

        'models/filters': {
            deps: [ 'jquery', 'vendor/backbone' ],
            exports: 'filterCollection'
        }
    },

    /* this is used by the require.js css plugin
       instead of using link tags it will inject css 
       directly onto the page 
    */
    map: {
        '*': {
            'css': 'vendor/css'
        }
    }
} );
