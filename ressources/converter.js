define(["ressources/d3/d3.js"],function(d3){ return {convert:function(json_file){
	d3.json(json_file,function(response){
		cvt_dico ={"agent":"agent","region":"region","key_res":"residue","attribute":"values","flag":"values","mod":"mod","bnd":"bind","brk":"unbind"};
		var ret={"name":"ActionGraph",
			"top_graph":{
				"edges":[],
				"nodes":[]				
			},
			"children":[]
		};
		function expt(node){
			response[node].forEach(function(e,i){
				var cvt_node = {
					"id":e.labels.join("_")+"_"+i,
					"type":cvt_dico[e.classes[0]]
				};
				ret.top_graph.nodes.push(cvt_node);
			});
		}
		expt("agents");
		expt("regions");
		expt("key_rs");
		expt("attributes");
		expt("flags");	
		response.actions.forEach(function(e,i){		
			var n_child={"name":e.labels.join()+"_"+i,
			"top_graph":{
				"edges":[],
				"nodes":[]
			},
			"children":[]
			};
			var act_node = {
				"id":e.labels.join("_")+"_"+i,
				"type":cvt_dico[e.classes[1]]
			};
			var goTest={"bind":"binded","unbind":"freed"};
			if(e.classes[1]!="mod"){
			var test_node = {
				"id":e.labels.join("_")+"_"+i+"_tst",
				"type":goTest[cvt_dico[e.classes[1]]]
			};
			ret.top_graph.nodes.push(test_node);
			}
			ret.top_graph.nodes.push(act_node);
			
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
	});
}}
		

});