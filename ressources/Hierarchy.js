/* This module add the "hierarchy" menu to the UI
 * This module add a div containing a selector and a scrolling tab menu
 * this module trigger graphUpdate events
 * @ Author Adrien Basso blandin
 * This module is part of regraphGui project
 * this project is under AGPL Licence
*/
define([
	"ressources/d3/d3.js",
	"ressources/simpleTree.js",
	"ressources/requestFactory.js",
	"ressources/d3/d3-context-menu.js"
	],
	function(d3,Tree,RFactory,d3ContextMenu){
	/* Create a new hierarchy module
	 * @input : container_id : the container to bind this hierarchy
	 * @input : dispatch : the dispatch event object
	 * @input : server_url : the regraph server url
	 * @return : a new Hierarchy object
	 */
	return function Hierarchy(container_id,dispatch,server_url){
		if(!server_url) throw new Error("server url undefined");
		var srv_url = server_url;//the current url of the server
		var disp = dispatch;//global dispatcher for events
		var container = d3.select("#"+container_id).append("div").attr("id","tab_menu").classed("top_menu",true);//add all tabl to menu
		var hierarchy = new Tree();//a tree containing the whole hierarchy
		var top_h_select = container.append("div").attr("id","top_h_select");
		var h_select = top_h_select.append("select").attr("id","h_select").classed("mod_el",true);//the hierarchy selector
		top_h_select.append("i").attr("id","gotoParent").classed("icon",true);//the hierarchy selector
		var h_list = container.append("div").attr("id","scrolling_list");//the list of son of the specified node
		var textBox = container.append("input")
		                       .attr("type","text")
		                       .attr("id","nugFilter")
							   .on("input",filterNuggets);
        var condData = [];
		var condList = container.append("div")
		         .attr("id","conditionsList");

		var current_node = null;//the current node
		var selected_node = null;//the current selected son
		var selected_graphs = {};//the currently selected graphs
		var factory = new RFactory(srv_url);

		var selfHierarchy = this;
        var right_click_menu = [
              {title : "delete",
			   action : function(elm, d, i) {
                             current_obj = hierarchy.getAbsPath(d)
			                 if (confirm("Confirmation : remove "+current_obj+" and all its children ?"))
							 	factory.delHierarchy(current_obj,function(e,r){
							 		if(e) return console.error(e);
							 		console.log(r);
							 		dispatch.call("hieUpdate",this);
							 	});
			            }

			  },
              {title : "get kappa",
			   action : toKappa
			  },

              {title : "set rate",
			   action : setRate
			  }
		];
        var only_graph_menu = [
			{title : "create rule",
		     action: createRule
			}
		];
		/* load a new hierarchy from the server
		 * @input : root_path : the hierarchy root pathname
		 */
		this.update = function update(root_path){
			factory.getHierarchy(root_path,function(err,req){
				hierarchy.load(req);
				current_node = hierarchy.getRoot();
				initHlist(hierarchy.getSons(current_node),hierarchy.getRules(current_node));
				initHselect(hierarchy.getTreePath(current_node));
			});
		};

		/* load a new hierarchy and go to a node
		 * @input : root_path : the hierarchy root pathname
		 * @input : node : the node to go to
		 */
		this.updateAndMove = function (root_path, node_id){
			factory.getHierarchy(root_path,function(err,req){
				hierarchy.load(req);
				current_node = node_id;
				initHlist(hierarchy.getSons(current_node),hierarchy.getRules(current_node));
				initHselect(hierarchy.getTreePath(current_node));
			});
		};

		this.updateInPlace = function (root_path){
			factory.getHierarchy(root_path,function(err,req){
				hierarchy.load(req);
				initHlist(hierarchy.getSons(current_node),hierarchy.getRules(current_node));
				initHselect(hierarchy.getTreePath(current_node));
			});
		};
		/* update the scrolling tab menu with the current node sons
		 * @input : data : the list of sons of the current node
		 */
		function initHlist(data,rules){
			clearCondData();
			h_list.selectAll("*").remove();
			var slc =h_list.selectAll(".tab_menu_el")
				.data(data);
			slc.exit().remove();
			slc.enter().append("div")
				.classed("tab_menu_el",true)
				.classed("unselectable",true)
				.classed("selected",false)
				.attr("id",function(d){return d})
				.on("click",function(d,i){return dispach_click(d,i,this)})
				.on("contextmenu",d3ContextMenu(right_click_menu.concat(only_graph_menu)))
				.on("dblclick",function(d){return lvlChange(d)});

			var slc=h_list.selectAll(".tab_menu_el");
            slc.append("i")
			   .classed("icon",true);
			slc.append("div")
				.classed("tab_menu_el_name",true)
				.text(function(d){
					// let nm = hierarchy.getName(d);
					// return nm.length>14?nm.substring(0,12).concat("..."):nm;
					return hierarchy.getName(d);
				});

			slc = slc.data(data.concat(rules));
            ruleSelection = slc.enter().append("div")
				.classed("tab_menu_el",true)
				.classed("unselectable",true)
				.classed("selected",false)
				.attr("id",function(d){return d})
				.on("click",function(d){return display_rule(d,this)})
				.on("contextmenu",d3ContextMenu(right_click_menu));
            ruleSelection.append("i")
			   .classed("icon_rule",true);
			ruleSelection.append("div")
				.classed("tab_menu_el_name",true)
				.text(function(d){return d.id});
			    

            try {
			if (hierarchy.getName(hierarchy.getFather(hierarchy.getFather(data[0])))==="kami"){
                 d3.selectAll(".tab_menu_el")
				   .each(function(id){
						var elem = d3.select(this)
                        factory.getGraph(hierarchy.getAbsPath(id),
						                 function(err,resp){
							 if(err){return 0}
							 rate = resp.attributes["rate"];
							 rate = rate?rate:"und";
						     elem.append("div")
							     .style("width","1vw");
							 elem.append("div")
							     .classed("tab_menu_el_rate",true)                                               
								 .text(rate);

						}


						)

				   })
			}}
			catch(err){}

		};
		/* update the selector with the current node parents
		 * @input : data : the absolute path of the current node
		 */
		function initHselect(data){
			h_select.selectAll("*").remove();
			h_select.selectAll("option")
				.data(data)
				.enter().append("option")
					.text(function(d){return hierarchy.getName(d)})
					.attr("selected",function(d){return d==current_node});
			h_select.on("change",lvlChange);
			top_h_select.select("i").on("click", function () {
			disp.call("loadGraph", this, hierarchy.getAbsPath(data[data.length - 1]))});
		};

        function display_rule(d,elem){
			h_list.selectAll(".tab_menu_el")
			      .classed("current",false)
			d3.select(elem)
			      .classed("current",true)	  
			var absPath = (d.path=="/"?"":d.path)+"/"+d.id;
			disp.call("loadRule",this,absPath);
		};

		function dispach_click(d,i,elem){
		    d3.event.stopPropagation();
			if(d3.event.ctrlKey){
				if(d3.select(elem).classed("selected"))
					d3.select(elem).classed("selected",false);
				else 
					d3.select(elem).classed("selected",true);
			}
			else{
				tabChange(d,elem);
			}
			
		};
		/* color in blue the currently selected node of the scrolling tab menu
		 * @input : id : the new selected node
		 * @call : graphUpdate event
		 */
		function tabChange(id,elem){
			// if(selected_node==id)return;
			selected_node = id;
			// h_list.selectAll(".tab_menu_el")
			// 	.style("color","rgb(251, 249, 200)")//show the correct menu element
			// 	.style("background",function(d){
			// 		return d==id?"linear-gradient(to bottom, #3fa4f0 0%, #0f71ba 100%)":"none";
			// 	});

			h_list.selectAll(".tab_menu_el")
			      .classed("current",false)
			d3.select(elem)
			      .classed("current",true)	 
			disp.call("loadGraph",this,hierarchy.getAbsPath(id));
			disp.call(
				"tabUpdate",
				this,
				hierarchy.getAbsPath(id),
				hierarchy.getSons(current_node).map(function(d){
					return hierarchy.getName(d);
				}),
				hierarchy.getAbsPath(current_node),
				"hierarchy"
			);
		};
		/* change the current node in the hierarchy
		 * this function update the selector and the tab menu
		 * @input : id : the new current node
		 */
		function lvlChange(id){
			d3.event.stopPropagation();
			var data = id;
			if(!id){
				var si   = h_select.property('selectedIndex'),
				s    = h_select.selectAll("option").filter(function (d, i) { return i === si });
				data = s.datum();
			}
			// if(hierarchy.getSons(data).length==0)return;
			current_node = data;
			initHlist(hierarchy.getSons(data),hierarchy.getRules(data));
			initHselect(hierarchy.getTreePath(data));
			disp.call("loadGraph",this,hierarchy.getAbsPath(data));

		};

		/* Convert the current graph into kappa : TODO
		 * Open a new page with the Kappa code 
		 */
		function toKappa(){
            var callback = function(error, response){
				d3.select("body")
				.style("cursor","default");
				if(error) {
					alert(error.currentTarget.response);
				    return false;
				}
                d3.select("#json_link")
                  .attr("href",
                             'data:text/json;charset=utf-8,'
							  + encodeURIComponent(JSON.parse(response.response)["kappa_code"]));
                document.getElementById('json_link').click();
                       };
			nugget_list = []		   
			d3.selectAll(".tab_menu_el.selected")
			                .each(function(){
								nugget_list.push(hierarchy.getName(this.id))
							})
			var path = hierarchy.getAbsPath(current_node)+"/"
			path = (path == "//")?"/":path
			d3.select("body")
			  .style("cursor","progress");
            factory.getKappa(path, JSON.stringify({"names": nugget_list}), callback)
            return false;
		};

		function setRate(elm, d, i){
            var path = hierarchy.getAbsPath(d)+"/";
            var rate = prompt("Enter the rate", "");
			if (!rate){return 0};
			var callback = function(err, resp){
				if(err){
					alert(err.currentTarget.response);
				    return false;
				}
				console.log(self);
				selfHierarchy.updateAndMove("/",hierarchy.getFather(d));
			}
			factory.addAttr(path, JSON.stringify({"rate":rate}), callback);

		};

		this.addGraph = function(){
			//var name=prompt("Give it a name !", "model_"+(Math.random()).toString());
			var name = prompt("Name of the new graph?", "");
			if (!name) {return 0}
			var current_path = hierarchy.getAbsPath(current_node)+"/";
			if (current_path == "//"){current_path="/"}

			factory.addHierarchy(current_path+name+"/",
				JSON.stringify({name:name,top_graph:{edges:[],nodes:[]},children:[]},null,"\t"),
				function(err,ret){
					if(!err){
						dispatch.call("hieUpdate",this,null);
						console.log(ret);
					}
					else console.error(err);
				}
			);
		};

	    function filterNuggets(){
			var searchString = d3.select("#nugFilter").property("value");
			var searchStrings = searchString.split("|");
            var testTextBox = function(nugName){
				return searchStrings.some(function (s){
					return (-1) !== nugName.search(s) })};

			var testCondList = function(nugName){
				return condData.map(d => d.cond)
						.reduce((acc,f)=>acc && f(nugName), true);
			};
			var test = function (nugName){
				return testCondList(nugName) && testTextBox(nugName);
			};
			    		
            var notTest = function(nugName){
				return !test(nugName)
			};
			d3.selectAll(".tab_menu_el:not(.selected)")
			  .filter(function(){
				  var nugName = d3.select(this).selectAll(".tab_menu_el_name").text();
				  return notTest(nugName);
			  })
			  .style("display","none");
			d3.selectAll(".tab_menu_el:not(.selected)")
				.filter(function () {
					var nugName = d3.select(this).selectAll(".tab_menu_el_name").text();
					return test(nugName);
				})
				.style("display", "flex");
	    };

        this.filterNuggets = filterNuggets; 

		function createRule(elm,d,i){
			var name = prompt("Name of the new rule?", "");
			var path = hierarchy.getAbsPath(current_node)+"/";
			if (path=="//"){path = "/"};
            var patternName = hierarchy.getName(d);
		    var callback = function(err,ret){
					if(!err){
						dispatch.call("hieUpdate",this,null);
						console.log(ret);
					}
					else console.error(err);
				};
			factory.addRule(path+name+"/",patternName,callback);
		};

		function updateCondList(){
			var s = condList.selectAll("div")
				.data(condData);
			s.exit().remove();
			s.enter().append("div")
			         .classed("cond",true)
			         .classed("unselectable",true)
					 .on("click",removeFromCondList)
					 .text(function(d){return d.name+"_filter"});
			filterNuggets();
		};

		function removeFromCondList(d) {
			var index = condData.indexOf(d);
			if (index > -1) {
				condData.splice(index, 1);
			}
			updateCondList();
		};
        var clearCondData = function(){
			condData = [];
			updateCondList();
		};
		this.clearCondData = clearCondData;
		this.addToCondData = function (d){
			condData.push(d);
			updateCondList();
		};

	};

});
