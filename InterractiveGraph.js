define(["ressources/d3/d3.js","ressources/Convert.js","ressources/d3/d3-context-menu.js"],function(d3,cvt,d3ContextMenu){return function InterractiveGraph(container_id,server_url,dispatch){
	var disp = dispatch;
	var svg = d3.select("#"+container_id).append("div").classed("interractive_graph",true).append("svg:svg");
	var size = d3.select("#"+container_id).select(".interractive_graph").node().getBoundingClientRect();
	svg.attr("preserveAspectRatio", "xMinYMin meet")
		.attr("height",size.height)
		.attr("width",size.width)
		.classed("svg-content-responsive", true)
		.on("contextmenu",d3ContextMenu(function(){return svgMenu();}));
	this.init = function init(graph){
		svg.selectAll("*").remove();
		loadGraph(graph);	
	};
	function loadGraph(graph){
		d3.json(server_url+"graph"+cvt.absPath(graph),function(response){
			if(!response) {
				console.error("No graph");
				return;
			};
			console.log("loading graph");
			console.log(response);
			var link = svg.selectAll(".link")
				.data(response.edges, function(d) { return d.from + "-" + d.to; });
			link.enter().insert("line","g")
				.classed("link",true)
				.on("contextmenu",d3ContextMenu(function(){return edgeCtMenu();}));
			link.exit().remove();
			var node = svg.selectAll("g.node")
				.data(response.nodes, function(d) { return d.id;});
			var node_g = node.enter().insert("g")
				.classed("node",true)
				.classed(function(d){return d.ttype;},true)
				.on("contextmenu",d3ContextMenu(function(){return nodeCtMenu();}));
		node_g.insert("circle")
			.attr("r", 20);
		node_g.insert("text")
			.classed("nodeLabel",true)
			.attr("x", 0)
			.attr("dy", ".35em")
			.attr("text-anchor", "middle")
			.text(function(d) {return d.id})
			.attr("font-size", "7px");
		node.exit().remove();
		});
	};
	function svgMenu(){
		var menu = [];
		return menu;
	};
	function edgeCtMenu(){
		var menu = [];
		return menu;
	}

};});