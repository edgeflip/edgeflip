require.config( {

    paths: {

        styles: '../css',

        templates: '../templates',

        jquery: 'vendor/jquery'

    },

    shim: {

        'vendor/backbone': {
            deps: [ 'vendor/underscore', 'vendor/jquery' ],
            exports: 'Backbone'
        },

        'vendor/underscore': {
            exports: '_'
        },

        'vendor/handlebars': {
            exports: 'Handlebars'
        },
        
        'vendor/bootstrap': {
            deps: [ 'vendor/jquery' ]
        },
    },

    map: {
        '*': {
            'css': 'vendor/css'
        }
    }
} );

require(['app']);
