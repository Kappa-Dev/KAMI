define(["ressources/d3/d3.js","ressources/pathConvert.js"],function(d3,cvt){return function InterractiveGraph(container_id,server_url){
	var svg = d3.select("#"+container_id).append("div").attr("id","interractive_graph").append("svg:svg");
	this.init = function init(node){
		svg.selectAll("*").remove();
		var tmp_graph = loadGraph(node);
		
	};
	function loadGraph(node){
		console.log(server_url);
		var request = d3.json(server_url+"graph"+cvt.absPath(node),function(response){
				console.log(response);
			});
	};



};});