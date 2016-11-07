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
		dispatch.on("load",function(){
			graphs[root] = ig.rootGraph();
			ig.loadGraph(graphs[root],{n:"r",e:"r",s:"r"});
			
		})
		dispatch.on("hieUpdate",function(){
			console.log("reload hierarchy");
			hf.init();
		});
		dispatch.on("statechange.hrF",function(path){
			console.log("updating svg graph");
				svg.init(path);
		});
		
		
		
		
		
	
	
	
	
	
	
	
	
	
	
	}());
});
	