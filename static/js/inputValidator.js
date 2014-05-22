define(
    [ 'jquery', 'vendor/underscore', 'ourBackbone', 'util', 'vendor/bootstrap' ],

    function( $, _, Backbone, util ) {

        return new ( Backbone.View.extend( {

            collection: [ ],

            popoverOptions: {
                animation: false,
                trigger: 'manual',
                placement: 'bottom'
            },

            destroyPopover: function( item ) {
                item.inputEl.off( 'focus', item.destroyBinding );
                item.popoverEl.popover('destroy');
                this.collection = _.without( this.collection, item );
            },

            destroyAll: function() {
                _.each( this.collection, this.destroyPopover, this );
            },

            positionAndShowPopover: function() {
                var item = _.last( this.collection ),
                    offset = item.inputEl.offset(),
                    top = offset.top + ( item.inputEl.outerHeight( true ) / 2 ),
                    left = offset.left + ( item.inputEl.outerWidth( true ) / 2 ),
                    self = this;

                item.destroyBinding = function() { self.destroyPopover(item); }

                item.popoverEl.css( { top: top, left: left } ).popover('show')
                              .next().addClass('invalid-input-message').on( 'click', item.destroyBinding );

                item.inputEl.on( 'focus', item.destroyBinding );
            },

            notifyUser: function( el, options ) {
                if( _.find( this.collection, function( data ) {
                    return data.inputEl === el; } ) ) { return; }

                this.collection.push( {
                    popoverEl: $('<div class="invalid-input-popover"></div>')
                                    .appendTo( this.$el )
                                    .popover( _.extend( { }, this.popoverOptions, options ) ),
                    inputEl: el
                } );

                this.positionAndShowPopover();
            },

            scrollToFirst: function() {
                var maxScroll = util.maxScroll,
                    scrollTop = _.reduce( this.collection, function( memo, data ) {
                        var top = data.inputEl.offset().top;
                        if( top < memo ) { memo = top; }
                        return memo;
                    }, maxScroll, this );

                $('html,body').animate(
                    { 'scrollTop': scrollTop - 100 },
                    { duration: 600 } );

            },

        } ) )( { el: 'body' } );
    }
);
