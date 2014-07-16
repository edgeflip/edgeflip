define(
    [
      'jquery',
      'vendor/underscore',
      'vendor/backbone',
      'templates/sidebar',
      'css!styles/sidebar'
    ],
    function( $, _, Backbone, template ) {

        return Backbone.View.extend( {
            
            events: {
                'click li[data-js="btn"]': 'navClicked',
                'click li[data-nav="reports"]': 'reportsClicked',
                'click li[data-nav="help"]': 'helpClicked',
                'click li[data-nav="campaigns"]': 'campaignsClicked'
            },

            initialize: function( options ) {

                _.extend( this, options );

                this.model.on( "change:state", this.renderState, this );

                return this.render();
            },

            render: function() {

                this.slurpHtml( {
                    template: template( this.templateOptions ),
                    insertion: { $el: this.$el.appendTo(this.parentEl) } } );

                this.postRender();

                return this;
            },

            postRender: function() {
                this.renderState();
            },

            renderState: function() {
                this.templateData.btn
                    .removeClass('selected')
                    .filter("li[data-nav='" + this.model.get('state') + "']").addClass('selected');
            },

            navClicked: function(e) {
                this.model.set( "state", $(e.currentTarget).data('nav') );
            },

            campaignsClicked: function() {
                $('.help').parent().fadeOut( function() {
                    $('.client-home').parent().fadeIn(); } );
            },

            helpClicked: function() {
                $('.client-home').parent().fadeOut( function() {
                    $('.help').parent().fadeIn(); } );
            },

            reportsClicked: function() {
                window.location = this.reportingDashboardURL;
            }
        } );
    }
);
