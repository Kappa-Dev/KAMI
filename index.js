define(["ressources/d3/d3.js","ressources/simpleTree.js","ressources/LayerGraph.js","ressources/GraphFactory.js","ressources/converter.js"],function(d3,Tree,Graph,GraphFactory,converter){
	(function pageLoad(){
		var server_url = "https://api.executableknowledge.org/iregraph/";
		var main_ct_id = "main_container";
		var root = "/";
		var hie_tree = new Tree();
		var graphs = {};
		graphs[root] = GraphFactory.rootGraph();
		var main_container = d3.select("body").append("div").attr("id",main_ct_id);
		var dispatch = d3.dispatch("dataLoaded","hStateChange","graphFileLoaded");
		//var hie_gui = new Hierarchy(hie_tree,dispatch);
		
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
							.classed("removable_tab",true)
							.on("click",function(){
								var file=document.getElementById("import_f").files;
								if(typeof(file)!="undefined" && file !=null && file.length>0){
									for(var i=0;i<file.length;i++)
										loadFile(file[i]);
								}else alert("No input file.");
});
	var loadFile = function(data){
				var ka = new FileReader();
				ka.readAsDataURL(data);
				ka.onloadend = function(e){
					converter.kamiToRegraph(e.target.result,dispatch);
				}
	}

dispatch.on("graphFileLoaded",function(graph){
	converter.exportGraph(graph);
});
}())
		
		
	
});
	