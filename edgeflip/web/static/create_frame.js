(function() {
	var efFrameURL = '/frame_faces';
	var urlparams = read_url_params();

	var efSessionId = urlparams['efsid'];
	if (efSessionId) {
		efFrameURL = efFrameURL + '?efsid=' + efSessionId;
	}

	var efFrameHTML = '<iframe src="'+efFrameURL+'" id="faces_frame" ALLOWTRANSPARENCY="true"></iframe>';
	var efTempDiv = document.createElement('div');
	efTempDiv.innerHTML = efFrameHTML;

	var efDiv = document.getElementById('ef_frame_div');
	efDiv.appendChild(efTempDiv.firstChild);
}());
