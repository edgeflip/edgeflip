/* sidebar depends on */
define(
    [
      'jquery',
      'vendor/underscore',
      'vendor/backbone',
      'templates/sidebar', // function which returns sidebar html
      'css!styles/sidebar' // CSS ( inserted into DOM )
    ],
    function( $, _, Backbone, template ) {

        return Backbone.View.extend( {
           
            /* event handler: function */ 
            events: {
                'click li[data-nav="reports"]': 'reportsClicked',
                'click li[data-nav="help"]': 'contentItemClicked',
                'click li[data-nav="campaigns"]': 'contentItemClicked'
            },

            /* called on instantiation */
            initialize: function( options ) {

                _.extend( this, options );

                this.model.on( "change:state", this.renderState, this );

                return this.render();
            },

            render: function() {

                this.slurpHtml( {
                    template: template( this.templateOptions ),
                    insertion: { $el: this.$el.prependTo(this.parentEl) } } );

                this.postRender();

                return this;
            },

            postRender: function() {
                this.renderState();
            },

            /* style 'selected' button */
            renderState: function() {
                this.templateData.btn
                    .removeClass('selected')
                    .filter("li[data-nav='" + this.model.get('state') + "']").addClass('selected');
            },

            /* toggle content on click */
            contentItemClicked: function(e) {
                this.model.set( "state", $(e.currentTarget).data('nav') );
                this.content[ this.model.previous('state') ].fadeOut();
                this.content[ this.model.get('state') ].fadeIn();
            },

            reportsClicked: function() {
                window.location = this.reportingDashboardURL;
            }
        } );
    }
);
