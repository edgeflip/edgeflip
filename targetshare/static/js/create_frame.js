(function() {
	var efDiv = document.getElementById('ef_frame_div');
    var script_src = efDiv.children[0].src;

	var efFrameURL = script_src.replace('/static/create_frame.js', '/frame_faces');


	var urlparams = {};

	var parts = window.location.href.replace(/[?&]+([^=&]+)=([^&]*)/gi, function(m,key,value) {
		urlparams[key] = value;
		// Note -- if our param appears multiple times in the URL, this will only take the last one!
	});

	if (urlparams['efcmpgslug']) {

		var efSlug = urlparams['efcmpgslug'];
		efFrameURL = efFrameURL + '/' + efSlug;

	} else {

		var efCampaignId = urlparams['efcmpg'];
		var efContentId = urlparams['efcnt'];

		efFrameURL = efFrameURL + '/' + efCampaignId + '/' + efContentId

	}

	// session id's will eventually migrate to cookies...
	var efSessionId = urlparams['efsid'];
	if (efSessionId) {
		efFrameURL = efFrameURL + '?efsid=' + efSessionId;
	}

	var efFrameStyle = 'style="width: 100%; height: 900px; border: none; margin-top: 30px;"'

	var efFrameHTML = '<iframe src="'+efFrameURL+'" id="faces_frame" ALLOWTRANSPARENCY="true" '+efFrameStyle+'></iframe>';
	var efTempDiv = document.createElement('div');
	efTempDiv.innerHTML = efFrameHTML;
	efDiv.appendChild(efTempDiv.firstChild);
}());
