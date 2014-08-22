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
            
            events: { },

            initialize: function( options ) {

                _.extend( this, options ); 
                
                this.model = new Backbone.Model( { clientId: this.clientId } );

                if( this.id ) {
                    this.formAction += this.id + "/";
                    this.getCampaignData();
                    this.on( 'receivedCampaignData', this.render, this );
                } else {
                    this.render();
                }

                return this;
            },

            render: function() {

                this.slurpHtml( {
                    template: template(this),
                    insertion: { $el: this.$el.appendTo(this.parentEl) } } );

                this.renderSubViews();
                
                this.model.on( 'change:state', this.reflectState, this );
                this.model.set( { state: 'intro' } );

                this.off( 'receivedCampaignData', this.render );
                return this;
            },

            renderSubViews: function() {

                var subViewOpts = {
                    model: this.model,
                    campaignModel: this.campaignModel,
                    facebookPostImage: this.facebookPostImage,
                    facesExampleURL: this.facesExampleURL,
                    fbObjExampleURL: this.facebookPostImage,
                    howItWorksURL: this.howItWorksURL,
                    parentEl: this.templateData.container,
                    hide: true
                };

                this.subViews = {
                    intro: new Intro( subViewOpts )
                               .on('nextStep', this.handleIntroNextStep, this ),

                    filters: new Filters( subViewOpts )
                               .on('nextStep', function() { this.model.set('state','faces'); }, this )
                               .on('previousStep', function() { this.model.set('state','intro'); }, this ),
                    
                    faces: new Faces( subViewOpts )
                               .on('nextStep', function() { this.model.set('state','fbObj'); }, this )
                               .on('previousStep', function() { this.model.set('state','filters'); }, this ),
                    
                    fbObj: new FbObj( subViewOpts )
                               .on('validated', this.postForm, this )
                               .on('previousStep', function() { this.model.set('state','faces'); }, this )
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

            handleIntroNextStep: function() {
                this.templateData.name.val( this.subViews.intro.templateData.formInput.val() );
                this.model.set('state','filters');
            },

            postForm: function() {
                this.templateData.form.submit();
            },

            getCampaignData: function() {

                $.ajax( {
                    url: this.campaignDataURL.replace( '/0/', '/' + this.id + '/' ),
                    success: this.handleCampaignData.bind( this )
                } );
            },

            handleCampaignData: function( response ) {
                this.campaignModel = new Backbone.Model( response );
                this.trigger('receivedCampaignData');
            }

        } );
    }
);
