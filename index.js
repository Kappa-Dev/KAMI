define(["ressources/d3/d3.js","HierarchyFinder.js","HierarchyUpdater.js","InterractiveGraph.js","ressources/simpleTree.js"],function(d3,HierarchyFinder,HierarchyUpdater,InterractiveGraph,Tree){
	(function pageLoad(){
		var server_url = "https://api.executableknowledge.org/iregraph/";
		var main_ct_id = "main_container";
		var root = "/";
		var main_container = d3.select("body").append("div").attr("id",main_ct_id);
		var dispatch = d3.dispatch("load","statechange","hieupdate","gupdate");
		var hierarchy = new Tree();
		var graphs = {};
		var hf = new HierarchyUpdater(main_ct_id,server_url,dispatch,hierarchy);
		var ig = new InterractiGraph(main_ct_id,server_url,dispatch);
		hf.load(root);
		dispatch.on("load.hierarcy",function(){//when the hierrachy is loaded
			graphs[root] = GraphFactory.rootGraph();
			graphs[hierarchy.getSons(root)[0]] = new Graph();
			ig.loadGraph(graphs[hierarchy.getSons(root)[0]],hierarchy.getSons(root)[0]);
			ig.editable(false);
		});
		
		
		
		
		
	
	
	
	
	
	
	
	
	
	
	}());
});
	