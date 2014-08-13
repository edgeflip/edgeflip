define(
    [
      'jquery',
      'vendor/underscore',
      'extendBackbone',
      'templates/sidebar',
      'css!styles/sidebar'
    ],
    function( $, _, Backbone, template ) {

        //This module always returns the same instance of sidebar
        //Useful for accessing in other scopes
        return new ( Backbone.View.extend( {
           
            events: {
                'click li[data-nav="reports"]': 'reportsClicked',
                'click li[data-nav="help"]': 'helpClicked',
                'click li[data-js="btn"]': 'contentItemClicked'
            },

            initialize: function() { },

            setup: function( options ) {

                _.extend( this, options );

                this.model.on( "change:state", this.renderState, this );

                return this;
            },

            render: function() {

                this.slurpHtml( {
                    template: template( this.model.toJSON() ),
                    insertion: { $el: this.$el.prependTo(this.parentEl) } } );

                this.postRender();

                return this;
            },

            postRender: function() {
                this.renderState();
            },

            /* style 'selected' button */
            renderState: function() {
                if( this.templateData.contentBtn && this.model.get('state') ) {
                    this.templateData.contentBtn
                        .removeClass('selected')
                        .filter("li[data-nav='" + this.model.get('state') + "']").addClass('selected');
                }
            },

            /* toggle content on click */
            contentItemClicked: function(e) {
                this.model.set( "state", $(e.currentTarget).data('nav') );
                this.content[ this.model.previous('state') ].fadeOut();
                this.content[ this.model.get('state') ].fadeIn();
            },

            reportsClicked: function() {
                window.location = this.reportingDashboardURL;
            },

            helpClicked: function() {
                window.open("mailto:help@edgeflip.com");
            }
        } ) )();
    }
);
