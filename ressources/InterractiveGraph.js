/* This module add the graph container to the UI
 * this module trigger graphUpdate events
 * @ Author Adrien Basso blandin
 * This module is part of regraphGui project
 * this project is under AGPL Licence
*/
define([
	"ressources/d3/d3.js",
	"ressources/d3/d3-context-menu.js",
	"ressources/requestFactory.js",
	"ressources/inputMenu.js"
],function(d3,d3ContextMenu,RqFactory,inputMenu){
	/* Create a new interractive graph structure
	 * @input : container_id : the container to bind this hierarchy
	 * @input : dispatch : the dispatch event object
	 * @input : server_url : the regraph server url
	 * @return : a new InterractiveGraph object
	 */
	return function InterractiveGraph(container_id,dispatch,server_url){
	var disp = dispatch;
	var size = d3.select("#"+container_id).node().getBoundingClientRect();//the svg size
	d3.select("#"+container_id)//the main svg object
		.append("div")
		.attr("id","tab_frame")
		.append("svg:svg")
		.attr("height",size.height)
		.attr("width",size.width);
	var svg = d3.select("svg"),
		width = +svg.attr("width"),
		height = +svg.attr("height"),
		transform = d3.zoomIdentity;;
	var svg_content = svg.append("g")//the internal zoom and drag object for svg
		.classed("svg_zoom_content",true);
	var simulation;//the force simulation
	var radius = 30;
	var links_f;//the link force
	var request = new RqFactory(server_url);
	var g_id;//the graph id in the hierarchy
	var type_list;
	var locked = false;//lock event actions
	var zoom;
	/* initialize all the svg objects and forces
	 * this function is self called at instanciation
	 */
	(function init(){
		initSvg();
		initForce();
	}());
	/* init all the forces
	 * this graph has :
	 * 	-collision detection
	 * 	-link forces : force nodes linked to stay close
	 * 	-many bodies forces : repulsing force between nodes
	 * 	-center force : foce node to stay close to the center
	 */
	function initForce(){
		simulation = d3.forceSimulation()
    .force("link", d3.forceLink().id(function(d) {return d.id}))
    .force("charge", d3.forceManyBody().distanceMax(radius*10))
    .force("center", d3.forceCenter(width / 2, height / 2))
	.force("collision",d3.forceCollide(radius+radius/4));
		simulation.on("tick",move);
		simulation.stop();
	}
	/* init the svg object
	 * add arrows on edges
	 * add svg context menu
	 * add tooltip
	 * add zoom and drag behavior
	 */
	function initSvg(){
		//add drag/zoom behavior
		zoom = d3.zoom().scaleExtent([0.02, 1.1]).on("zoom", zoomed);
		svg.classed("svg-content-responsive", true);
			svg.append("svg:defs").selectAll("marker")
			.data(["arrow_end"])      // Different link/path types can be defined here
			.enter().append("svg:marker")    // This section adds the arrows
			.attr("id", function(d){return d;})
			.attr("refX", 0)
			.attr("refY", 3)
			.attr("markerWidth", 10)
			.attr("markerHeight", 10)
			.attr("orient", "auto")
			.attr("markerUnits","strokeWidth")
			//.attr("position","50%")
			.append("svg:path")
			.attr("d","M0,0 L0,6 L9,3 z");
		svg.on("contextmenu",d3ContextMenu(function(){return svgMenu();}));//add context menu
		svg.call(zoom);
		d3.select("#tab_frame").append("div")//add the description tooltip
			.attr("id","n_tooltip")
			.classed("n_tooltip",true)
			.style("visibility","hidden");
		svg_content.append("svg:image")
			.attr("width",900)
			.attr("height",400)
			.attr("x",function(){return width/2-450})
			.attr("y",function(){return height/2-200})
			.attr("xlink:href","ressources/toucan.png");
	};
	/* this fonction  is triggered by tick events
	 * move all the svg object (node and links)
	 * movement can be due to force simulation or user dragging
	 */
	function move(){
		var nodes = svg_content.selectAll("g.node");
			nodes.attr("transform", function(d) {
				return "translate(" + d.x + "," + d.y + ")"; 
				});
			svg_content.selectAll(".link")
			.attr("d", function(d) {
				var x1 = d.source.x,
					y1 = d.source.y,
					x2 = d.target.x,
					y2 = d.target.y,
					dx = x2 - x1,
					dy = y2 - y1,
					dr = Math.sqrt(dx * dx + dy * dy),
					drx = dr,
					dry = dr,
					xRotation = 0,
					largeArc = 0,
					sweep = 1;
					// Self edge.
				if ( x1 === x2 && y1 === y2 ) {
					xRotation = -45;
					largeArc = 1;
					drx = 30;
					dry = 20;
					x2 = x2 + 1;
					y2 = y2 + 1;
				} 
				return "M"+x1+","+y1+"A"+drx+","+dry+" "+xRotation+","+largeArc+","+sweep+" "+x2+","+y2;
			});	
	}
	/* this fonction  is triggered by zoom events
	 * transform the svg container according to zoom
	 */
	function zoomed() {
		if(!locked)
			svg_content.attr("transform", d3.event.transform);
	}
	/* update the current view to a new graph
	 * this function also load all nodes types
	 * @input : graph : the new graph
	 * @input : path : the graph path
	 */
	this.update = function update(graph,path){
		g_id = path;
		if(path != "/"){
			svg_content.selectAll("*").remove();
		//if(graph.nodes.length<100)
			loadType(path,graph,loadGraph);
		}
		else{
			svg_content.append("svg:image")
			.attr("width",900)
			.attr("height",400)
			.attr("x",function(){return width/2-450})
			.attr("y",function(){return height/2-200})
			.attr("xlink:href","ressources/toucan.png");
		}
	};
	/* load all type of a graph, this is needed for node coloration 
	 * @input : graph : the new graph
	 * @input : path : the graph path
	 * @input : callback : the next function to call : loadGraph
	 */
	function loadType(path,graph,callback){
		if(path != "/"){
			path=path.split("/");
			if(path.length<=2){
				type_list =[];
				return callback(graph);
			}
			path.pop();
			path=path.join("/");
			request.getGraph(path,function(e,r){
				if(e) console.error(e);
				else {
					type_list=r.nodes.map(function(e){
						return e.id;
					});
					disp.call("configUpdate",this,type_list);
					callback(graph);
				}
			});
		}else callback(graph);
	}
	/* find a specific node in a graph
	 * @input : n : the node id
	 * @input : graph : the graph object 
	 * @return : the node DOM object
	 */
	function findNode(n,graph){
		var ret=graph.filter(function(e){
			return e.id==n;		
		});
		return ret[0];
	}
	/* load a new graph in the svg
	 * nodes and edges have context menu
	 * nodes can be dragged
	 * nodes can be selected with shift + click
	 * nodes can be unlocked with ctrl+click
	 * nodes can be renamed by double clicking it
	 * @input : response : a json structure of the graph
	 */
	function loadGraph(response){
		//transform links for search optimisation
		var links = response.edges.map(function(d){
			return {source:findNode(d.from,response.nodes),target:findNode(d.to,response.nodes)}
		});
		//add all links as line in the svg
		var link = svg_content.selectAll(".link")
			.data(links, function(d) { return d.source.id + "-" + d.target.id; });
		link.enter()//.insert("line","g")
			.append("path")
			.classed("link",true)
			.attr("marker-mid", "url(#arrow_end)")
			.on("contextmenu",d3ContextMenu(edgeCtMenu));
		link.exit().remove();
		//add all node as circle in the svg
		var node = svg_content.selectAll("g.node")
			.data(response.nodes, function(d) {return d.id;});
		var node_g = node.enter().insert("g")
			.classed("node",true)
			.call(d3.drag().on("drag", dragged))
			.on("mouseover",mouseOver)
			.on("mouseout",mouseOut)
			.on("click",clickHandler)
			.on("contextmenu",d3ContextMenu(function(){return nodeCtMenu()}));
		//class all nodes with there type
		svg_content.selectAll("g.node").each(function(d){if(d.type) d3.select(this).classed(d.type,true)});
		node_g.insert("circle")
			.attr("r", radius)
			.style("fill",function(d){
				if(d.type && d.type!="") return "#"+setColor(type_list.indexOf(d.type),type_list.length);
				else return "white";
			});
		//add all node id as label
		node_g.insert("text")
			.classed("nodeLabel",true)
			.attr("x", 0)
			.attr("dy", ".35em")
			.attr("text-anchor", "middle")
			.text(function(d) {return d.id.length>7?d.id.substring(0,5).concat("..."):d.id;})
			.attr("font-size", function(){return(radius/2)+"px"})
			.style("fill",function(d){
				if(d.type  && d.type!="") return "#"+setColor(type_list.indexOf(d.type),type_list.length,true);
				else return "black";
			})
			.style("stroke",function(d){
				if(d.type && d.type!="") return "#"+setColor(type_list.indexOf(d.type),type_list.length,true);
				else return "black";
			})
			.on("dblclick",clickText);
		node.exit().remove();
		if(response.nodes.length>100)//if the graph has more than 100 nodes : rescale it at load
			zoom.scaleTo(svg_content,0.2);
		else zoom.scaleTo(svg_content,1);
		//start the simulation
		simulation.nodes([]);
		simulation.nodes(response.nodes);
		simulation.force("link").links(links);
		//links_f
		simulation.alpha(1);
		simulation.restart();
	};
	/* define a color set according to the size of an array
	 * and the element position in the array
	 * @input : nb : the element index
	 * @input : tot : the size of the array
	 * @input : neg : return the color as negative
	 * @return : a color in hex format
	 */
	function setColor(nb,tot,neg){
		if(neg){
			//calculate color luminosity
			var tmp = ((0xFFFFFF/tot)*(nb+1)).toString(16).split(".")[0];
			var ret =(parseInt(tmp[0]+tmp[1],16)*299+parseInt(tmp[2]+tmp[3],16)*587+parseInt(tmp[4]+tmp[5],16)*114)/1000;
			//if brigth : return black, else return white
			if(ret <150) return (0xFFFFFF).toString(16);
			else return (0x000000).toString(16);
		}
		return ((0xFFFFFF/tot)*(nb+1)).toString(16).split(".")[0];
	}
	/* define the svg context menu
	 * svg context menu allow to unlock all nodes,
	 * select all nodes,
	 * unselect all nodes,
	 * add a new node of a correct type,
	 * remove all selected nodes
	 * @return : the svg context menu object
	 * @call : graphUpdate
	*/
	function svgMenu(){
		var menu = [{
			title: "Unlock all",
			action: function(elm,d,i){
				svg_content.selectAll("g").each(function(d){d.fx=null;d.fy=null});
				if(simulation.nodes().length>0)
				simulation.alpha(1).restart();
			}
		},{
			title: "Lock all",
			action: function(elm,d,i){
				svg_content.selectAll("g").each(function(d){d.fx=d.x;d.fy=d.y});
			}
		},{
			title: "Select all",
			action: function(elm,d,i){
				svg_content.selectAll("g").classed("selected",true);
			}
		},{
			title: "Unselect all",
			action: function(elm,d,i){
				svg_content.selectAll("g").classed("selected",false);
			}
		},{
			title: "Add node",
			action: function(elm,d,i){
				var mousepos=d3.mouse(elm);
				locked = true;
				inputMenu("New Name",[""],type_list,null,true,true,'center',function(cb){
					locked = false;
					if(cb.line){
						request.addNode(g_id,cb.line,cb.radio,function(e,r){
							if(e) console.error(e);
							else{ 
								disp.call("graphUpdate",this,g_id);
								console.log(r);
							}
						});
					}
				},{x:mousepos[0],y:mousepos[1],r:radius/2},svg_content)
			}
		}];
		var selected = svg_content.selectAll("g.selected")
		if(selected.size()){
			menu.push({
				title: "Remove Selected nodes",
				action: function(elm,d,i){
					if(confirm("Are you sure you want to delete ALL those Nodes ?")){
						selected.each(function(el,i){
							request.rmNode(g_id,el.id,false,function(e,r){
								if(e) console.error(e);
								else console.log(r);
								if(i=selected.size()-1) disp.call("graphUpdate",this,g_id);
							})
						});
					}
				}
			});
		}
		return menu;
	};
	/* define the node context menu
	 * node context menu allow to remove it,
	 * clone it,
	 * link it to all selected nodes,
	 * merge with a selected node : TODO -> change server properties,
	 * @return : the node context menu object
	 * @call : graphUpdate
	*/
	function nodeCtMenu(){
		var menu=[{
			title: "Remove",
			action: function(elm,d,i){
				if(confirm("Are you sure you want to delete this Node ?")){
					request.rmNode(g_id,d.id,false,function(e,r){
						if(e) console.error(e);
						else{ 
							disp.call("graphUpdate",this,g_id);
							console.log(r);
						}
					});
				}
			}
		},{
			title: "Clone",
			action: function(elm,d,i){
				locked = true;
				inputMenu("New Name",[d.id+"copy"],null,null,true,true,'center',function(cb){
					if(cb.line){
						request.cloneNode(g_id,d.id,cb.line,function(e,r){
							if(e) console.error(e);
							else{ 
								disp.call("graphUpdate",this,g_id);
								console.log(r);
							}
						});
					}
					locked = false;
				},d,svg_content)
			}
		}];
		var selected = svg_content.selectAll("g.selected")
		if(selected.size()){
			menu.push({
				title: "Link to",
				action: function(elm,d,i){
					var cpt=0,err_cpt=0;
					selected.each(function(el){
						request.addEdge(g_id,d.id,el.id,function(e,r){
							if(!e){ console.log(r); cpt++;}
							else{ console.error(e); err_cpt++;}
							if(cpt == selected.size()-err_cpt) disp.call("graphUpdate",this,g_id);
						});
					});
					
				}
			});
		if(selected.size()==1){
			menu.push({
				title: "Merge with selected nodes",
				action: function(elm,d,i){
					locked=true;
					inputMenu("New Name",[d.id+selected.datum().id],null,null,true,true,'center',function(cb){
						if(cb.line){
							request.mergeNode(g_id,d.id,selected.datum().id,cb.line,false,function(e,r){
								if(!e){ console.log(r); disp.call("graphUpdate",this,g_id);}
								else console.error(e);
							});
						}locked=false;
					},d,svg_content);
				}
			})
		}

		}
		return menu;		
	};
	/* define the edge context menu
	 * edge context menu allow to remove it,
	 * select source and target node,
	 * @call : graphUpdate
	*/
	var edgeCtMenu =[{
		title: "Select Source-target",
		action: function(elm,d,i){
			svg_content.selectAll("g").filter(function(e){return e.id==d.source.id || e.id==d.target.id })
				.classed("selected",true);
		}
	},{
		title: "Remove",
		action: function(elm,d,i){
			locked=true;
			if(confirm('Are you sure you want to delete this Edge ? The linked element wont be removed')){
					request.rmEdge(g_id,d.source.id,d.target.id,false,function(e,r){
					if(e) console.error(e);
					else{ 
						disp.call("graphUpdate",this,g_id);
						console.log(r);
					}
					locked=false;
				});
			}else locked=false;
		}
	}];
	/* handling mouse over nodes
	 * show all the node information in the bottom left tooltip
	 * @input : d : the node datas
	 */
	function mouseOver(d){
		var div_ct="<p><h3><b><center>"+d.id+"</center></b>";
			div_ct+="<h5><b><center>class: "+d.type+"</center></b></h5>";
			div_ct+="</p>";
			d3.select("#n_tooltip")
				.style("visibility","visible")
				.style("background-color","#fffeec")
				.style("position","absolute")
				.style("bottom","20px")
				.style("left","10px")
				.style("border","4px solid #0f71ba")
				.style("border-radius","10px")
				.style("box-shadow"," 3px 3px 3px #888888")
				.style("z-index"," 100")
				.style("display"," block")
				.style("text-align"," left")
				.style("vertical-align"," top")
				.style("width"," 150px")
				.style("overflow "," hidden")
				.html(div_ct);
	};
	/* handling mouse out of nodes
	 * hide the bottom left tooltip
	 * @input : d : the node datas (not needed yet)
	 */
	function mouseOut(d){
		d3.select("#n_tooltip")
			.style("visibility","hidden")
			.text("");
	};
	/* handling click on a node
	 * on shift : select/uselect the node
	 * on ctrl : unlock the node and restart simulation
	 * @input : d : the node datas
	 */
	function clickHandler(d) {
		d3.event.stopPropagation();
		if(d3.event.ctrlKey){
			d.fx=null;
			d.fy=null;
			if(simulation.nodes().length>0)
			simulation.alpha(1).restart();
		}
		if(d3.event.shiftKey){
			if(d3.select(this).classed("selected"))
				d3.select(this).classed("selected",false);
			else 
				d3.select(this).classed("selected",true);
		}	
	};
	/* handling double-click on a node text
	 * open an input menu
	 * change the node id 
	 * @input : d : the node datas
	 * @call : graphUpdate
	 */
	function clickText(d){
        var el = d3.select(this);
		var lab=[d.id];
		locked =true;
		inputMenu("name",lab,null,null,true,true,'center',function(cb){
			if(cb.line && cb.line!=d.id){
				request.cloneNode(g_id,d.id,cb.line,function(err,ret){
					if(!err){
						request.rmNode(g_id,d.id,false,function(e,r){
							if(e) console.error(e);
							else{
								disp.call("graphUpdate",this,g_id);
								console.log(ret);
							}	
						})
					}
				else console.error(err);
				});
			}
			locked=false;
		},d,svg_content);
		
	};
	/* handling dragging event on nodes
	 * @input : d : the node datas
	 */
	function dragged(d) {
		if(locked)return;
		if(simulation.alpha()<0.09 && simulation.nodes().length>0)
			simulation.alpha(1).restart();
		d3.select(this).attr("cx", d.fx = d3.event.x).attr("cy", d.fy = d3.event.y);
	}

};});