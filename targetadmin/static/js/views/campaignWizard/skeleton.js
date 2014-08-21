define(
    [
      'jquery',
      'vendor/underscore',
      'extendBackbone',
      'views/campaignWizard/intro',
      'views/campaignWizard/filters',
      'views/campaignWizard/faces',
      'views/campaignWizard/fbObj',
      'templates/campaignWizard/skeleton',
      'css!styles/campaignWizard/skeleton'
    ],
    function( $, _, Backbone, Intro, Filters, Faces, FbObj, template ) {

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
                    template: template(this),
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
                    } ).on('nextStep', function() { this.model.set('state','faces'); }, this ),
                    
                    faces: new Faces( {
                        model: this.model,
                        parentEl: this.templateData.container,
                        facesExampleURL: this.facesExampleURL,
                        hide: true,
                    } ).on('nextStep', function() { this.model.set('state','fbObj'); }, this ),
                    
                    fbObj: new FbObj( {
                        model: this.model,
                        parentEl: this.templateData.container,
                        fbObjExampleURL: this.facebookPostImage,
                        hide: true,
                    } ).on('validated', this.postForm, this )
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
                $('html,body').scrollTop(0);
                this.subViews[ this.model.get('state') ].$el.fadeIn( 400, this.triggerShown.bind(this) );
            },

            triggerShown: function() {
                this.subViews[ this.model.get('state') ].trigger('shown');
            },

            postForm: function() {
                this.templateData.form.submit();
            }

        } );
    }
);
