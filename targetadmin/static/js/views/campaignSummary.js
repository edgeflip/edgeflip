/* module for campaign summary view */
define(
    [
      'jquery',
      'vendor/underscore',
      'extendBackbone',
      'models/campaign',
      'templates/campaignSummary',
      'views/modal',
      'css!styles/campaignSummary'
    ],
    function ($, _, Backbone, campaign, template, modal) {

        return Backbone.View.extend({
            /* model for view's state */
            model: new Backbone.Model({}),

            /* see sidebar.js for not bloated DOM suggestion */
            events: {
                'click [data-js=homeBtn],[data-js=editBtn],[data-js=cloneBtn]': 'goHome',
                'click [data-js=previewBtn]': 'openPreview',
                'click [data-js=publishBtn]': 'confirmPublish',
                'click [data-js=archiveBtn]': 'confirmArchive'
            },

            initialize: function (options) {
                _.extend(this, options);
                this.model.set('state', 'mainView');

                /* creates campaign, see model for attributes */
                this.campaign = new campaign(options, {parse: true});
                this.archiveUrl = null;
                this.publishUrl = null;

                return this.render();
            },

            /* render out that campaign */
            render: function () {
                this.slurpHtml({
                    template: template({
                        campaign: this.campaign.toJSON(),
                        canArchive: this.canArchive
                    }),
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
            },

            postUrl: function (url) {
                var $form = $('<form method="post" action="' + url + '">' +
                              this.token + '</form>');
                this.$el.append($form);
                $form.submit();
            },

            confirmPublish: function (event) {
                modal.reset().update({
                    title: 'Publish <span class="sml-caps">' + this.campaign.get('name') + '</span>?',
                    body: (
                        "<p>Publishing your campaign makes it visible to your supporters. " +
                            "We'll provide you with a public URL, for you to disseminate far and wide.</p>" +
                        "<p>However, to provide you with the most accurate reporting, " +
                            "once you've published a campaign, you may no longer edit it.</p>" +
                        "<p>Are you sure you're ready to publish this campaign?</p>"
                    ),
                    confirmText: 'Yes, publish it!',
                    showCloseBtn: true
                }).on('confirmed', this.performPublish, this)
                .templateData.modalContainer.modal();
            },

            performPublish: function () {
                /* Disable submission button to prevent multiple calls */
                modal.templateData.modalContainer.trigger('confirm_bad');

                /* Reverse URL path lazily */
                if (this.publishUrl === null) {
                    this.publishUrl = edgeflip.router.reverse('targetadmin:publish-campaign',
                                                              this.clientId,
                                                              this.campaign.get('pk'));
                }

                this.postUrl(this.publishUrl);
            },

            confirmArchive: function (event) {
                modal.reset().update({
                    title: 'Archive <span class="sml-caps">' + this.campaign.get('name') + '</span>?',
                    body: (
                        "<p>[Superusers only] Are you sure you want to archive this campaign? " +
                        "Archiving disables access to the campaign outside of this page!</p>"
                    ),
                    confirmText: 'Yes, archive it!',
                    showCloseBtn: true
                }).on('confirmed', this.performArchive, this)
                .templateData.modalContainer.modal();
            },

            performArchive: function () {
                modal.templateData.modalContainer.trigger('confirm_bad');

                /* Reverse URL path lazily */
                if (this.archiveUrl === null) {
                    this.archiveUrl = edgeflip.router.reverse('targetadmin:archive-campaign',
                                                              this.clientId,
                                                              this.campaign.get('pk'));
                }

                this.postUrl(this.archiveUrl);
            }
        });
    }
);
