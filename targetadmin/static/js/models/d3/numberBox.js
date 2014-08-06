define(
    [
      'vendor/backbone',
      'vendor/underscore',
      'models/d3/widget'
    ],
    function( Backbone, _, BaseModel ) {

        return BaseModel.extend( {

            defaults: function(options) {
                return _.extend(
                    {},
                    BaseModel.prototype.defaults,
                    {
                        spacing: 25,
                        numberHeight: 0
                    }
                );
            },

            initialize: function(options) {

                this.on( "change:titleHeight change:numberHeight", this.calculateHeight, this );

                return this;
            },

            calculateHeight: function() {

                if( this.has('titleHeight') && this.has('numberHeight') ) {
                    this.set( {
                        height: this.get('titleHeight') +
                                this.get('numberHeight') +
                                this.get('spacing') +
                                ( this.get('padding') * 2 )
                    } );
                }
            }
        } );
    }
);
