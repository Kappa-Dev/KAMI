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
	"ressources/ConfigTab.js",
	"ressources/requestRulesFactory.js"
	],
	function(d3,Tree,Hierarchy,converter,InputFileReader,RFactory,InterractiveGraph,SideMenu,ConfigTab,ruleFactory){
	//Regraph Gui Core
	(function pageLoad(){
		//this section must be changed to feet the server/user requirement.
		//var server_url = "http://0.0.0.0:5000";
		var server_url = "{{server_url}}";
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
			"addNugetsToInput",//triggered when finding the children of a node
			"configUpdate",//triggered when the graph shown is changed
			"loadGraph",//triggered by the menu when clicking on a graph name
			"loadRule",//triggered by the menu when clicking on a rule name 
			"loadingEnded",//triggered when a sub graph finished loading
			"move"//triggered when a subgraph moved
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

		var size = d3.select("#graph_frame").node().getBoundingClientRect();
		graph_frame.append("div")
			.attr("id", "tab_frame")
			.append("svg")
			.attr("id", "main_svg")
			.classed("svg-content-responsive",true)
			.attr("width", size.width)
			.attr("height", size.height);
        

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
		var graph_pan = new InterractiveGraph("main_svg", "sub_svg_graph",size.width,size.height, dispatch, factory);
		var sub_svg_1 = graph_pan.svg_result;
		main_svg = d3.select("#main_svg");
		//main_svg.append(graph_pan.svg_result);

		//the rule showed

		lhs_factory = new ruleFactory(server_url,function(rule){return rule["L"]})
		phs_factory = new ruleFactory(server_url,function(rule){return rule["P"]})
		rhs_factory = new ruleFactory(server_url,function(rule){return rule["R"]})

		var lhs = new InterractiveGraph("main_svg", "lhs",size.width/2,size.height/3, dispatch, lhs_factory);
		var phs = new InterractiveGraph("main_svg", "phs",size.width/2,size.height/3, dispatch, phs_factory);
		var rhs = new InterractiveGraph("main_svg", "rhs",size.width,size.height*2/3, dispatch, rhs_factory);
		main_svg.append(lhs.svg_result)
			.attr("x", 0)
			.attr("y", 0);
			// .attr("height",size.height/3)
			// .attr("width",size.width/2);

		main_svg.append(phs.svg_result)
			.attr("x", size.width / 2)
			.attr("y", 0);
			// .attr("height",size.height/3)
			// .attr("width",size.width/2);

		main_svg.append(rhs.svg_result)
			.attr("x", 0)
		    .attr("y", size.height / 3);
			// .attr("height",size.height*2/3)
			// .attr("width",size.width);

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
		// dispatch.on("addGraph",function(type){
		// 	var name=prompt("Give it a name !", "model_"+(Math.random()).toString());
		// 	var isSlash =current_graph=="/"?"":"/";
		// 	if(type=="Graph" || type=="Rule"){
		// 		console.log("server Error... Using addHierarchy instead");
		// 	}
		// 	factory.addHierarchy(current_graph+isSlash+name,
		// 		JSON.stringify({name:name,top_graph:{edges:[],nodes:[]},children:[]},null,"\t"),
		// 		function(err,ret){
		// 			if(!err){
		// 				dispatch.call("hieUpdate",this,null);
		// 				console.log(ret);
		// 			}
		// 			else console.error(err);
		// 		}
		// 	);
		// });

    
		dispatch.on("addGraph", hierarchy.addGraph)
		dispatch.on("configUpdate",function(type_graph){
		//	config.loadGraphConf(type_graph);
			
		});
		

       function update_graph(abs_path,noTranslate){
			dispatch.on("move",null);
            dispatch.on("loadingEnded", null);
			current_graph=abs_path;
			factory.getGraph(
				current_graph,
				function (err, ret) {
					if (!err) {
						graph_pan.update(ret, current_graph, noTranslate);
						main_svg.selectAll(".separation_line").remove();
						main_svg.select("#lhs").remove();
						main_svg.select("#rhs").remove();
						main_svg.select("#phs").remove();
						main_svg.select("#sub_svg_graph").remove();
						main_svg.selectAll(".ruleMapping").remove();
						main_svg.append(graph_pan.svg_result);
					}
				});
	   };

       function draw_mappings(pl_mapping, pr_mapping){
					   var pl = [];
					   for (var key in pl_mapping) {
						   var source_node = main_svg.selectAll("#phs .node")
							   .filter(function (d) {
								   return d.id == key
							   });
						   var target_node = main_svg.selectAll("#lhs .node")
							   .filter(function (d) {
								   return d.id == pl_mapping[key]
							   });
						   pl.push({ source: source_node.data()[0], target: target_node.data()[0] });
					   };
					   var pr = [];
					   for (var key in pr_mapping) {
						   var source_node = main_svg.selectAll("#phs .node")
							   .filter(function (d) {
								   return d.id == key
							   });
						   var target_node = main_svg.selectAll("#rhs .node")
							   .filter(function (d) {
								   return d.id == pr_mapping[key]
							   });
						   pr.push({ source: source_node.data()[0], target: target_node.data()[0] });
					   };

					   var links = main_svg.selectAll(".plMapping")
						   //.data(pl, function (d) { return d.source + "-" + d.target; });
						   .data(pl);

					   links.enter()//.insert("line","g")
						   .append("path")
						   .classed("ruleMapping", true)
						   .classed("plMapping", true)
						   .attr("marker-mid", "url(#arrow_end)");
					   links.exit().remove();

					   var links = main_svg.selectAll(".prMapping")
						   //.data(pl, function (d) { return d.source + "-" + d.target; });
						   .data(pr);

					   links.enter()//.insert("line","g")
						   .append("path")
						   .classed("ruleMapping", true)
						   .classed("prMapping", true)
						   .attr("marker-mid", "url(#arrow_end)");
					   links.exit().remove();
					   dispatch.on("move", moveMappingEdges);
				   };

       function update_rule(abs_path,noTranslate){
		   dispatch.on("move", null);
		   dispatch.on("loadingEnded", null);
		   current_graph = abs_path;
		   var callback = function (err, rep) {
			   if (!err) {
				   dispatch.on("loadingEnded", loadedEndedHandler(()=>draw_mappings(rep["PL"],rep["PR"])));
				   main_svg.selectAll("#lhs").remove();
				   main_svg.selectAll("#rhs").remove();
				   main_svg.selectAll("#phs").remove();
				   main_svg.selectAll("#sub_svg_graph").remove();
				   main_svg.selectAll(".separation_line").remove();
				   main_svg.selectAll(".ruleMapping").remove();
				   main_svg.append(lhs.svg_result);
				   main_svg.append(phs.svg_result);
				   main_svg.append(rhs.svg_result);
				   lhs.update(rep["L"], current_graph, false);
				   phs.update(rep["P"], current_graph, false);
				   rhs.update(rep["R"], current_graph, false);
				   main_svg.append("line")
					   .classed("separation_line", true)
					   .attr("x1", 0)
					   .attr("y1", size.height / 3)
					   .attr("x2", size.width)
					   .attr("y2", size.height / 3);
				   main_svg.append("line")
					   .classed("separation_line", true)
					   .attr("x1", size.width / 2)
					   .attr("y1", 0)
					   .attr("x2", size.width / 2)
					   .attr("y2", size.height / 3);
			   }
		   };
		   factory.getRule(current_graph, callback);
	   };


	   dispatch.on("loadGraph", function (abs_path) {
		   dispatch.on("graphUpdate", update_graph);
		   update_graph(abs_path, false);
	   });
	   dispatch.on("loadRule", function (abs_path) {
		   dispatch.on("graphUpdate", update_rule);
		   update_rule(abs_path, false);
	   });



	   function loadedEndedHandler(callback) {
		   var nbEnd = 0;
		   return function () {
			   if (nbEnd == 2) {
				   callback();
			   }
			   else { nbEnd++; }
		   }
	   };
	   /* On graphFileLoaded : Load a graph into the server and update Gui
		* @input : graph : graph to add (may be Hierarchy, Graph or Rule)
		* if the request succeed, the new graph is loaded on screen and the hierarchy updated
		* TODO : change server rule to to allow graph and rule adding
		*/
	   dispatch.on("graphFileLoaded", function (graph) {
		   function callback(err, ret) {
			   if (!err) {
				   dispatch.call("hieUpdate", this, null);
			   }
			   else console.error(err);
		   };
		   if (graph.hierarchy.name == "ActionGraph") //if it is a Kami old format suggest a renaming
			   graph.hierarchy.name = prompt("Give it a name !", "model_" + (Math.random()).toString());
		   if (graph.type == "Hierarchy") {
			   factory.mergeHierarchy(
				   "/",
				   JSON.stringify(graph.hierarchy, null, "\t"),
				   callback
			   );
		   } else if (graph.type == "Graph") {
			   var isSlash = current_graph == "/" ? "" : "/";
			   factory.addHierarchy(
				   current_graph + isSlash + graph.hierarchy.name,
				   JSON.stringify(graph.hierarchy, null, "\t"),
				   callback
			   );
		   } else if (graph.type == "Rule") {
			   console.log("not implemented");
		   }
	   });
	   /* On graphExprt : Export the current graph as a Json File.
		* TODO : if coordinates are set, export the config file.
		* @input : current_graph : the current graph path in the hierarchy
		* if the request succeed, the json file is opened in a new Window
		*/
	   dispatch.on("graphExprt", function (type) {
		   switch (type) {
			   case "Hierarchy":
				   factory.getHierarchyWithGraphs(
					   "/",
					   function (err, ret) {
						   converter.downloadGraph(ret);
					   }
				   );
				   break;
			   default:
				   factory.getGraph(
					   current_graph,
					   function (err, ret) {
						   converter.exportGraph({ hierarchy: ret });
					   }
				   );
		   }
	   });
	   /* On hieUpdate : Reload the hierarchy
		* if the request succeed, the hierarchy menu is reloaded so is the current graph.
		* TODO : also remove the graph
		*/
	   dispatch.on("hieUpdate", function () {
		   // hierarchy.update(root);
		   hierarchy.updateInPlace(root);
		   //current_graph="/";
	   });

	   dispatch.on("addNugetsToInput", function (nuggets) {
		   var searchString = d3.select("#nugFilter").property("value");
		   if (searchString !== "") { searchString = searchString + "|" };
		   d3.select("#nugFilter").property("value", searchString + nuggets.join("|"));
		   hierarchy.filterNuggets();

	   });

	   /* move the edges representing rule morphisms when one of the graphs moved 
	   */
	   function moveMappingEdges() {
		   rTransf = d3.zoomTransform(main_svg.select("#rhs").node());
		   pTransf = d3.zoomTransform(main_svg.select("#phs").node());
		   lTransf = d3.zoomTransform(main_svg.select("#lhs").node());
		   main_svg.selectAll(".plMapping")
			   .attr("d", function (d) {
				   return "M" + ((d.source.x * pTransf.k + pTransf.x) + size.width / 2) + "," + (d.source.y * pTransf.k + pTransf.y)
					   + " " + (d.target.x * lTransf.k + lTransf.x) + "," + (d.target.y * lTransf.k + lTransf.y);
			   });
		   main_svg.selectAll(".prMapping")
			   .attr("d", function (d) {
				   return "M" + ((d.source.x * pTransf.k + pTransf.x) + size.width / 2) + "," + (d.source.y * pTransf.k + pTransf.y)
					   + " " + (d.target.x * rTransf.k + rTransf.x) + "," + (d.target.y * rTransf.k + rTransf.y + size.height / 3);
			   });
	   };


		} ())
	});
	