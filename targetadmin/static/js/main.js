require.config( {

    baseUrl: '/static/js',

    paths: {
        styles: '../css',
        templates: '../templates',
        jquery: 'vendor/jquery',

        font: 'vendor/font',
        propertyParser : 'vendor/propertyParser'
    },

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
        
        'vendor/d3': {
            exports: [ 'd3' ]
        },

        'extendBackbone': {
            deps: [ 'vendor/backbone', 'vendor/underscore', 'jquery' ],
            init: function( Backbone, _, $ ) { return Backbone; }
        },

        'models/filters': {
            deps: [ 'jquery', 'vendor/backbone' ],
            exports: 'filterCollection'
        }
    },

    map: {
        '*': {
            'css': 'vendor/css'
        }
    }
} );
