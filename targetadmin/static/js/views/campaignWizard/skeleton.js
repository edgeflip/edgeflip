define(
    [
      'jquery',
      'vendor/underscore',
      'extendBackbone',
      'views/campaignWizard/intro',
      'views/campaignWizard/filters',
      'templates/campaignWizard/skeleton',
      'css!styles/campaignWizard/skeleton'
    ],
    function( $, _, Backbone, Intro, Filters, template ) {

        return Backbone.View.extend( {
            
            model: new Backbone.Model( { } ),

            events: { },

            initialize: function( options ) {

                _.extend( this, options ); 
                
                this.model.set( { clientId: this.clientId } );

                this.render();

                this.model.on( 'change:state', this.reflectState, this );
                this.model.set( { state: 'intro' } );

                return this;
            },

            render: function() {

                this.slurpHtml( {
                    template: template(),
                    insertion: { $el: this.$el.appendTo(this.parentEl) } } );

                this.renderSubViews();

                return this;
            },

            renderSubViews: function() {

                this.subViews = {
                    intro: new Intro( {
                        model: this.model,
                        facebookPostImage: this.facebookPostImage,
                        howItWorksURL: this.howItWorksURL,
                        parentEl: this.templateData.container,
                        hide: true,
                    } ).on('nextStep', function() { this.model.set('state','filters'); }, this ),

                    filters: new Filters( {
                        model: this.model,
                        parentEl: this.templateData.container,
                        hide: true,
                    } ).on('nextStep', function() { this.model.set('state','faces'); }, this )
                }

                return this;
            },

            reflectState: function() {
                var previousUI = this.subViews[ this.model.previous('state') ];

                if( previousUI ) {
                    previousUI.$el.fadeOut( 400, this.showCurrentState.bind(this) );
                } else {
                    this.showCurrentState();
                }
            },

            showCurrentState: function() {
                this.subViews[ this.model.get('state') ].$el.fadeIn();
            },

        } );
    }
);
