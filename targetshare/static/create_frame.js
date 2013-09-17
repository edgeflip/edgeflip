/* I am (should be) a copy of static/js/create_frame.js.
*  FIXME: Get rid of me!
*/
(function() {
	var efDiv = document.getElementById('ef_frame_div');

	// Determine appropriate frame_faces URL base -- PROTOCOL://HOST/frame_faces
	var efFrameURL = (function() {
		var child, host;
		var parser = document.createElement('a');
		for (var childIndex = 0; childIndex < efDiv.children.length; childIndex++) {
			child = efDiv.children[childIndex];
			parser.href = child.src;
			host = parser.host;
			if (host.indexOf('edgeflip.com') != -1) {
				return parser.protocol + "//" + host + "/frame_faces";
			}
		}
	})();

	// Collect window URL parameters
	var urlparams = {};
	window.location.href.replace(/[?&]+([^=&]+)=([^&]*)/gi, function(m, key, value) {
		// Note -- if our param appears multiple times in the URL, this will only take the last one!
		urlparams[key] = value;
	});

	// Complete frame_faces URL path from window URL parameters
	if (urlparams['efcmpgslug']) {
		efFrameURL += '/' + urlparams['efcmpgslug'];
	} else {
		efFrameURL += '/' + urlparams['efcmpg'] + '/' + urlparams['efcnt'];
	}

	// Carry certain URL parameters through
	efFrameURL += (function() {
		// TODO: session id's will eventually migrate to cookies
		var carryThroughKeys = ['efsid', 'efsrc'];
		var paramKey, paramValue, queryPairs = [];
		for (var paramIndex = 0; paramIndex < carryThroughKeys.length; paramIndex++) {
			paramKey = carryThroughKeys[paramIndex];
			paramValue = urlparams[paramKey];
			if (paramValue) {
				queryPairs.push(encodeURIComponent(paramKey) + "=" + encodeURIComponent(paramValue));
			}
		}
		var queryString = queryPairs.join('&');
		if (queryPairs.length > 0) {
			queryString = '?' + queryString;
		}
		return queryString;
	})();

	// Construct frame HTML
	var efFrameStyle = 'style="width: 100%; height: 900px; border: none; margin-top: 30px;"';
	var efFrameHTML = '<iframe src="' + efFrameURL + '" id="faces_frame" ALLOWTRANSPARENCY="true" ' + efFrameStyle + '></iframe>';
	var efTempDiv = document.createElement('div');
	efTempDiv.innerHTML = efFrameHTML;
	efDiv.appendChild(efTempDiv.firstChild);
})();
