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
	"ressources/ruleViewer.js"
],
	function (d3, Tree, Hierarchy, converter, InputFileReader, RFactory, InterractiveGraph, SideMenu, RuleViewer) {
		//Regraph Gui Core
		(function pageLoad() {
			//this section must be changed to feet the server/user requirement.
			//var server_url = "http://0.0.0.0:5000";
			var server_url = "{{server_url}}";
			var main_ct_id = "main_container";
			var root = "/";
			var current_graph = "/";
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
				"loadPreview",//triggered by hovering on a name
				"closePreview"//triggered by hovering on a name
			);

			d3.select("body").append("div").attr("id", main_ct_id);

			var main_container = d3.select("#" + main_ct_id);//Main div
			//main_container.append("div")//separator between menu and page core
			//	.attr("id","bottom_top_chart");
			var container = main_container.append("div")//page core
				.attr("id", "container");
			main_container.append("div")//top menu
				.attr("id", "top_chart");
			// var side = container.append("div")//main div of side menu
			// 	.attr("id","side_menu");
			var graph_frame = container.append("div")//main div of graph
				.attr("id", "graph_frame");

			var tab_frame = graph_frame.append("div")
				.attr("id", "tab_frame");

			// var side_ct=graph_frame.append("div")//add the vertical separator container
			// 	.attr("id","drag_bar_cont");
			// side_ct.append("div")//add a drag bar for the menu
			// 	.attr("id","drag_bar")
			// 	.on("click",function(){return dispatch.call("tabMenu",this)});


			//request factory for the given regraph server
			var factory = new RFactory(server_url);
			//regraph hierarchy
			var hierarchy = new Hierarchy("top_chart", dispatch, server_url);
			hierarchy.update(root);
			//modification menu : add, export and new graph + file input + type selector
			var input_hie = new InputFileReader("top_chart", dispatch, server_url);

			//configuration menu : change serveur url, node color, size and shape.
			// var config = new ConfigTab("top_chart",dispatch,server_url);
			// config.init();

			//the graph showed : TODO -> maybe a graph list to avoid reloading each graph.

			var size = d3.select("#graph_frame").node().getBoundingClientRect();
			var rule_pan = new RuleViewer("svg_rule", tab_frame, dispatch, server_url);
			var graph_pan = new InterractiveGraph("tab_frame", "sub_svg_graph", size.width, size.height, dispatch, factory);
			var preview_pan = new InterractiveGraph("tab_frame", "preview_graph", size.width*0.9, size.height/2, dispatch, factory, true);
            tab_frame.selectAll("#svg_rule").remove();
			tab_frame.append(graph_pan.svg_result);


			//the side menu
			//var side_menu = new SideMenu("side_menu",dispatch,server_url);
			/* dispatch section
			 * here each dispatch event is handled
			 */
			/* On tabMenu : open or close the tab menu
			 */
			dispatch.on("tabMenu", function () {
				d3.event.stopPropagation();
				var size = side.style("width") != "0px" ? "0px" : "15.6%";
				side.style("min-width", size);
				graph_frame.style("margin-left", size);
				side.style("width", size);
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

			dispatch.on("addGraph", hierarchy.addGraph);
			// dispatch.on("configUpdate",function(type_graph){
			// //	config.loadGraphConf(type_graph);

			// });

			function sameSubgraph(hie) {
				var sameSubgraphAux = function (hie, n_id) {
					var f = function (acc, subG) {
						return acc.concat(subG["top_graph"]["nodes"].map((d) => d["type"]))
					};
					var images = hie["children"]
						.filter((graph) =>
							graph["top_graph"]["nodes"].some((d) => d["type"] == n_id))
						.reduce(f, []);
					return (n2_id) => images.indexOf(n2_id) > -1;
				};
				return (n_id) => sameSubgraphAux(hie, n_id);
			};

			function update_graph(abs_path, noTranslate) {
				current_graph = abs_path;
				factory.getGraphAndDirectChildren(
					current_graph,
					function (err, ret) {
						if (!err) {
							graph_pan.update(ret["top_graph"], current_graph,
								{ noTranslate: noTranslate, highlightRel: sameSubgraph(ret) });
							tab_frame.append(graph_pan.svg_result)
								.attr("x", 0)
								.attr("y", 0);
						}
					});
			};

			function update_preview(abs_path, noTranslate) {
				console.log("updatePreview");
				factory.getGraph(
					abs_path,
					function (err, ret) {
						if (!err) {
							preview_pan.update(ret, abs_path,
								{ noTranslate: noTranslate, highlightRel: null });
							tab_frame.append(preview_pan.svg_result);
						}
					});
			};

			function update_rule(abs_path, noTranslate) {
				current_graph = abs_path;
				factory.getRule(
					current_graph,
					function (err, ret) {
						if (!err) {
							rule_pan.update(ret, current_graph, { noTranslate: noTranslate });
							tab_frame.append(rule_pan.svg_result)
								.attr("x", 0)
								.attr("y", 0);
						}
					});
			};

			dispatch.on("loadGraph", function (abs_path) {
				tab_frame.selectAll("svg")
					.remove();
				rule_pan.stop();
				dispatch.on("graphUpdate", update_graph);
				update_graph(abs_path, false);
			});

			dispatch.on("loadPreview", function (abs_path) {
				rule_pan.stop();
				update_preview(abs_path, false);
			});

			dispatch.on("closePreview", function (abs_path) {
				tab_frame.selectAll("#preview_graph")
					.remove();
			});

			dispatch.on("loadRule", function (abs_path) {
				tab_frame.selectAll("svg")
					.remove();
				rule_pan.stop();
				dispatch.on("graphUpdate", update_rule);
				update_rule(abs_path, false);
			});

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

			dispatch.on("addNugetsToInput", function (nuggets, name, keepOldConds) {
				// var searchString = d3.select("#nugFilter").property("value");
				// if (searchString !== "") { searchString = searchString + "|" };
				// d3.select("#nugFilter").property("value", searchString + nuggets.join("|"));
                if (!keepOldConds){hierarchy.clearCondData()};
				hierarchy.addToCondData({name:name,cond:(nug)=>nuggets.indexOf(nug)>-1});

			});

		} ())
	});
	