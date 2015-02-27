String.prototype.contains = function(it) { return this.indexOf(it) != -1; };

function basename(path) {
   return path.split(/[\\/]/).pop();
}

var entityMap = {
	"&": "&amp;",
	"<": "&lt;",
	">": "&gt;",
	'"': '&quot;',
	"'": '&#39;',
	"/": '&#x2F;'
};

function escapeHtml(string) {
	return String(string).replace(/[&<>"'\/]/g, function (s) {
		return entityMap[s];
	});
}


function renderMustache(data) {
	var template = $('#template').html();
  	Mustache.parse(template);
  	var rendered = Mustache.render(template, data);
  	$('#rendered').html(rendered);
}

function addReportNames(reports) {
	reports.report_files = [];
	for (var i=0; i < reports.reports_list.length; i++) {		
		reports.report_files[i] = {
			path: reports.reports_list[i],
			name: basename(reports.reports_list[i])
		};
	}
	return reports;
}

function parseYaml(value) {
	try {
		return jsyaml.load(value);
	} catch (ex) {
		console.log('Failed to parse the following YAML:');
		console.log(value);
		console.error(ex.message);
	}_
}


jQuery(document).ready(function(){

	function renderMessage (message) {
			var itemClass = 'info';
			if (message.type.contains('error')) {
				itemClass = 'danger';
			} else if (message.type == 'warning') {
				itemClass = 'warning';
			} else if (message.message == 'complete') {
				itemClass = 'success';
			}
			console.log(message);
			var html = '';
			html += '<a href="#" class="list-group-item list-group-item-' + itemClass + '">';
			if ("output" in message && message.output.length > 0) {
				html += '<button type="button" class="btn btn-default btn-sm"';				
				html += ' data-toggle="modal" data-target=".bs-output-modal-lg" data-content="';
				html += escapeHtml(message.output);
				html += '"';
  				html += '><span class="glyphicon glyphicon-new-window" aria-hidden="true"></span></button>';
  				html += ' ';
			}
			html += message.message + '</a>';
			return html;
	}

	var data = {
		
		renderProcess: function() {
			var html = '';
			html += '<div class="panel panel-default">' +
			'  <div class="panel-heading">' +
			'    <h3 class="panel-title">' + this.name  + '</h3>' +
			'  </div>' +
			'  <div class="panel-body">' +
			'    <div class="list-group">';
			console.log(this);
			for (var index = 0; index < this.messages.length; index++) {
				html += renderMessage(this.messages[index]);
			}
			html += '    </div>' +
			'    <!-- more info -->' +
			'  </div>' +
			'</div>';			

			return html;
		}
	};

	$.get('reports.yaml', function(reports_yaml){
		var reports = parseYaml(reports_yaml);
		// console.log(reports);
		data.reports = addReportNames(reports);
		// console.log(reports);
		var report_file = basename(reports.reports_list[0]);
		$.get('/reports/' + report_file, function(report_yaml) {
			var report = parseYaml(report_yaml);
			console.log(report);
			$('#brainy-logo').show();
			data.report = report;
			renderMustache(data);			
			// Enable pop-ups, modals, etc.
			$("[data-toggle='popover']").popover({
    			container: 'body'
    		});
	  		$('.bs-output-modal-lg').on('show.bs.modal', function (event) {
	  			// Button that triggered the modal
  				var button = $(event.relatedTarget);
  	 			var content = button.data('content');
  	 			var container = $(this).find('.modal-body');
  	 			container.html('<pre>' + content + '</pre>');
			});
		});
	});
});
