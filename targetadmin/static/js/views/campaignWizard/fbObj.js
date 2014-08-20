define(
    [
      'jquery',
      'vendor/underscore',
      'extendBackbone',
      'views/campaignWizard/util/imageCompanion',
      'templates/campaignWizard/fbObj'
    ],
    function( $, _, Backbone, imageCompanion, template ) {

        return imageCompanion.extend( {
            
            template: template,

            fields: {
                'org_name': {
                    hoverText: 'The cause or organization you enter will appear here.',
                    imageCoords: { x: 540, y: 80 },
                    placement: 'bottom'
                },
                'msg1_pre': {
                    hoverText: 'This text will go before the friend names.',
                    imageCoords: { x: 56, y: 206 },
                    placement: 'bottom'
                },
                'msg1_post': {
                    hoverText: 'This text will go after the friend names.',
                    imageCoords: { x: 519, y: 204 },
                    placement: 'bottom'
                },
                'msg2_pre': {
                    hoverText: 'Suggest a second message.',
                    imageCoords: { x: 56, y: 206 },
                    placement: 'bottom'
                },
                'msg2_post': {
                    hoverText: 'Suggest a second message.',
                    imageCoords: { x: 519, y: 204 },
                    placement: 'bottom'
                },
                'og_title': {
                    hoverText: "Your title will go here.",
                    imageCoords: { x: 386, y: 754 },
                    placement: 'bottom'
                },
                'og_image': {
                    hoverText: 'Your image will go here.',
                    imageCoords: { x: 641, y: 417 },
                    placement: 'right'
                },
                'og_description': {
                    hoverText: 'Your description will go here.',
                    imageCoords: { x: 464, y: 861 },
                    placement: 'bottom'
                },
                'content_url': {
                    hoverText: 'Where should we send people who click on the Facebook post?',
                    placement: 'bottom'
                }
            }

        } );
    }
);
