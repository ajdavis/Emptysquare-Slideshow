var imageId = 0;

/* Show the proper image after updating imageId.
 */
function navigateToImageId() {
    // Start clean -- the div can't be completely empty or it won't respect its
    // height and width styles, so put an nbsp in it
    $("#left_arrow").html('&nbsp;').unbind('click');
    $("#right_arrow").html('&nbsp;').unbind('click');
    $("#photo").unbind('click');
    
	/**
	 *  Show or hide the left and right arrows depending on current position in
	 * list of photos - recall that our internal imageId is 0-indexed, but
	 * we use 1-based indices in the UI
	 */
	if (imageId > 0) {
		$("#left_arrow")
		.html('<img src="emptysquare_slideshow_arrow_left.gif" />')
        .click(go_left);
	}
	
	if (imageId < photos['photo'].length - 1) {
		$("#right_arrow")
        .html('<img src="emptysquare_slideshow_arrow_right.gif" />')
        .click(go_right);
        
        $("#photo").click(go_right);
	}
	
	/**
	 * Update the displayed image id
	 */
	$("#photo_index_span").html("" + (imageId + 1));
	
	$("#photo_caption").html(photos['photo'][imageId]['description']);
    $("#photo_credit_span").html(photos['photo'][imageId]['owner_realname']);
    $("#flickr_link").attr('href', photos['photo'][imageId]['flickr_url']);

    if (show_titles) {
        $("#photo_title").html(photos['photo'][imageId]['title']);
    }
	/**
	 * Show the image
	 */
	setImage(photos['photo'][imageId].image);
	
	return false;
}

/* Show a photo
 * @param image:	An Image object
 */
function setImage(image) {
	$("#photo").empty().append(image);
}

/* Preload all photos in the photos array
 * @param preload_image_id:	Which image to preload, or -1 for all photos
 * @param onload_function:	Function to call when image has loaded
 */
function preloadImage(preload_image_id, onload_function) {
	var imageObj = new Image();
	imageObj.imageId = preload_image_id;
	photos['photo'][preload_image_id].image = imageObj;
	
	$(imageObj).load(function() {
		// As soon as image loads, show it if it's the current image
		if (imageId == this.imageId) {
			setImage(this);
		}
        
		if (onload_function) onload_function();
	});
	
	// Trigger a preload
	imageObj.src = photos['photo'][preload_image_id]['source'];
}

function go_left() {
    imageId -= 1;
    navigateToImageId();
}

function go_right() {
    imageId += 1;
    navigateToImageId();
}

/* Call this in $(document).ready()
 * @param photos:       An array of objects, not the actual photos but
 *                      information about them
 */
function emptysquare_slideshow_onready(photos) {
	// Load current image first to maximize speed, then load remaining photos
    preloadImage(0, function() {
        navigateToImageId();
        
		for (var i = 0; i < photos['photo'].length; i++) {
			// Don't load the first image twice
			if (i != 0) {
				preloadImage(i, null);
			}
		}
	});
}
