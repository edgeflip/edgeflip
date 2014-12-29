/* Campaign wizard's "skeleton" view.  Manages the wizard sub views. */
define(
    [
      'jquery',
      'vendor/underscore',
      'extendBackbone',
      'views/modal',
      'views/campaignWizard/intro',
      'views/campaignWizard/filters',
      'views/campaignWizard/faces',
      'views/campaignWizard/fbObj',
      'templates/campaignWizard/skeleton',
      'css!styles/campaignWizard/skeleton'
    ],
    function ($, _, Backbone, modal, Intro, Filters, Faces, FbObj, template) {

        return Backbone.View.extend({
            
            events: {
                "keyup input": "keyUp"
            },

            /* If a campaign id was passed into the constructor,
               make an ajax request to get the data.  A more backbone approach
               would be to create a campaign model, and have that do the work.
               If no id, just render. */               
            initialize: function (options) {
                var effectiveId;

                _.extend(this, options);
                this.model = new Backbone.Model({clientId: this.clientId});
                if (this.id) {
                    this.formAction = edgeflip.router.reverse('targetadmin:campaign-wizard-edit',
                                                              this.clientId, this.id);
                } else {
                    this.formAction = edgeflip.router.reverse('targetadmin:campaign-wizard',
                                                              this.clientId);
                }

                effectiveId = this.id || this.cloneId;
                if (effectiveId) {
                    this.getCampaignData(effectiveId);
                    this.on('receivedCampaignData', this.render, this);
                } else {
                    this.render();
                }

                return this;
            },


            render: function () {
                /* Insert wizard scaffold, then insert sub views, initialize model's "state"
                 * (associated with a sub view), so we know what view to render
                 */
                this.slurpHtml({
                    template: template(this),
                    insertion: {$el: this.$el.appendTo(this.parentEl)}
                });
                this.renderSubViews();
                
                this.model.on('change:state', this.reflectState, this);
                this.model.set({state: 'intro'});

                this.off('receivedCampaignData', this.render);
                return this;
            },

            navDeferred: function (state) {
                return (function () {
                    this.model.set('state', state);
                }).bind(this);
            },

            renderSubViews: function () {
                /* This function creates the sub views, adds handlers to their back/next events.
                 *
                 * subViewOpts is sloppy, each subview, or sub mode should make
                 * an ajax request to get the data it needs rather than frontloading
                 * everything in client_home.
                 */
                var subViewOpts = {
                    model: this.model,
                    campaignModel: this.campaignModel,
                    facebookPostImage: this.facebookPostImage,
                    facesExampleURL: this.facesExampleURL,
                    fbObjExampleURL: this.facebookPostImage,
                    howItWorksURL: this.howItWorksURL,
                    parentEl: this.templateData.container,
                    hide: true,
                    isEdit: Boolean(this.id),
                    isClone: Boolean(this.cloneId)
                };

                this.subViews = {
                    intro: new Intro(subViewOpts)
                               .on('nextStep', this.handleIntroNextStep, this),

                    filters: new Filters(subViewOpts)
                               .on('nextStep', this.navDeferred('faces'), this)
                               .on('previousStep', this.navDeferred('intro'), this),
                    
                    faces: new Faces(subViewOpts)
                               .on('nextStep', this.navDeferred('fbObj'), this)
                               .on('previousStep', this.navDeferred('filters'), this),
                    
                    fbObj: new FbObj(subViewOpts)
                               .on('validated', this.postForm, this)
                               .on('previousStep', this.navDeferred('faces'), this)
                };

                return this;
            },

            setStateLocation: function () {
                window.location.hash =
                    'campaign.' +
                    (this.id ? this.id + '.' : '') +
                    'wizard.' +
                    this.model.get('state');
            },

            getStateLocation: function () {
                var stateMatch = window.location.hash.match(/campaign\.(?:\d+\.)?wizard\.(.+)$/);
                return stateMatch ? stateMatch[1] : null;
            },

            reflectLocation: function () {
                var hashState = this.getStateLocation();
                if (hashState && hashState !== this.model.get('state')) {
                    /* user initiated browser navigation */
                    this.model.set('state', hashState);
                }
            },

            reflectState: function () {
                /* When the model's "state" attribute changes, this function fires,
                 * hiding the old and showing the new
                 */
                var previousUI;

                // Don't let the modal singleton stay open or otherwise share state across subviews:
                modal.reset();

                previousUI = this.subViews[this.model.previous('state')];
                if (previousUI) {
                    previousUI.$el.fadeOut(400, this.showCurrentState.bind(this));
                } else {
                    this.showCurrentState();
                }

                this.setStateLocation();
            },

            showCurrentState: function () {
                $('html,body').scrollTop(0);
                this.subViews[this.model.get('state')].$el.fadeIn(400, this.triggerShown.bind(this));
            },

            /* used by the image companion views (faces, fbObj) -- triggers an event on
               the sub view when it is shown */
            triggerShown: function () {
                this.subViews[this.model.get('state')].trigger('shown');
            },

            /* called when the intro sub view triggers 'nextStep', sets the campaign, updates model */
            handleIntroNextStep: function () {
                this.templateData.name.val(this.subViews.intro.templateData.formInput.val());
                this.model.set('state','filters');
            },

            /* posts form to server to make or edit a campaign.  I think it best that this be done
               via ajax eventually */
            postForm: function () {
                this.templateData.form.submit();
            },

            getCampaignData: function (id) {
                var dataUrl = edgeflip.router.reverse('targetadmin:campaign-data',
                                                      this.clientId, id);
                $.ajax({url: dataUrl, success: this.handleCampaignData.bind(this)});
            },

            /* takes campaign-data response and sets it on the campaignModel */
            handleCampaignData: function (response) {
                this.campaignModel = new Backbone.Model(response);
                this.trigger('receivedCampaignData');
            },

            keyUp: function (event) {
                if (event.which === 13) {
                    this.subViews[this.model.get('state')].trigger('enterPressed');
                }
            }

        });
    }
);
