define(["ressources/d3/d3.js","HierarchyFinder.js","HierarchyUpdater.js","InterractiveGraph.js"],function(d3,HierarchyFinder,HierarchyUpdater,InterractiveGraph){
	(function pageLoad(){
		var server_url = "https://api.executableknowledge.org/iregraph/";
		var main_ct_id = "main_container";
		var main_container = d3.select("body").append("div").attr("id",main_ct_id);
		var dispatch = d3.dispatch("load","statechange");
		var hf = new HierarchyFinder(main_ct_id,server_url,dispatch);
		var hu = new HierarchyUpdater(main_ct_id,server_url,dispatch);
		var svg = new InterractiveGraph(main_ct_id,server_url,dispatch); 
		hf.init("/");
		dispatch.on("load.hrF",function(node){
				svg.init(["/"]);
		});
		dispatch.on("statechange.hrF",function(path){
			console.log("updating svg graph");
				console.log(path);
				svg.init(path);
		});
		
		
		
		
		
	
	
	
	
	
	
	
	
	
	
	}());
});
	