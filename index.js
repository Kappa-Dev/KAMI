define(["ressources/d3/d3.js","HierarchyFinder.js","HierarchyUpdater.js","InterractiveGraph.js"],function(d3,HierarchyFinder,HierarchyUpdater,InterractiveGraph){
	(function pageLoad(){
		var server_url = "https://api.executableknowledge.org/iregraph/";
		var main_ct_id = "main_container";
		var main_container=d3.select("body").append("div").attr("id",main_ct_id);
		var hf = new HierarchyFinder(main_ct_id,server_url); hf.init("/");
		var hu = new HierarchyUpdater(main_ct_id,server_url,hf);
		var svg = new InterractiveGraph(main_ct_id,server_url,hf); svg.init(["/"]);
		
		
	
	
	
	
	
	
	
	
	
	
	}());
});
	