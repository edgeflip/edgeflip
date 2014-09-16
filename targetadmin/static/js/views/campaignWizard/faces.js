/* Module exporting the faces section of the campaign wizard */
define(
    [
      'jquery',
      'vendor/underscore',
      'extendBackbone',
      'views/campaignWizard/util/imageCompanion',
      'templates/campaignWizard/faces'
    ],
    function( $, _, Backbone, imageCompanion, template ) {

        /* Note this extends the imageCompanion view */
        return imageCompanion.extend( {

            template: template,

            events: function() {
                return _.extend( 
                    imageCompanion.prototype.events,
                    { 
                      'click *[data-js="nextStep"]': 'validateInputs',
                      'click *[data-js="prevStep"]': 'goBack'
                    }
                );
            },

            /* call image companion initialization, listen for validation */
            initialize: function(options) {

                imageCompanion.prototype.initialize.call(this, options);

                this.on( 'validated', this.triggerNextStep );

                return this;
            },

            /* data structure which maps the input elements to
               the popover displayed on the image -- I'd say
               put this on the server, in the db */
            fields: {
                'sharing_prompt': {
                    hoverText: 'Your headline will go here.',
                    imageCoords: { x: 457, y: 63 },
                    placement: 'bottom'
                },
                'sharing_sub_header': {
                    hoverText: 'Your sub-heading will go here.',
                    imageCoords: { x: 457, y: 145 },
                    placement: 'bottom'
                },
                'sharing_button': {
                    hoverText: 'What should the sharing button say?',
                    imageCoords: { x: 625, y: 804 },
                    placement: 'left'
                },
                'thanks_url': {
                    hoverText: "Where should we send your supporters once they've shared with their friends?",
                    placement: 'bottom'
                },
                'error_url': {
                    hoverText: 'Where should we send your supporters in case something goes wrong?',
                    placement: 'bottom'
                },
                'faces_url': {
                    hoverText: 'Leave this blank unless you plan to host the Friend Suggestion Page on your site.',
                    placement: 'bottom'
                }
            },

            triggerNextStep: function() {
                this.trigger('nextStep');
            },
            
            goBack: function() {
                this.trigger('previousStep');
            }
            
        } );
    }
);
