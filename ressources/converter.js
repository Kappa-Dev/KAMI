define(["ressources/d3/d3.js"],function(d3){ return {

/* convert the old Kami 2.0 graph format to the new Regraph Format
 * Convert a nugget list into a graph tree with the action graph as root and each action as nugget leafs
 * @input json_file : a Kami 2.0 Json File
 * @output : a Regraph Json File
*/ 
kamiToRegraph:function(json_file,dispatch){
	d3.json(json_file,function(response){
		if(!response.version) dispatch.call("graphFileLoaded",this,{"hierarchy":response,"coord":null});
		//rename graph objects in the new format
		cvt_dico ={"agent":"agent","region":"region","key_res":"residue","attribute":"values","flag":"values","mod":"mod","bnd":"bind","brk":"unbind"};
		cls_to_js_id = {"agent":"agents","region":"regions","flag":"flags","attribute":"attributes","key_res":"key_rs","action":"actions"}
		//OutPut object
		var ret={
			"name":"ActionGraph",
			"top_graph":{"edges":[],"nodes":[]},
			"children":[]
		};
		var coord={"ActionGraph":{}};
		/* convert @input kami node type into a regraph node list and add it to the output graph */
		["agents","regions","key_rs","attributes","flags"].forEach(function(node_type){
			response[node_type].forEach(function(e,i){
				ret.top_graph.nodes.push({
					"id":e.labels.join("_")+"_"+i,
					"type":cvt_dico[e.classes[0]]
				});
				e.values.forEach(function(ee,ii){
					ret.top_graph.nodes.push({
						"id":e.labels.join("_")+"_"+i+"_"+ee,
						"type":"value"
					});
					ret.top_graph.edges.push({
						"from":e.labels.join("_")+"_"+i+"_"+ee,
						"to":e.labels.join("_")+"_"+i
					});
				});
				coord.ActionGraph[e.labels.join("_")+"_"+i]=[e.x,e.y];
			});
		});
		//add edges corresponding to path
		["regions","key_rs","attributes","flags"].forEach(function(node_type){
			response[node_type].forEach(function(e,i){
				ret.top_graph.edges.push({
					"from":e.labels.join("_")+"_"+i,
					"to":getFthId(e)
				});
			});
		});
		function getFthId(e){
			if(e.path.length == 0) throw new Error ("This node has no father");
			var ret;
			response[cls_to_js_id[e.father_classes[0]]].some(function(ee,i){
				if(
					ee.labels.indexOf(e.path[e.path.length-1])!=-1 
					&& (
						(
							(e.father_classes[0] == "action" || e.father_classes[0] == "agent")
							&&
							e.father_classes.join()==ee.classes.join()
						)||
						e.path.slice(0,e.path.length-1).join("_")==ee.path.join("_")
					)
				){
					ret=ee.labels.join("_")+"_"+i;
					return true;
				} return false;
			});
			if(!ret) throw new Error ("This node' father doesn't exist"+e.labels.join("_"));
			return ret;
		};
		// for each action, create a new graph corresponding to its nugget and add it to the action graph
		response.actions.forEach(function(e,i){
			addToACT(e,i);
			addToNug(e,i);
		});
		
		function getCVal(e,ee){
			let tmp_ref = response[ee.ref[0]][ee.ref[1]];
			return tmp_ref.values[tmp_ref.values.indexOf(ee.values[0])+(e.classes[2]=="pos"?1:-1)];
		};
		function addToACT(e,i){
			//the action node
			ret.top_graph.nodes.push({
				"id":e.labels.join("_")+"_"+i,
				"type":cvt_dico[e.classes[1]]
			});
			ret.top_graph.nodes.push({
				"id":e.labels.join("_")+"_"+i+"_left",
				"type":(e.classes[1]=="brk"?"output":"input")
			});
			ret.top_graph.nodes.push({
				"id":e.labels.join("_")+"_"+i+"_right",
				"type":(e.classes[1]=="bnd"?"input":"output")
			});
			coord.ActionGraph[e.labels.join("_")+"_"+i]=[e.x,e.y];
			if (e.classes[1]=="brk"){
				["left","right"].forEach(function(obj){
					e[obj].forEach(function(ee,ii){
						ret.top_graph.edges.push({
							"from":e.labels.join("_")+"_"+i+"_"+obj,
							"to":response[ee.ref[0]][ee.ref[1]].labels.join("_")+"_"+ee.ref[1]
						})
					});
				});
			} else if(e.classes[1]=="mod"){
				e.right.forEach(function(ee,ii){
					ret.top_graph.edges.push({
						"from":e.labels.join("_")+"_"+i+"_right",
						"to":response[ee.ref[0]][ee.ref[1]].labels.join("_")+"_"+ee.ref[1]
					});
					ret.top_graph.nodes.push({
						"id":e.labels.join("_")+"_"+i+"_"+ee.values[0],
						"type":"Lvalue"
					});
					ret.top_graph.nodes.push({
						"id":e.labels.join("_")+"_"+i+"_"+getCVal(e,ee),
						"type":"Rvalue"
					});
					ret.top_graph.edges.push({
						"from":e.labels.join("_")+"_"+i+"_"+ee.values[0],
						"to":e.labels.join("_")+"_"+i
					});
					ret.top_graph.edges.push({
						"from":e.labels.join("_")+"_"+i+"_"+getCVal(e,ee),
						"to":e.labels.join("_")+"_"+i
					});
				});
			}else if(e.classes[1]=="bnd"){
				ret.top_graph.nodes.push({
					"id":e.labels.join("_")+"_"+i+"_btst",
					"type":"binded"
				});
				ret.top_graph.nodes.push({
					"id":e.labels.join("_")+"_"+i+"_btst_left",
					"type":(e.classes[1]=="brk"?"output":"input")
				});
				ret.top_graph.nodes.push({
					"id":e.labels.join("_")+"_"+i+"_btst_right",
					"type":(e.classes[1]=="bnd"?"input":"output")
				});
				["left","right"].forEach(function(obj){
					e[obj].forEach(function(ee,ii){
						ret.top_graph.edges.push({
							"from":response[ee.ref[0]][ee.ref[1]].labels.join("_")+"_"+ee.ref[1],
							"to":e.labels.join("_")+"_"+i+"_"+obj
						});
						ret.top_graph.edges.push({
							"from":response[ee.ref[0]][ee.ref[1]].labels.join("_")+"_"+ee.ref[1],
							"to":e.labels.join("_")+"_"+i+"_btst_"+obj
						});
					});
				});				
			}	
		};
		//the nugget graph
		function addToNug(act,i){
			var inst_cpt = 0;
			var n_child={
				"name":act.labels.join()+"_"+i,
				"top_graph":{"edges":[],"nodes":[]},
				"children":[]
			};
			n_child.top_graph.nodes.push({
				"id":act.labels.join("_")+"_"+i,
				"type":act.labels.join("_")+"_"+i
			});	
			n_child.top_graph.nodes.push({
				"id":act.labels.join("_")+"_"+i+"_left",
				"type":act.labels.join("_")+"_"+i+"_left"
			});
			n_child.top_graph.nodes.push({
				"id":act.labels.join("_")+"_"+i+"_right",
				"type":act.labels.join("_")+"_"+i+"_left"
			});
			["left","right","context"].forEach(function(ctx){
				act[ctx].forEach(function(e){
					var tmp_node = response[e.ref[0]][e.ref[1]];
					if(tmp_node.classes[0]=="action" && tmp_node.classes[1] == "bnd"){
						n_child.top_graph.nodes.push({
							"id":tmp_node.labels.join("_")+"_"+e.ref[1]+"_"+inst_cpt,
							"type":tmp_node.labels.join("_")+"_"+e.ref[1]+"_btst"
						});
					}else{
						n_child.top_graph.nodes.push({
							"id":tmp_node.labels.join("_")+"_"+e.ref[1]+"_"+inst_cpt,
							"type":tmp_node.labels.join("_")+"_"+e.ref[1]
						});
						if(e.values) e.values.forEach(function(v,vi){
							n_child.top_graph.nodes.push({
								"id":tmp_node.labels.join("_")+"_"+e.ref[1]+"_"+inst_cpt+"_"+v,
								"type":tmp_node.labels.join("_")+"_"+e.ref[1]+"_"+v
							});
							n_child.top_graph.edges.push({
								"from":tmp_node.labels.join("_")+"_"+e.ref[1]+"_"+inst_cpt+"_"+v,
								"to":tmp_node.labels.join("_")+"_"+e.ref[1]+"_"+inst_cpt
							});
						});
					}
					if(ctx != "context"){
						if (act.classes[1]=="brk"){
							n_child.top_graph.edges.push({
								"from":act.labels.join("_")+"_"+i+"_"+ctx,
								"to":tmp_node.labels.join("_")+"_"+e.ref[1]+"_"+inst_cpt
							});
						}else if(act.classes[1]=="mod" || act.classes[1]=="bnd"){
							n_child.top_graph.edges.push({
								"from":tmp_node.labels.join("_")+"_"+e.ref[1]+"_"+inst_cpt,
								"to":act.labels.join("_")+"_"+i+"_"+ctx
							});
							if(ctx == "right" && act.classes[1]=="mod"){
								n_child.top_graph.nodes.push({
									"id":act.labels.join("_")+"_"+i+"_"+e.values[0],
									"type":act.labels.join("_")+"_"+i+"_"+e.values[0]
								});
								n_child.top_graph.nodes.push({
									"id":act.labels.join("_")+"_"+i+"_"+getCVal(act,e),
									"type":act.labels.join("_")+"_"+i+"_"+getCVal(act,e)
								});
								n_child.top_graph.edges.push({
									"from":act.labels.join("_")+"_"+i+"_"+e.values[0],
									"to":act.labels.join("_")+"_"+i
								});
								n_child.top_graph.edges.push({
									"from":act.labels.join("_")+"_"+i+"_"+getCVal(act,e),
									"to":act.labels.join("_")+"_"+i
								});
							}
						}
					}
					inst_cpt++;
				});
			});
			ret.children.push(n_child);
			
		};
		dispatch.call("graphFileLoaded",this,{"hierarchy":ret,"coord":coord});
	});
},
exportGraph:function(ret){
	var url = 'data:text/json;charset=utf8,' + encodeURIComponent(JSON.stringify(ret.hierarchy,null,"\t"));
		window.open(url, '_blank');
	var url2 = 'data:text/json;charset=utf8,' + encodeURIComponent(JSON.stringify(ret.coord,null,"\t"));
		window.open(url2, '_blank');
		window.focus();
},
loadCoord:function(coord,graphic_g){
	graphic_g.stopMotion();
	for(node in coord[graphic_g.getName()]){
		graphic_g.setCoord(node,coord[graphic_g.getName()][node]);
	}graphic_g.startMotion();
	
}


}});