define(["ressources/d3/d3.js","ressources/d3/d3-context-menu.js"],function(d3,d3ContextMenu){
	return function InterractiveGraph(container_id,dispatch,server_url){
	var disp = dispatch;
	var svg = d3.select("#"+container_id).append("div").attr("id","tab_frame").append("svg:svg");
	var size = d3.select("#tab_frame").node().getBoundingClientRect();
	var sumulation;
	var node_data;
	var radius = 30;
	var links_f;
	(function init(){
		svg.attr("preserveAspectRatio", "xMinYMin meet")
			.attr("height",size.height)
			.attr("width",size.width)
			.classed("svg-content-responsive", true)
			.on("contextmenu",d3ContextMenu(function(){return svgMenu();}));
			simulation = d3.forceSimulation();
			var center_f = d3.forceCenter(svg.attr("width")/2,svg.attr("height")/2);
			simulation.force("center",center_f);
			var collid_f = d3.forceCollide(radius+radius/4).strength(0.9);
			simulation.force("collision",collid_f);
			links_f = d3.forceLink()
				.id(function(d){return d})
				.distance(function(d){return d.source.type==d.target.type?radius/2:radius*2});
			simulation.force("links",links_f);
			var many_f = d3.forceManyBody()
				.strength(-30)
				.distanceMin(radius/2);
			simulation.force("charge",many_f);
			simulation.on("tick",function(){
				console.log(simulation.alpha());
				
				var nodes = svg.selectAll("g.node");
				nodes.attr("transform", function(d) {
					d.x=Math.max(20, Math.min(svg.attr("width") - 20, d.x));
					d.y=Math.max(20, Math.min(svg.attr("height") - 20, d.y));
					return "translate(" + d.x + "," + d.y + ")"; 
				});
				svg.selectAll(".link")
					.attr("x1", function(d){ return d.source.x;})
					.attr("y1", function(d){ return d.source.y;})
					.attr("x2", function(d){ return d.target.x;})
					.attr("y2", function(d){ if (d.source.id == d.target.id) return d.target.y-60;return d.target.y;});
			});
			simulation.stop();
			
	}());
	
	this.update = function update(graph){
		svg.selectAll("*").remove();
		loadGraph(graph);	
	};
	function findNode(n,graph){
		var ret=graph.filter(function(e){
			return e.id==n;		
		});
		return ret[0];
	}
	function loadGraph(response){
		var links = response.edges.map(function(d){
			return {source:findNode(d.from,response.nodes),target:findNode(d.to,response.nodes)}
		});
		var link = svg.selectAll(".link")
			.data(links, function(d) { return d.source.id + "-" + d.target.id; });
		link.enter().insert("line","g")
			.classed("link",true)
			.on("contextmenu",d3ContextMenu(function(){return edgeCtMenu();}));
		link.exit().remove();
		var node = svg.selectAll("g.node")
			.data(response.nodes, function(d) {return d.id;});
		var node_g = node.enter().insert("g")
			.classed("node",true)
			.on("contextmenu",d3ContextMenu(function(){return nodeCtMenu();}));
			svg.selectAll("g.node").each(function(d){if(d.type) d3.select(this).classed(d.type,true)});
		node_g.insert("circle")
			.attr("r", radius);
		node_g.insert("text")
			.classed("nodeLabel",true)
			.attr("x", 0)
			.attr("dy", ".35em")
			.attr("text-anchor", "middle")
			.text(function(d) {return d.id})
			.attr("font-size", "7px");
		node.exit().remove();
		d3.selectAll("g.node").call(d3.drag().on("start", dragstarted));
		simulation.nodes(response.nodes);
		links_f.links(links);
		simulation.alpha(1);
		simulation.restart();
	};
	function svgMenu(){
		var menu = [];
		return menu;
	};
	function edgeCtMenu(){
		var menu = [];
		return menu;
	}
	function dragstarted();

};});