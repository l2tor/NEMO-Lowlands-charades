var IP = "192.168.178.18";

var socket = null;
var is_socket_open = false;
var lang = 'nl';
var countdown_timer = 3;
var item_button_state = 'start';
var current_item = null;
var answers_enabled = false;
var attempt_number = 1;

var texts = {
	'button_start': {
		'nl': 'Start',
		'en': 'Start'
	},
	'button_done': {
		'nl': 'Klaar',
		'en': 'Done'
	}
};

var self = this;

// Disable right click (for tablet)
document.addEventListener('contextmenu', event => event.preventDefault());

document.addEventListener('touchstart', function(e) {
    if (e.targetTouches.length >= 2) {
        e.preventDefault();
    }
}, {passive: false});     		


window.onload = function () {
	//socket = new WebSocket("ws://127.0.0.1:1335/ws");
	socket = new WebSocket("ws://" + this.IP + ":1335/ws");

	console.log(socket);

	socket.onopen = function () {
		console.log("Connected!");
		is_socket_open = true;
	}

	socket.onmessage = function (e) {
		//if (is_socket_open)
		//	socket.send("msgrcvd")
		if (typeof e.data == "string") {
			console.log("Text message received: " + e.data);
			var msg = e.data;

			if (msg.startsWith("show_language_choice")) {
				// Hide all other screens just to be sure
				$('#item_to_perform_container').hide();
				$('#answers').hide();
				$('#feedback').hide();
				$('#robot_thinking').hide();
				$("#language_choice").css('display', 'flex');
			}

			else if (msg.startsWith("show_item")) {
				var tmp = msg.substring(msg.indexOf('(')+1, msg.indexOf(')'));
				console.log(tmp);

				var params = JSON.parse(msg.substring(msg.indexOf('(')+1, msg.indexOf(')')));
				show_item(params);
			}

			else if (msg.startsWith("enable_item")) {
				$('#button_container').show();
				$('#item_to_perform_container').css('display', 'flex');
				//$('#button_item_to_perform').removeClass('button_inactive');
				$('#button_item_to_perform').show();	
				item_button_state = 'start';
				attempt_number = 2;
			}

			else if (msg.startsWith("hide_item")) {
				$('#item_to_perform_container').hide();
				$('#button_container').hide();				
			}

			else if (msg.startsWith("hide_classification")) {
				$('#feedback').hide();
			}

			else if (msg.startsWith("show_answers")) {
				$('#answer_overlay').hide();				
				var params = JSON.parse(msg.substring(msg.indexOf('(')+1, msg.indexOf(')')));
				attempt_number = 1;
				self.correct_answer = params["correct_answer"];

				$('.answer_block').removeClass('correct_answer');

				for (var i = 0; i < params["answers"].length; i++) {
					$('#answer' + (i+1)).attr('item', params["answers"][i]['id']);
					$('#answer' + (i+1) + "_text").text(params["answers"][i]['description'][lang]);
					$('#answer' + (i+1) + '_image').children('img').attr('src', 'images/' + params["answers"][i]['image_filename']);
				}

				$('#answers').css('display', 'flex');
				answers_enabled = true;
			}

			else if (msg.startsWith("hide_answers")) {
				$('#answers').hide();
				answers_enabled = true;				
			}

			else if (msg.startsWith("enable_answers")) {
				answers_enabled = true;
				$('#answer_overlay').hide();
			}

			else if (msg.startsWith("show_classification")) {
				$('#robot_thinking').hide();
				$('#item_to_perform_container').hide();
				var tmp = msg.substring(msg.indexOf('(')+1, msg.indexOf(')'));
				console.log(tmp);

				var params = JSON.parse(msg.substring(msg.indexOf('(')+1, msg.indexOf(')')));
				show_classification(params)
			}

			else if (msg.startsWith("show_hourglass")) {
				$('#item_to_perform_container').hide();
				$('#robot_thinking').css('display', 'flex');				
			}
		}
	}

	socket.onclose = function (e) {
		console.log("Connection closed (wasClean = " + e.wasClean + ", code = " + e.code + ", reason = '" + e.reason + "')");
		isopen = false;
		is_socket_open = null;
	}	

}

