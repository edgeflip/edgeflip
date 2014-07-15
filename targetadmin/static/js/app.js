define(
    [ 'vendor/bootstrap.min',
      'css!styles/vendor/bootstrap.min',
      'css!styles/vendor/bootstrap-theme.min',
      'css!styles/app'
    ],
    function() {
        //mozilla polyfill (will ECMA 6 arrive?)
        if(!String.prototype.endsWith) {
            Object.defineProperty(String.prototype, 'endsWith', {
                value: function (searchString, position) {
                    var subjectString = this.toString();
                    if(position === undefined || position > subjectString.length) {
                        position = subjectString.length;
                    }
                    position -= searchString.length;
                    var lastIndex = subjectString.indexOf(searchString, position);
                    return lastIndex !== -1 && lastIndex === position;
                }
            } );
        }
    }
);
