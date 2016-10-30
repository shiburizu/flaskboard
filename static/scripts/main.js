function load() {
	var urllocation = location.href;
	if(urllocation.indexOf("#anchor") > -1){
		window.location.hash="anchor"; 
	} else {
	return false;
	}
}
