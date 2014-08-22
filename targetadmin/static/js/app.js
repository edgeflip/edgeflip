/*
   application wide module:
      adds custom flavor to backbone,
      a .js polyfill,
      uses require.js font plugin to grab our typekit font package
      bootstrap css, and our global css
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
