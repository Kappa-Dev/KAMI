define(["ressources/d3/d3.js","ressources/Convert.js","ressources/d3/d3-context-menu.js"],function(d3,cvt,d3ContextMenu){return function InterractiveGraph(container_id,server_url,dispatch){
	var disp = dispatch;
	var svg = d3.select("#"+container_id).append("div").classed("interractive_graph",true).append("svg:svg");
	var size = d3.select("#"+container_id).select(".interractive_graph").node().getBoundingClientRect();
	var sumulation;
	var node_data;
	svg.attr("preserveAspectRatio", "xMinYMin meet")
		.attr("height",size.height)
		.attr("width",size.width)
		.classed("svg-content-responsive", true)
		.on("contextmenu",d3ContextMenu(function(){return svgMenu();}));
	this.init = function init(graph){
		svg.selectAll("*").remove();
		simulation = d3.forceSimulation();
		simulation.stop();
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
				.data(response.nodes, function(d) {return d.id;});
			var node_g = node.enter().insert("g")
				.classed("node",true)
				.on("contextmenu",d3ContextMenu(function(){return nodeCtMenu();}));
			//.classed(function(d){return d.ttype?d.ttype:"node";},true)
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
		console.log("Data");
		simulation.nodes(response.nodes);
//simulation.force("center", d3.forceCenter([300,400]))
			simulation.force("collision",d3.forceCollide([22]));
			simulation.force("links",d3.forceLink(function(){return response.edges.map(function(e,i){return {source:e.from,target:e.to,index:i}})}));
			simulation.on("tick",function(){
				console.log("in tick");
				svg.selectAll("g.node").attr("transform", function(d) {
					d.x=Math.max(20, Math.min(svg.attr("width") - 20, d.x));
					d.y=Math.max(20, Math.min(svg.attr("height") - 20, d.y));
					return "translate(" + d.x + "," + d.y + ")"; 
				});
				
			});
			simulation.restart();
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