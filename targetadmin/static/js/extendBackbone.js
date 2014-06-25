Backbone.View.prototype.slurpEl = function( el ) {

    var key = ( el.is('[data-js]') )
        ? el.attr('data-js')
        : ( el.is('input,select,textarea[name]' ) )
            ? el.attr('name')
            : '_';

    this.templateData[ key ] = ( this.templateData.hasOwnProperty(key) )
        ? this.templateData[ key ].add( el )
        : el;

    return this;
}

Backbone.View.prototype.slurpHtml = function( options ) {
   
    var $html = ( options && options.template ) ? $( options.template ) : this.$el,
        selector = '[data-js]',
        self = this;
       
    if( options && options.slurpInputs ) { selector += ',input,select,textarea'; }

    if( this.templateData === undefined ) { this.templateData = { }; }

    _.each( $html, function( el ) {
        var $el = $(el);
        if( $el.is( selector ) ) { this.slurpEl( $el ); }
    }, this );

   _.each( $html.get(), function( el ) {
       $( el ).find( selector ).each( function( i, elToBeSlurped ) {
           self.slurpEl($(elToBeSlurped) ); } );
   }, this );

    if( options && options.insertion ) { options.insertion.$el[ ( options.insertion.method ) ? options.insertion.method : 'append' ]( $html ); }

    return this;
};

String.prototype.capitalize = function() { return this.charAt(0).toUpperCase() + this.slice(1); }
