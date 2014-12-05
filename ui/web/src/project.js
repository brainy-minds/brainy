function basename(path) {
   return path.split(/[\\/]/).pop();
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
		}
	}
	return reports;
}


jQuery(document).ready(function(){

	var data = {};

	$.get('reports.json', function(reports){
		data.reports = addReportNames(reports);
		// console.log(reports);
		var report_file = basename(reports.reports_list[0]);
		$.get('/reports/' + report_file, function(report) {			
			data.report = report;
			renderMustache(data);
		});
	});

});
