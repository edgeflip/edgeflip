/* module for campaign summary view */
define(
    [
      'jquery',
      'vendor/underscore',
      'extendBackbone',
      'models/campaign',
      'templates/campaignSummary',
      'css!styles/campaignSummary'
    ],
    function ($, _, Backbone, campaign, template) {

        return Backbone.View.extend({
            /* model for view's state */
            model: new Backbone.Model({}),

            /* see sidebar.js for not bloated DOM suggestion */
            events: {
                'click [data-js=homeBtn],[data-js=editBtn],[data-js=cloneBtn]': 'goHome',
                'click [data-js=previewBtn]': 'openPreview'
            },

            initialize: function (options) {
                _.extend(this, options);
                this.model.set('state', 'mainView');

                /* creates campaign, see model for attributes */
                this.campaign = new campaign(options, {parse: true});

                return this.render();
            },

            /* render out that campaign */
            render: function () {
                this.slurpHtml({
                    template: template({campaign: this.campaign.toJSON()}),
                    insertion: {$el: this.$el.appendTo(this.parentEl)}
                });
                return this;
            },

            goHome: function (event) {
                var btnData = $(event.currentTarget).attr('data-js'),
                    actionMatch = btnData && btnData.match(/^(edit|clone)Btn$/),
                    action = actionMatch && actionMatch[1],
                    hash = action ? '#campaign.' + this.pk + '.' + action : '';

                window.location = this.campaign_list_url + hash;
            },

            openPreview: function (event) {
                window.open(this.sharing_url);
            }
        });
    }
);
