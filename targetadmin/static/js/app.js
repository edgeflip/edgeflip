/*
   module that adds our flavor to backbone, a .js polyfill,
   bootstrap.js, bootstrap css, and our global css
*/
define(
    [ 
      'extendBackbone',
      'polyfill',
      'vendor/bootstrap.min',
      'css!styles/vendor/bootstrap.min',
      'css!styles/vendor/bootstrap-theme.min',
      'css!styles/app'
    ],
    function( extendedBackbone ) { } );
