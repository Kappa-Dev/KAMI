/* Load the Gui and handle broadcasted events.
 * This module is automaticaly loaded at page loading.
 * @ Author Adrien Basso blandin
 * This module is part of regraphGui project
 * this project is under AGPL Licence
*/
define([
	"ressources/d3/d3.js",
	"ressources/simpleTree.js",
	"ressources/Hierarchy.js",
	"ressources/converter.js",
	"ressources/InputFileReader.js",
	"ressources/requestFactory.js",
	"ressources/InterractiveGraph.js",
	"ressources/SideMenu.js",
	"ressources/ConfigTab.js"
	],
	function(d3,Tree,Hierarchy,converter,InputFileReader,RFactory,InterractiveGraph,SideMenu,ConfigTab){
	//Regraph Gui Core
	(function pageLoad(){
		//this section must be changed to feet the server/user requirement.
		var server_url = "http://localhost:5000";
		var main_ct_id = "main_container";
		var root = "/";
		var current_graph="/";
		//end of config section : Todo : add this section as a config html page.
		//dispatch event between modules
		var dispatch = d3.dispatch(
			"addGraph", //triggered when the add Graph button is clicked
			"graphExprt", //triggered then the graph export button is clicked
			"graphFileLoaded",//triggered when the import button is clicked
			"hieUpdate",//triggered when a module change the hierarchy
			"tabUpdate",//triggered when the content of the tab Menu need to be changed 
			"graphUpdate",//triggered when a module change the current graph showed
			"graphSave",//triggered when the edition box is closed and saved ----->TODO
			"tabMenu",//triggered when the tab scroller is clicked
			"configUpdate"//triggered when the graph shown is changed
		);
		d3.select("body").append("div").attr("id",main_ct_id);
		var main_container = d3.select("#"+main_ct_id);//Main div
		//main_container.append("div")//separator between menu and page core
		//	.attr("id","bottom_top_chart");
		var container = main_container.append("div")//page core
			.attr("id","container");
		main_container.append("div")//top menu
			.attr("id","top_chart");
		// var side = container.append("div")//main div of side menu
		// 	.attr("id","side_menu");
		var graph_frame = container.append("div")//main div of graph
			.attr("id","graph_frame");
		// var side_ct=graph_frame.append("div")//add the vertical separator container
		// 	.attr("id","drag_bar_cont");
		// side_ct.append("div")//add a drag bar for the menu
		// 	.attr("id","drag_bar")
		// 	.on("click",function(){return dispatch.call("tabMenu",this)});
		//request factory for the given regraph server
		var factory = new RFactory(server_url);
		//regraph hierarchy
		var hierarchy = new Hierarchy("top_chart",dispatch,server_url);
		hierarchy.update(root);
		//modification menu : add, export and new graph + file input + type selector
		var input_hie = new InputFileReader("top_chart",dispatch,server_url);

		//configuration menu : change serveur url, node color, size and shape.
		var config = new ConfigTab("top_chart",dispatch,server_url);
		config.init();

		//the graph showed : TODO -> maybe a graph list to avoid reloading each graph.
		var graph_pan = new InterractiveGraph("graph_frame",dispatch,server_url);
		//the side menu
		//var side_menu = new SideMenu("side_menu",dispatch,server_url);
		/* dispatch section
		 * here each dispatch event is handled
		 */
		 /* On tabMenu : open or close the tab menu
		  */
		 dispatch.on("tabMenu",function(){
			d3.event.stopPropagation();
			var size=side.style("width")!="0px"?"0px":"15.6%";
			side.style("min-width",size);
			graph_frame.style("margin-left",size);
			side.style("width",size);
		 });
		 /* On tabUpdate : change the tab content
		  * @input : g_id : the current object in the hierarchy
		  * @input : up_type : the type of content
		  */
		// dispatch.on("tabUpdate",function(g_id,sons,fth,up_type){
		// 	side_menu.load(g_id,sons,fth,up_type);
		// });
		/* On addGraph : add a new graph to the current graph in the Hierarchy 
		 * @input : type : the type of element to add : Graph, Hierarchy, Rule
		 * if the request succeed, add a new graph, else, throw error
		 * TODO : change server rule to to allow graph and rule adding
		 */
		dispatch.on("addGraph",function(type){
			var name=prompt("Give it a name !", "model_"+(Math.random()).toString());
			var isSlash =current_graph=="/"?"":"/";
			if(type=="Graph" || type=="Rule"){
				console.log("server Error... Using addHierarchy instead");
			}
			factory.addHierarchy(current_graph+isSlash+name,
				JSON.stringify({name:name,top_graph:{edges:[],nodes:[]},children:[]},null,"\t"),
				function(err,ret){
					if(!err){
						dispatch.call("hieUpdate",this,null);
						console.log(ret);
					}
					else console.error(err);
				}
			);
		});
		dispatch.on("configUpdate",function(type_graph){
			config.loadGraphConf(type_graph);
		});
		
		
		
		/* On graphUpdate : get the new graph to show from server and load it in the UI
		 * @input : abs_path : the absolute path of the graph in the hierarchy
		 * if the request succeed, the new graph is loaded on screen
		 */
		dispatch.on("graphUpdate",function(abs_path){
			current_graph=abs_path;
			factory.getGraph(
				current_graph,
				function(err,ret){
					graph_pan.update(ret,current_graph);
				}
			);
		});
		/* On graphFileLoaded : Load a graph into the server and update Gui
		 * @input : graph : graph to add (may be Hierarchy, Graph or Rule)
		 * if the request succeed, the new graph is loaded on screen and the hierarchy updated
		 * TODO : change server rule to to allow graph and rule adding
		 */
		dispatch.on("graphFileLoaded",function(graph){
			function callback(err,ret){
				if(!err){
					dispatch.call("hieUpdate",this,null);
					console.log(ret);
				}
				else console.error(err);
			};
			if(graph.hierarchy.name=="ActionGraph") //if it is a Kami old format suggest a renaming
				graph.hierarchy.name=prompt("Give it a name !", "model_"+(Math.random()).toString());
			if(graph.type=="Hierarchy"){
				factory.addHierarchy(
					root+graph.hierarchy.name,
					JSON.stringify(graph.hierarchy,null,"\t"),
					callback
				);
			}else if(graph.type=="Graph"){
				var isSlash =current_graph=="/"?"":"/";
				factory.addHierarchy(
					current_graph+isSlash+graph.hierarchy.name,
					JSON.stringify(graph.hierarchy,null,"\t"),
					callback
				);
			}else if(graph.type=="Rule"){
				console.log("not implemented");
			}
		});
		/* On graphExprt : Export the current graph as a Json File.
		 * TODO : if coordinates are set, export the config file.
		 * @input : current_graph : the current graph path in the hierarchy
		 * if the request succeed, the json file is opened in a new Window
		 */
		dispatch.on("graphExprt",function(type){
			switch(type){
				case "Hierarchy" :
				factory.getHierarchy(
					"/",
					function(err,ret){
						converter.exportGraph({hierarchy:ret});
					}
				);
				break;
				default : 
				factory.getGraph(
					current_graph,
					function(err,ret){
						converter.exportGraph({hierarchy:ret});
					}
				);
			}
		});
		/* On hieUpdate : Reload the hierarchy
		 * if the request succeed, the hierarchy menu is reloaded so is the current graph.
		 * TODO : also remove the graph
		 */
		dispatch.on("hieUpdate",function(){
			hierarchy.update(root);
			current_graph="/";
		});
	}())
});
	