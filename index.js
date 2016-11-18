define(["ressources/d3/d3.js","ressources/simpleTree.js","ressources/LayerGraph.js","ressources/GraphFactory.js","ressources/converter.js"],function(d3,Tree,Graph,GraphFactory,converter){
	(function pageLoad(){
		var server_url = "https://api.executableknowledge.org/iregraph/";
		var main_ct_id = "main_container";
		var root = "/";
		//var hie_tree = new Tree();
		//var graphs = {};
		//graphs[root] = GraphFactory.rootGraph();
		d3.select("body").append("div").attr("id",main_ct_id);
		var main_container = d3.select("#"+main_ct_id);
		var dispatch = d3.dispatch("graphFileLoaded","coordFileLoaded","hieUpdate","tabUpdate","graphUpdate");
		main_container.append("div").attr("id","topchart");
		main_container.append("div").attr("id","botom_topchart");
		main_container.append("div").attr("id","sliding_container");
		main_container.select("#sliding_container").append("div").attr("id","menu_container");
		main_container.select("#sliding_container").append("div").attr("id","graph_container");
		var hierarchy = HierarchyFactory.rootHierarchy("#topchart",dispatch,server_url,root);
		kamiModule.addInputFile("#topchart",dispatch,server_url);
		kamiModule.addExportFile("#topchart",dispatch,server_url);
		kamiModule.addConfig("#topchart",main_ct_id,dispatch,server_url);
		kamiModule.addTabMenu("#menu_container",dispatch,server_url);
		var main_graph = GraphFactory.rootGraph("#graph_container",dispatch,server_url);
		var editor = GraphFactory.graphEditor("#sliding_container",dispatch,server_url);
		
		
		d3.select("#main_container").append("div").attr("id","menu");
	d3.select("#menu").append("form").attr("id","menu_f");
	var tmp_form=d3.select("#menu_f");
	tmp_form.append("input").attr("type","file")
							.attr("id","import_f")
							.attr("value","data.json")
							.classed("removable_tab",true)
							.attr("multiple",true);
	tmp_form.append("input").attr("type","button")
							.attr("id","import")
							.attr("value","Import Data")
							.attr("accept",".json,.JSON,.Json,.coord,.COORD,.Coord")
							.classed("removable_tab",true)
							.on("click",function(){
								var file=document.getElementById("import_f").files;
								if(typeof(file)!="undefined" && file !=null && file.length>0){
									for(var i=0;i<file.length;i++){
											loadFile(file[i]);
									}
								}else alert("No input file.");
});
	var loadFile = function(data){
				var ka = new FileReader();
				ka.readAsDataURL(data);
				ka.onloadend = function(e){
					if(data.name.split(".")[1]=="json")
						converter.kamiToRegraph(e.target.result,dispatch);
					else if(file.name.split(".")[1]=="coord")
						converter.loadCoord(e.target.result,main_graph);
				}
	};

dispatch.on("graphFileLoaded",function(graph){
	if(!main_graph)
		main_graph = new interractiveGraph(graph.hierarchy.name);
	//converter.exportGraph(graph);
});
}())
		
		
	
});
	