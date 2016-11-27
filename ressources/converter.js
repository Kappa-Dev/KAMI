/* This module contain convertion functions for graph structures
 * this module trigger graphFileLoaded events
 * @ Author Adrien Basso blandin
 * This module is part of regraphGui project
 * this project is under AGPL Licence
*/
define(["ressources/d3/d3.js"],function(d3){ return {
/* converte a snip file into a regraph file
 * @input : json_file : a snip Json File
 * @input : dispatch : the dispatch event object
 * @input : type : the graph type
 * @output : a Regraph Json File
*/ 
snipToRegraph:function(json_file,dispatch,type){
	d3.json(json_file,function(response){
		var ret={
			"name":"ThreadGraph",
			"top_graph":{"edges":[],"nodes":[]},
			"children":[]
		};
		ret.top_graph.nodes.push({id:"Concat",type:""});
		ret.top_graph.nodes.push({id:"Contact",type:""});
		ret.top_graph.nodes.push({id:"LastName",type:""});
		ret.top_graph.nodes.push({id:"FirstName",type:""});
		ret.top_graph.edges.push({from:"LastName",to:"Contact"});
		ret.top_graph.edges.push({from:"FirstName",to:"Contact"});
		ret.top_graph.edges.push({from:"LastName",to:"Concat"});
		ret.top_graph.edges.push({from:"FirstName",to:"Concat"});
		response.forEach(function(el,el_idx){
			ret.top_graph.nodes.push({id:el.name+"_Thread",type:""});
			ret.top_graph.edges.push({from:"Contact",to:el.name+"_Thread"});
			ret.top_graph.edges.push({from:"Concat",to:el.name+"_Thread"});
			var n_child={
				"name":el.name,
				"top_graph":{"edges":[],"nodes":[]},
				"children":[]
			};
			el.contacts.forEach(function(e,idx){
				n_child.top_graph.nodes.push({id:e.id,type:"Contact"});
				if(e.lastName!=""){
					n_child.top_graph.nodes.push({id:e.lastName+"_"+idx,type:"LastName"});
					n_child.top_graph.edges.push({from:e.lastName+"_"+idx,to:e.id});
				}if(e.firstName!=""){
					n_child.top_graph.nodes.push({id:e.firstName+"_"+idx,type:"FirstName"});
					n_child.top_graph.edges.push({from:e.firstName+"_"+idx,to:e.id});
				}
			});
			el.threads.forEach(function(e,idx){
				if(e.length>0){
					n_child.top_graph.nodes.push({id:"cvt_"+idx,type:el.name+"_Thread"});
					e.forEach(function(node){
						n_child.top_graph.edges.push({from:node,to:"cvt_"+idx});
					});
				}
			});
			ret.children.push(n_child);
		});
		console.log(ret);
		return dispatch.call(
			"graphFileLoaded",
			this,
			{"hierarchy":ret,"coord":{},"type":type}
		);
	});
},
/* convert the old Kami 2.0 graph format to the new Regraph Format
 * Convert a nugget list into a graph tree with the action graph as root and each action as nugget leafs
 * @input : json_file : a Kami 2.0 Json File
 * @input : dispatch : the dispatch event object
 * @input : type : the graph type
 * @output : a Regraph Json File
*/ 
kamiToRegraph:function(json_file,dispatch,type){
	d3.json(json_file,function(response){
		if(!response.version){
			dispatch.call("graphFileLoaded",this,{"hierarchy":response,"coord":null,"type":type});
			return;
		}
		//rename graph objects in the new format
		cvt_dico ={"agent":"agent","region":"region","key_res":"residue","attribute":"attribute","flag":"flag","mod":"mod","bnd":"bind","brk":"unbind"};
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
		/* get an element father id
		 * @input : the element father
		 * @return : if no father : error, else return the father id
		 */
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
		//for each action, create a new graph corresponding to its nugget and add it to the action graph
		response.actions.forEach(function(e,i){
			addToACT(e,i);
			addToNug(e,i);
		});
		/* get the value of a specific object for mod actions
		 * @input : e : the element type
		 * @input : ee : the element idx
		 * @ return : the element value after mod action
		 */
		function getCVal(e,ee){
			let tmp_ref = response[ee.ref[0]][ee.ref[1]];
			return tmp_ref.values[tmp_ref.values.indexOf(ee.values[0])+(e.classes[2]=="pos"?1:-1)];
		};
		/* add elements to the action graph :
		 * @input e : the element
		 * @input i : a counter avoiding elements with same name
		 * @return : modify the ret object.
		 */
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
						"type":"value"
					});
					ret.top_graph.nodes.push({
						"id":e.labels.join("_")+"_"+i+"_"+getCVal(e,ee),
						"type":"value"
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
		/* add elements to the nugget graphs :
		 * @input act : the action
		 * @input i : a counter avoiding elements with same name
		 * @return : modify the ret object.
		 */
		function addToNug(act,i){
			var inst_cpt = 0;
			//the new nugget for this action
			var n_child={
				"name":act.labels.join()+"_"+i,
				"top_graph":{"edges":[],"nodes":[]},
				"children":[]
			};
			//add the action node
			n_child.top_graph.nodes.push({
				"id":act.labels.join("_")+"_"+i,
				"type":act.labels.join("_")+"_"+i
			});	
			//add the action binders 
			n_child.top_graph.nodes.push({
				"id":act.labels.join("_")+"_"+i+"_left",
				"type":act.labels.join("_")+"_"+i+"_left"
			});
			n_child.top_graph.nodes.push({
				"id":act.labels.join("_")+"_"+i+"_right",
				"type":act.labels.join("_")+"_"+i+"_left"
			});
			//add the nugget content (all nodes and edges)
			["left","right","context"].forEach(function(ctx){
				act[ctx].forEach(function(e){
					var tmp_node = response[e.ref[0]][e.ref[1]];
					//if the node is a bind
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
						//add all node values
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
						//for left and right elements : add edges
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
		dispatch.call("graphFileLoaded",this,{"hierarchy":ret,"coord":coord,"type":type});
	});
},
/* export a given graph into a json file
 * open a new windows with the json file
 *  if there exist coordinate for nodes in the graph, output them in an other file
 * @input : ret : the graph hierarchy object
 * TODO : add coordinate to graph object !
 */
exportGraph:function(ret){
	var url = 'data:text/json;charset=utf8,' + encodeURIComponent(JSON.stringify(ret.hierarchy,null,"\t"));
		window.open(url, '_blank');
		window.focus();
	if(ret.coord){
		var url2 = 'data:text/json;charset=utf8,' + encodeURIComponent(JSON.stringify(ret.coord,null,"\t"));
			window.open(url2, '_blank');
	}
	
},
/* add cordinates to a graph
 * @input : coord : a coordinate hashtable for each nodes
 * @input : graphic_g : the interactive graph to updateCommands
 * TODO : this function
 */
loadCoord:function(coord,graphic_g){
	console.log("not implemented");
}
}});