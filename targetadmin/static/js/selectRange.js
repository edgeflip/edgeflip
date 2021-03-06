define(['jquery'], function ($) {
    $.fn.selectRange = function (start, end) {
        if (!end) end = start; 
        return this.each(function () {
            if (this.setSelectionRange) {
                this.setSelectionRange(start, end);
            } else if (this.createTextRange) {
                var range = this.createTextRange();
                range.collapse(true);
                range.moveEnd('character', end);
                range.moveStart('character', start);
                range.select();
            }
        });
    };
});
