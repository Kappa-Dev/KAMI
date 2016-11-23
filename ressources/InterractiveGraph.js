define([
	"ressources/d3/d3.js",
	"ressources/d3/d3-context-menu.js",
	"ressources/requestFactory.js",
	"ressources/inputMenu.js"
],function(d3,d3ContextMenu,RqFactory,inputMenu){
	return function InterractiveGraph(container_id,dispatch,server_url){
	var disp = dispatch;
	var svg = d3.select("#"+container_id).append("div").attr("id","tab_frame").append("svg:svg");
	var svg_content = svg.append("g").classed("svg_zoom_content",true);
	var size = d3.select("#tab_frame").node().getBoundingClientRect();
	var sumulation;
	var node_data;
	var radius = 30;
	var links_f;
	var transform = d3.zoomIdentity;
	var request = new RqFactory(server_url);
	var g_id;
	var type_list;
	var locked = false;
	(function init(){
		initSvg();
		initForce();
	}());
	function initForce(){
		simulation = d3.forceSimulation();
		var center_f = d3.forceCenter(svg.attr("width")/2,svg.attr("height")/2);
		simulation.force("center",center_f);
		var collid_f = d3.forceCollide(radius+radius/4).strength(0.9);
		simulation.force("collision",collid_f);
		links_f = d3.forceLink()
			.id(function(d){return d})
			.distance(function(d){return d.source.type==d.target.type?radius/2:radius*2})
			.strength(function(d){
				return 1 
			});
		simulation.force("links",links_f);
		var many_f = d3.forceManyBody()
			.strength(function(d){return d.fx?-10:-10})
			.distanceMin(radius/2)
			.distanceMax(radius*4);
		simulation.force("charge",many_f);
		simulation.on("tick",move);
		simulation.stop();
	}
	function initSvg(){
		svg.attr("preserveAspectRatio", "xMinYMin meet")
			.attr("height",size.height)
			.attr("width",size.width)
			.classed("svg-content-responsive", true);
			svg.append("svg:defs").selectAll("marker")
			.data(["arrow_end"])      // Different link/path types can be defined here
			.enter().append("svg:marker")    // This section adds in the arrows
			.attr("id", function(d){return d;})
			.attr("refX", radius)
			.attr("refY", 7)
			.attr("markerWidth", 13)
			.attr("markerHeight", 13)
			.attr("orient", "auto")
			.attr("markerUnits","strokeWidth")
			.append("svg:path")
			.attr("d", "M2,2 L2,13 L8,7 L2,2");
		svg.on("contextmenu",d3ContextMenu(function(){return svgMenu();}));
		d3.select("#tab_frame").append("div")
			.attr("id","n_tooltip")
			.classed("n_tooltip",true)
			.style("visibility","hidden");
		svg.call(d3.zoom().scaleExtent([0.02, 1.1]).on("zoom", zoomed));
	};
	function move(){
		var nodes = svg_content.selectAll("g.node");
			nodes.attr("transform", function(d) {
				d.x=Math.max(20, Math.min(svg.attr("width") - 20, d.x));
				d.y=Math.max(20, Math.min(svg.attr("height") - 20, d.y));
				return "translate(" + d.x + "," + d.y + ")"; 
				});
			svg_content.selectAll(".link")
				.attr("x1", function(d){ return d.source.x;})
				.attr("y1", function(d){ return d.source.y;})
				.attr("x2", function(d){ return d.target.x;})
				.attr("y2", function(d){ if (d.source.id == d.target.id) return d.target.y-60;return d.target.y;});
	}
	function zoomed() {
		if(!locked)
			svg_content.attr("transform", d3.event.transform);
	}
	this.update = function update(graph,path){
		g_id = path;
		svg_content.selectAll("*").remove();
		loadType(path,graph,loadGraph);
	};
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
					callback(graph);
				}
			});
		}else callback(graph);
	}
	function findNode(n,graph){
		var ret=graph.filter(function(e){
			return e.id==n;		
		});
		return ret[0];
	}
	function loadGraph(response){
		var links = response.edges.map(function(d){
			return {source:findNode(d.from,response.nodes),target:findNode(d.to,response.nodes)}
		});
		var link = svg_content.selectAll(".link")
			.data(links, function(d) { return d.source.id + "-" + d.target.id; });
		link.enter().insert("line","g")
			.classed("link",true)
			.attr("marker-end", "url(#arrow_end)")
			.on("contextmenu",d3ContextMenu(edgeCtMenu));
		link.exit().remove();
		var node = svg_content.selectAll("g.node")
			.data(response.nodes, function(d) {return d.id;});
		var node_g = node.enter().insert("g")
			.classed("node",true)
			.call(d3.drag().on("drag", dragged))
			.on("mouseover",mouseOver)
			.on("mouseout",mouseOut)
			.on("click",clickHandler)
			.on("contextmenu",d3ContextMenu(function(){return nodeCtMenu()}));
		svg_content.selectAll("g.node").each(function(d){if(d.type) d3.select(this).classed(d.type,true)});
		node_g.insert("circle")
			.attr("r", radius)
			.style("fill",function(d){
				if(d.type) return "#"+setColor(type_list.indexOf(d.type),type_list.length);
				else return "white";
			});
		node_g.insert("text")
			.classed("nodeLabel",true)
			.attr("x", 0)
			.attr("dy", ".35em")
			.attr("text-anchor", "middle")
			.text(function(d) {return d.id.length>7?d.id.substring(0,5).concat("..."):d.id;})
			.attr("font-size", function(){return(radius/2)+"px"})
			.style("fill",function(d){
				if(d.type) return "#"+setColor(type_list.indexOf(d.type),type_list.length,true);
				else return "black";
			})
			.style("stroke",function(d){
				if(d.type) return "#"+setColor(type_list.indexOf(d.type),type_list.length,true);
				else return "black";
			})
			.on("dblclick",clickText);
		node.exit().remove();
		simulation.nodes(response.nodes);
		links_f.links(links);
		simulation.alpha(1);
		simulation.restart();
	};
	function setColor(nb,tot,neg){
		if(nb+1==tot/2)tot++;
		if(neg) return ((0xFFFFFF-((0xFFFFFF/tot)*(nb+1)))).toString(16);
		return ((0xFFFFFF/tot)*(nb+1)).toString(16);
	}
	function svgMenu(){
		var menu = [{
			title: "Unlock all",
			action: function(elm,d,i){
				svg_content.selectAll("g").each(function(d){d.fx=null;d.fy=null});
				simulation.alpha(1).restart();
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
			/*menu.push({
				title: "Merge with selected nodes",
				action: function(elm,d,i){
					var cpt=0,err_cpt=0;
					selected.each(function(el){
						if(cpt+err_cpt==selected.size()-1){
							inputMenu("New Name",[d.id+el.id],null,null,true,true,'center',function(cb){
								if(cb.line){
									request.mergeNode(g_id,d.id,el.id,cb.line,false,function(e,r){
										if(!e){ console.log(r); cpt++;}
										else{ console.error(e); err_cpt++;}
										if(cpt == selected.size()-err_cpt) disp.call("graphUpdate",this,g_id);
									});
								}
							},d,svg_content);
						}else{
							request.mergeNode(g_id,d.id,el.id,d.id,false,function(e,r){
								if(!e){ console.log(r); cpt++;}
								else{ console.error(e); err_cpt++;}
								if(cpt == selected.size()-err_cpt) disp.call("graphUpdate",this,g_id);
							});
						}
					});
				}
			});*/
		}
		return menu;		
	};
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
	function mouseOver(d){//handling mouse over nodes/actions
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
	function mouseOut(d){//handling mouse out of nodes/actions
		d3.select("#n_tooltip")
			.style("visibility","hidden")
			.text("");
	};
	function clickHandler(d) {//handling click on a node or an action 
		d3.event.stopPropagation();
		if(d3.event.ctrlKey){
			d.fx=null;
			d.fy=null;
			simulation.alpha(1).restart();
		}
		if(d3.event.shiftKey){
			if(d3.select(this).classed("selected"))
				d3.select(this).classed("selected",false);
			else 
				d3.select(this).classed("selected",true);
		}	
	};
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
	function dragged(d) {
		if(locked)return;
		if(simulation.alpha()<0.09)
			simulation.alpha(1).restart();
		d3.select(this).attr("cx", d.fx = d3.event.x).attr("cy", d.fy = d3.event.y);
	}

};});