define(["ressources/d3/d3.js"],function(d3){ return {

/* convert the old Kami 2.0 graph format to the new Regraph Format
 * Convert a nugget list into a graph tree with the action graph as root and each action as nugget leafs
 * @input json_file : a Kami 2.0 Json File
 * @output : a Regraph Json File
*/ 
kamiToRegraph:function(json_file){
	d3.json(json_file,function(response){
		//rename graph objects in the new format
		cvt_dico ={"agent":"agent","region":"region","key_res":"residue","attribute":"values","flag":"values","mod":"mod","bnd":"bind","brk":"unbind"};
		cls_to_js_id = {"agent":"agents","region":"regions","flag":"flags","attribute":"attributes","key_res":"key_rs"}
		//OutPut object
		var ret={
			"name":"ActionGraph",
			"top_graph":{"edges":[],"nodes":[]},
			"children":[]
		};
		/* convert @input kami node type into a regraph node list and add it to the output graph */
		["agents","regions","key_rs","attributes","flags"].forEach(function(node_type){
			response[node_type].forEach(function(e,i){
				ret.top_graph.nodes.push({
					"id":e.labels.join("_")+"_"+i,
					"type":cvt_dico[e.classes[0]]
				});
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
			response[cls_to_js_id[e.father_classes]].forEach(function(ee,i){
				if(ee.labels.indexOf(e.path[e.path.lenght-1])!=-1 && e.path.slice(0,e.path.lenght-1).join()==ee.path.join())
				ret=ee.labels.join("_")+"_"+i	
			});
			if(!ret) throw new Error ("This node' father doesn't exist");
			return ret;
		};
		// for each action, create a new graph corresponding to its nugget and add it to the action graph
		response.actions.forEach(function(e,i){
			addToACT(e,i);
			addToNug(e,i);
		};
		function addToACT(e,i){
			//the action node
			var act_node = {
				"id":e.labels.join("_")+"_"+i,
				"type":cvt_dico[e.classes[1]]
			};
			ret.top_graph.nodes.push(act_node);
			if (e.classes[1]=="brk"){
				["left","right"].forEach(function(obj){
					e[obj].forEach(function(ee,ii){ret.top_graph.edges.push({
						"from":e.labels.join("_")+"_"+i,
						"to":response[ee.ref[0]][ee.ref[1]].labels.join("_")+"_"+ee.ref[1]
					})});
				});
			} else if(e.classes[1]=="mod"){
				e.right.forEach(function(ee,ii){ret.top_graph.edges.push({
					"from":e.labels.join("_")+"_"+i,
					"to":response[ee.ref[0]][ee.ref[1]].labels.join("_")+"_"+ee.ref[1]
				})});
			}else if(e.classes[1]=="bnd"){
				ret.top_graph.nodes.push({
					"id":e.labels.join("_")+"_"+i+"_btst",
					"type":"binded"
				});
				["left","right"].forEach(function(obj){
					e[obj].forEach(function(ee,ii){
						ret.top_graph.edges.push({
							"from":response[ee.ref[0]][ee.ref[1]].labels.join("_")+"_"+ee.ref[1],
							"to":e.labels.join("_")+"_"+i
						});
						ret.top_graph.edges.push({
							"from":response[ee.ref[0]][ee.ref[1]].labels.join("_")+"_"+ee.ref[1],
							"to":e.labels.join("_")+"_"+i+"_btst"
						});
					});
				});				
			}	
		};
		//the nugget graph
		function addToNug(act,idx){
			var n_child={
				"name":e.labels.join()+"_"+i,
				"top_graph":{"edges":[],"nodes":[]},
				"children":[]
			};
			
			ret.children.push(n_child);
		};
		
			
			
			//also add the action in the nugget
			n_child.top_graph.nodes.push({
				"id":e.labels.join("_")+"_"+i,
				"type":e.labels.join("_")+"_"+i
			});
			function cvt_n(cvt){
				e[cvt].forEach(function(ee,ii){
				var tmp_node = response[ee.ref[0]][ee.ref[1]];
				var cvt_node = {
					"id":tmp_node.labels.join("_")+"_"+ee.ref[1]+"_"+cvt,
					"type":tmp_node.labels.join("_")+"_"+ee.ref[1]
				};
				if(cvt =="context" && ee.ref[0]=="actions" )
					cvt_node.type+="_tst";
				n_child.top_graph.nodes.push(cvt_node);
				if(cvt == "left" || cvt =="right"){
					n_child.top_graph.edges.push({"from":act_node.id,"to":cvt_node.id});
					ret.top_graph.edges.push({"from":act_node.id,"to":cvt_node.type});
				}
			})};
			cvt_n("left");
			cvt_n("right");
			cvt_n("context");
			ret.children.push(n_child);
		});
		var url = 'data:text/json;charset=utf8,' + encodeURIComponent(JSON.stringify(ret,null,"\t"));
		window.open(url, '_blank');
		window.focus();
	}
}}});