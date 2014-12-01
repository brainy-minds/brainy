function basename(path) {
   return path.split(/[\\/]/).pop();
}

function renderMustache(data) {
	var template = $('#template').html();
  	Mustache.parse(template);
  	var rendered = Mustache.render(template, data);
  	$('#rendered').html(rendered);
}

jQuery(document).ready(function(){

	var data = {};

	$.get('reports.json', function(reports) {		
		data.reports = reports;
		// console.log(reports);
		var report_file = basename(reports.reports_list[0]);
		$.get('/reports/' + report_file, function(report) {
			console.log(report);
			data.report = report
			renderMustache(data);
		});
	});

});
