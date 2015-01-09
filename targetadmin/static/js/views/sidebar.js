/* view for side navigation menu */
define(
    [
      'jquery',
      'vendor/underscore',
      'extendBackbone',
      'templates/sidebar',
      'css!styles/sidebar'
    ],
    function ( $, _, Backbone, template ) {

        /* This module always returns the same instance of sidebar
           useful for accessing in other scopes */
        return new ( Backbone.View.extend( {
          
            /* automatically delegated on initialize
               in the past I've removed the data-* attributes in
               the slurpHtml function and bound the events myself
               using jQuery instead of backbone in order to reduce
               DOM bloat */
            events: {
                'click li[data-nav="reports"]': 'reportsClicked',
                'click li[data-nav="help"]': 'helpClicked',
                'click li[data-js="contentBtn"]': 'campaignListClicked'
            },

            /* see templates/targetadmin/client_home.html for example
               invocation, could certainly be cleaner */
            setup: function (options) {
                _.extend(this, options);
                this.model.on("change:state", this.renderState, this);
                return this;
            },

            /* creates DOM structure based on the model passed into this.setup */
            render: function () {
                this.slurpHtml({
                    template: template(this.model.toJSON()),
                    insertion: {$el: this.$el.prependTo(this.parentEl)}
                });
                this.renderState();
                return this;
            },

            /* style 'selected' button, show selected content */
            renderState: function () {
                var currentState = this.model.get('state'),
                    previousState = this.model.previous('state'),
                    contentBtn = this.templateData.contentBtn,
                    currentView;

                if (contentBtn && currentState) {
                    contentBtn.removeClass('selected')
                        .filter("li[data-nav='" + currentState + "']")
                        .addClass('selected');

                    if (previousState) { 
                        this.views[previousState].$el.fadeOut();
                    }

                    currentView = this.views[currentState];
                    if (currentView) {
                        currentView.trigger('sidebarSelected', (previousState || null));
                    }
                }
            },

            /* a nav item with associated content already on the page
                has been clicked, update the state, and let the associated
                content know that its top level nav has been clicked by
                triggering an event */
            contentItemClicked: function (event) {
                this.model.set("state", $(event.currentTarget).data('nav'));
            },

            campaignListClicked: function () {
                window.location = this.campaignListURL;
            },

            /* hacky, should be associated with nav structure
               ( perhaps with button type ), reports nav item has been clicked, redirect */
            reportsClicked: function () {
                window.location = this.reportingDashboardURL;
            },

            /* hacky, help nav item has been clicked, open mail */
            helpClicked: function () {
                window.open("mailto:help@edgeflip.com");
            }
        } ) )();
    }
);
