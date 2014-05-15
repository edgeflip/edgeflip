define( [ 'jquery' ], function( $ ) {
    var ourWindow = $(window),
        windowHeight = undefined,
        windowWidth = undefined;
        computeWindowSize = function() { 
            windowHeight = ourWindow.outerHeight( true );
            windowWidth = ourWindow.outerWidth( true );
        };

    computeWindowSize();
    $( computeWindowSize );
    ourWindow.on( 'resize', computeWindowSize );

    return {
        window: ourWindow,
        windowHeight: windowHeight,
        windowWidth: windowWidth
    }
} );
