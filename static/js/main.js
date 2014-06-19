require.config( {

    baseUrl: '/static/js',

    paths: {

        styles: '../css',
        templates: '../templates',

        targetshare: '/static',

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
        }
        
    },

    map: {
        '*': {
            'css': 'vendor/css'
        }
    }
} );
