/*
   module that adds our flavor to backbone, a .js polyfill,
   bootstrap.js, bootstrap css, and our global css
*/
define(
    [ 
      'polyfill',
      'vendor/bootstrap.min',
      'font!typekit,id:ixj6alt',
      'css!styles/vendor/bootstrap.min',
      'css!styles/vendor/bootstrap-theme.min',
      'css!styles/vendor/jquery-ui.css',
      'css!styles/app'
    ],
    function() { }
);
