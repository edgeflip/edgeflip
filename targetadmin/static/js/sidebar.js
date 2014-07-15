define(
    [
      'jquery',
      'vendor/underscore',
      'ourBackbone',
      'templates/sidebar',
      'css!styles/sidebar'
    ],
    function( $, _, Backbone, template ) {

        return Backbone.View.extend( {
            
            events: {
                'click li[data-nav="reports"]': 'reportsClicked'
            },

            initialize: function( options ) {

                _.extend( this, options ); 

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

            reportsClicked: function() {
                window.location = this.reportingDashboardURL;
            }
        } );
    }
);