var _send = function(dest, msg) {
	socket.send(dest + ":" + msg);
}

var set_language = function(lang) {
	$("#language_choice").hide();
	this.lang = lang;
	_send("maingame", "set_language(" + lang + ")");
}

var show_item = function(item) {
	this.current_item = item;
	$('#item_to_perform_description').text(item['description'][this.lang]);
	$('#item_to_perform_image').children('img').attr('src', 'images/' + item['image_filename']);	
	$('#button_item_to_perform').text(this.texts['button_start'][this.lang]);
	// @TODO: add picture
	$('#item_to_perform_container').css('display', 'flex');
	$('#button_container').show();
	$('#button_item_to_perform').show();
	//$('#button_item_to_perform').removeClass('button_inactive');	
	this.item_button_state = 'start';
}

var item_button_pressed = function() {
	if (this.item_button_state == 'start') {
		this.item_button_state = 'disabled';
		//$('#button_item_to_perform').addClass('button_inactive');
		$('#button_item_to_perform').hide();
		this.start_countdown();
		// @TODO: add disabled class to button
	}
	else if (this.item_button_state == 'done') {
		this.item_button_state = 'start';
		$('#button_item_to_perform').text(this.texts['button_start'][this.lang]);
		this.stop_recording();
	}
}

var show_classification = function(params) {
	$('.feedback_item').removeClass('feedback_item_correct');
	$('.feedback_item').hide();

	var num_items = 5;
	if (params.length < 5) {
		num_items = params.length;
	}

	for (var i = 0; i < num_items; i++) {
		console.log(params[i]);

		$('#feedback_' + (i+1) + '_text').text(params[i]["item"]["description"][this.lang]);
		$('#feedback_' + (i+1) + '_image').children('img').attr('src', 'images/' + params[i]["item"]["image_filename"]);

		var perc = Math.round(params[i]["percentage"] * 100)
		$('#feedback_' + (i+1) + "_percentage").text(perc + "%");
		$('#feedback_' + (i+1) + "_bar").css('width', perc + '%')

		if (params[i]["item"]["id"] == this.current_item["id"]) {
			$('#feedback_item_' + (i+1)).addClass('feedback_item_correct');
		}

		$('#feedback_item_' + (i+1)).css('display', 'flex');
	}

	$('#feedback').show();	
}

var start_countdown = function() {
	this.countdown_timer = 3;

	setTimeout(function() {
		do_countdown();		
	}, 1000);
}

var do_countdown = function() {
	$('#countdown').text(this.countdown_timer);
	
	if (this.countdown_timer == 3) {
		$('#countdown').css('display', 'flex');
	}

	this.countdown_timer--;

	if (this.countdown_timer >= 0) {
		setTimeout(function() {
			do_countdown();		
		}, 1000);		
	}
	else {
		$('#countdown').hide();
		//this.item_button_state = 'done';
		//$('#button_item_to_perform').text(this.texts['button_done'][this.lang]);
		/*setTimeout(function() {
			this.item_button_state = 'start';
			$('#button_item_to_perform').text(this.texts['button_start'][this.lang]);
			this.stop_recording();			
		}, 5000);*/
	}

	if (this.countdown_timer == 0) {
		var is_practice = this.current_item['id'] == 'ball';

		this._send("kinectrecorder", "StartRecording(" + this.current_item['id'] + "," + is_practice + "," + attempt_number + ")");
		this._send("stereorecorder", "StartRecording(" + this.current_item['id'] + "," + is_practice + "," + attempt_number + ")");
	}
}

var stop_recording = function() {
	this._send("maingame", "gesture_finished");
}

var answer_selected = function(src) {
	if (answers_enabled) {
		answers_enabled = false;
		var item_selected = $(src).attr('item');
		this._send("maingame", "answer_given(" + item_selected + ")");

		if (item_selected == self.correct_answer) {
			$(src).addClass('correct_answer');
		}
		else {
			$('#answer_overlay').show();					
		}
	}
}