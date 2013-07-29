/* parses query parameters out of url */
function read_url_params() {
	var urlparams = {};

	var parts = window.location.href.replace(/[?&]+([^=&]+)=([^&]*)/gi, function(m,key,value) {
		urlparams[key] = value;
		// Note -- if our param appears multiple times in the URL, this will only take the last one!
	});

	return urlparams;
}
