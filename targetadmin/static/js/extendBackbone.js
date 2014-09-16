/* Adding some extra flavor to Backbone */

/* This is a utility function used by slurpHtml below.  It takes an element
   and based on its 'data-js' or 'name' attribute, creates a key.
   If this key exists in the current view's templateData object, simply
   add the element, if not, create a new key/value pair */
Backbone.View.prototype.slurpEl = function (el) {
    var key, value;

    if (el.is('[data-js]')) {
        key = el.attr('data-js');
    } else if (el.is('input,select,textarea[name]')) {
        key = el.attr('name');
    } else {
        key = '_';
    }

    if (this.templateData.hasOwnProperty(key)) {
        value = this.templateData[key].add(el);
    } else {
        value = el;
    }

    this.templateData[key] = value;
    return this;
}

/* The purpose of this function is to ingest modules of HTML, and extract information
   from the it before it goes into the DOM as it gets more expensive to traverse
   when it is inside the DOM.  Any node with a 'data-js' attribute is slurped into
   a view's templateData key/value array.  I also added code to ingest input elements
   when I was slurping HTML already in the DOM - it was useful to get references to
   elements I knew I would use instead of writing jQuery selectors everytime. Note that
   this function will also insert the HTML to the DOM.  In the past, to minimize DOM bloat
   I have removed the data-js attributes, but only after I bound events to those elements
   using the same 'data-js' attribute. */
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

/* This function is not being used, and may not be necessary.  I have used it in the past
   to check if the mouse is hovering an element, usually an SVG element */
Backbone.View.prototype.isMouseOnEl = function( event, el ) {

    var elOffset = el.offset();
    var elHeight = el.outerHeight( true );
    var elWidth = el.outerWidth( true );

    if( ( event.pageX < elOffset.left ) ||
        ( event.pageX > ( elOffset.left + elWidth ) ) ||
        ( event.pageY < elOffset.top ) ||
        ( event.pageY > ( elOffset.top + elHeight ) ) ) {

        return false;
    }

    return true;
}

/* This is an "app" type of flavoring.  In most instances, I'm simply appending each
   Backbone view to the container below, and here is the DRY code that help us with that. */
Backbone.View.prototype.parentEl = $('#content-container');
