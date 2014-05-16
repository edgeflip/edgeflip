define( [ 'jquery' ], function( $ ) {
    var util = new ( function() {
        $.extend( this, {
            document: $(document),
            window: $(window),
            windowHeight: undefined,
            windowWidth: undefined } );
    } )(),
        computeWindowSize = function() { 
            util.windowHeight = util.window.outerHeight( true );
            util.windowWidth = util.window.outerWidth( true );
        };

    computeWindowSize();
    $( computeWindowSize );
    util.window.on( 'resize', computeWindowSize );

    return util;
} );
