/* IE-specifc stuff */

// IE 7 doesn't seem to implement JSON...
if (typeof JSON == 'undefined') {
	$.getScript("http://cdnjs.cloudflare.com/ajax/libs/json2/20110223/json2.min.js");
}


// IE 8 doesn't seem to implement indexOf() for arrays
if (!Array.prototype.indexOf) {
	Array.prototype.indexOf = function(obj, start) {
		for (var i = (start || 0), j = this.length; i < j; i++) {
			if (this[i] === obj) { return i; }
		}
		return -1;
	}
}

