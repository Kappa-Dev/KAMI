define([
	"ressources/d3/d3.js",
	"ressources/simpleTree.js",
	"ressources/Hierarchy.js",
	"ressources/converter.js",
	"ressources/InputFileReader.js",
	"ressources/requestFactory.js",
	"ressources/InterractiveGraph.js"
	],
	function(d3,Tree,Hierarchy,converter,InputFileReader,RFactory,InterractiveGraph){
	
	(function pageLoad(){
		var server_url = "https://api.executableknowledge.org/iregraph";
		var main_ct_id = "main_container";
		var root = "/";
		var current_graph=null;
		d3.select("body").append("div").attr("id",main_ct_id);
		var main_container = d3.select("#"+main_ct_id);
		var dispatch = d3.dispatch("graphExprt","graphFileLoaded","hieUpdate","tabUpdate","graphUpdate","graphSave","tabMenu");
		main_container.append("div").attr("id","top_chart");
		main_container.append("div").attr("id","bottom_top_chart");
		var container = main_container.append("div").attr("id","container");
		container.append("div").attr("id","side_menu");//main div of side menu
		var graph_frame = container.append("div").attr("id","graph_frame");//main div of graph
		var side_ct=graph_frame.append("div").attr("id","drag_bar_cont");
			side_ct.append("div").attr("id","drag_bar").on("click",dispatch.call("tabMenu",this));//add a drag bar for the menu
		var factory = new RFactory(server_url);
		var hierarchy = new Hierarchy("top_chart",dispatch,server_url);
		hierarchy.update(root);
		var input_hie = new InputFileReader("top_chart",dispatch,server_url);
		var graph_pan = new InterractiveGraph("graph_frame",dispatch,server_url);
		dispatch.on("graphUpdate",function(abs_path){
			current_graph=abs_path;
			factory.getGraph(current_graph,function(err,ret){graph_pan.update(ret,current_graph)});
		});
		dispatch.on("graphFileLoaded",function(graph){
			function callback(err,ret){
				if(!err){
					dispatch.call("hieUpdate",this,null);
					console.log(ret);
				}
				else console.error(err);
			};
			if(graph.type=="Hierarchy"){
				factory.addHierarchy(root+graph.hierarchy.name,
					JSON.stringify(graph.hierarchy,null,"\t"),
					callback
				);
			}else if(graph.type=="Graph"){
				var isSlash =current_graph=="/"?"":"/";
				factory.addHierarchy(current_graph+isSlash+graph.hierarchy.name,
					JSON.stringify(graph.hierarchy,null,"\t"),
					callback
				);
			}else if(graph.type=="Rule"){
				console.log("not implemented");
			}
		});
		dispatch.on("graphExprt",function(){
			factory.getGraph(current_graph,function(err,ret){converter.exportGraph({hierarchy:ret})});
		});
		dispatch.on("hieUpdate",function(){
			hierarchy.update(root);
			current_graph=null;
			//clean graph svg.
		});
	}())
});
	