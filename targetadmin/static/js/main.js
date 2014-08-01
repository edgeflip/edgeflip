require.config( {

    baseUrl: '/static/js',

    paths: {
        styles: '../css',
        templates: '../templates',
        jquery: 'vendor/jquery'
    },

    shim: {

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

        'vendor/handlebars': {
            exports: 'Handlebars'
        },
        
        'vendor/bootstrap.min': {
            deps: [ 'jquery' ]
        },

        'extendBackbone': {
            deps: [ 'vendor/backbone', 'vendor/underscore', 'jquery' ],
        },

        'models/filterModels': {
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
