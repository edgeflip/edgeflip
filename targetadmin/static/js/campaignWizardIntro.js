( function($) {
    window.campaignWizardIntro = new ( Backbone.View.extend( {

        config: {
            bottomPadding: 10
        },

        events: {
            'click [data-js="getStartedBtn"]': 'getStartedClicked',
            'click img': 'getStartedClicked'
        },

        initialize: function() {

            this.slurpHtml();
            this.util.computeSizes();
            this.setCarouselHeight();
            this.util.window.on( 'resize', this.setCarouselHeight.bind(this) );

            this.templateData.carousel.carousel( { interval: 20000, pause: "" } );

            window.campaignWizardNameModal.$el.on( 'hide', this.cycleCarousel.bind(this) );
        },

        cycleCarousel: function() {
            this.templateData.carousel.carousel('cycle');
        },

        pauseCarousel: function() {
            this.templateData.carousel.carousel('pause');
        },

        setCarouselHeight: function() {
            this.templateData.carousel.height(
                this.util.windowHeight -
                this.templateData.carousel.offset().top -
                this.config.bottomPadding );
        },

        showCampaignNameModal: function() {
            window.campaignWizardNameModal.$el.modal();
        },

        getStartedClicked: function() {
            this.pauseCarousel();
            this.showCampaignNameModal();
        }

    } ) )( { el: '#intro' } );
} )(jQuery);
