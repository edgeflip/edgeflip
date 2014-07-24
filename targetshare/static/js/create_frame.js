(function() {
    var efDiv = document.getElementById('ef_frame_div');

    // Determine approriate URL base
    var efFrameURL = (function() {
        var child, url, host, protocol;
        var parse = (function(url) {
            var parser = document.createElement('a');
            parser.href = url;
            return parser;
        });
        for (var childIndex = 0; childIndex < efDiv.children.length; childIndex++) {
            child = efDiv.children[childIndex];
            url = parse(child.src);
            host = url.host;
            if (host.indexOf('edgeflip.com') != -1) {
                protocol = url.protocol;
                // IE likes to return an invalid ":" for the protocol
                protocol = protocol == ':' ? '' : protocol;
                return protocol + "//" + host;
            }
        }
    })();

    // Collect window URL parameters
    var urlparams = {};
    window.location.href.replace(/[?&]+([^=&]+)=([^&]*)/gi, function(m, key, value) {
        // Note -- if our param appears multiple times in the URL, this will only take the last one!
        urlparams[decodeURIComponent(key)] = decodeURIComponent(value);
    });

    // Complete URL path from window URL parameters
    if (urlparams['efcmpgslug']) {
        efFrameURL += '/frame_faces/' + urlparams['efcmpgslug'];
    }
    else if (urlparams['efuuid']) {
        efFrameURL += '/faces-email/' + urlparams['efuuid'];
    } else {
        efFrameURL += '/frame_faces/' + urlparams['efcmpg'] + '/' + urlparams['efcnt'];
    }

    // Carry certain URL parameters through
    efFrameURL += (function() {
        var carryThroughKeys = ['efsrc', 'efobjsrc', 'efsuccessurl', 'eferrorurl', 'code'];
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
    var efFrameStyle = 'style="width: 100%; border: none; margin-top: 30px;"';
    var efFrameHTML = '<iframe src="' + efFrameURL + '" id="faces_frame" ALLOWTRANSPARENCY="true" ' + efFrameStyle + '></iframe>';
    var efTempDiv = document.createElement('div');
    efTempDiv.innerHTML = efFrameHTML;
    efDiv.appendChild(efTempDiv.firstChild);
})();
