define( [ 'jquery' ], function( $ ) {
    var util = function() {
        var self = this;

        $.extend( this, {
            document: $(document),
            window: $(window),
            html: $('html'),
            body: $('body'),
            bodyHeight: undefined,
            windowHeight: undefined,
            windowWidth: undefined,
            navbarHeight: undefined,
            scrollTop: undefined,
            maxScroll: undefined
        } );
    
        this.window.on( 'resize', function() { self.computeSizes() } );
        this.window.on( 'scroll', function() { self.getScrollPosition() } );
    
        this.computeSizes();

        $( function() {
            self.computeSizes();
            self.navbarHeight = $('.navbar-nav').outerHeight( true ) } );
    };

    $.extend( util.prototype, {

        computeSizes: function() { 
            $.extend( this, {
                windowHeight: this.window.outerHeight( true ),
                windowWidth: this.window.outerWidth( true ),
                bodyHeight: this.body.outerHeight( true )
            } );
            this.maxScroll = this.bodyHeight - this.windowHeight;
        },
        
        getScrollPosition: function() {
            this.scrollTop =
                ( this.body.scrollTop() != 0 )
                    ? this.body.scrollTop()
                    : this.html.scrollTop();
        }
    } );

    return new util();
} );
