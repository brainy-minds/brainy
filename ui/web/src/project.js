function renderMustache(data) {
	var template = $('body').html();
  	Mustache.parse(template);
  	var rendered = Mustache.render(template, data);
  	$('body').html(rendered);	
}

jQuery(document).ready(function(){
	
	var data = {
		project: {
			name: 'foo'
		}		
	}

	$.get('../reports.json', data, function(){
		console.log(data);
	});

	
});
