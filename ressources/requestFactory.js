define(["ressources/d3/d3.js"],function(d3){
	return function RequestFactory(url){
		var self = this;
		var srv = url;
		function request(type,loc,path,urlparam,content_type,callback,data,rsp_pars){
			var url_param_string = "" ;
			if(urlparam && urlparam.length>0){
				url_param_string=urlparam.reduce(function(accu,e,i){
					return accu+=e.id+"="+e.val+(i<urlparam.length-1?"&":"");
				},"?");
			}
			var rq = d3.request(srv+loc+path+url_param_string)
				.mimeType(content_type)
				.response(function(xhr){return rsp_pars?rsp_pars(xhr.responseText):xhr.responseText;})
				.on("error", function(error) { errorCb(error); })
				if(type == "POST") 
					rq.header("X-Requested-With", "XMLHttpRequest")
				rq.on("load", function(xhr) { callback(null, xhr); });
				rq.send(type,data);
		};
		function errorCb(error){
			console.error("unable to complete request :");
			console.error(error);
		}
		this.getHierarchy = function getHierarchy(hie_path,callback){
			request("GET",
				"/hierarchy",
				hie_path,
				[{id:"include_graphs",val:false},{id:"rules",val:false}],
				"application/json",
				callback,
				null,
				JSON.parse);
		};
		this.getGraph = function getGraph(gr_path,callback){
			request("GET",
				"/graph",
				gr_path,
				null,
				"application/json",
				callback,
				null,
				JSON.parse);
		};
		this.getMatching = function getMatching(gr_path,rule_path,callback){
			request("GET",
				"/graph/matchings",
				gr_path,
				[{id:"rule_name",val:rule_path}],
				"application/json",
				callback,
				null,
				JSON.parse);
		};
		this.getRule = function getRule(gr_path,rule_name,callback){
			request("GET",
				"/hierarchy",
				gr_path,
				[{id:"include_graphs",val:false},{id:"rules",val:true}],
				"application/json",
				function(err,resp){return callback(err,subRule(rule_name,resp))},
				null,
				JSON.parse);
		};
		function subRule(r_name,resp){
			if(!resp.rules){
				console.error("this hierarchy has no rules");
				return {};
			}
			var r_idx = resp.rules.indexOf(r_name);
			if(r_idx<0) throw new Error("unable to find this rule : "+r_name)
			return resp.rules[r_idx];
		};
		this.delHierarchy = function delHierarchy(hie_path,callback){
			request("DELETE",
				"/hierarchy",
				hie_path,
				null,
				"text/html",
				callback,
				null,
				null);
		};
		this.addHierarchy = function addHierarchy(hie_path,data,callback){
			d3.request(srv+"/hierarchy"+hie_path)
				.header("X-Requested-With", "XMLHttpRequest")
				.header("Content-Type", "application/json")
				.post(data, callback);
		};
		this.mergeHierarchy = function mergeHierarchy(hie_path,data,callback){
			console.log("this is useless");
		};
		this.addRule = function addRule(rule_path,pattern,callback){
			d3.request(srv+"/rule"+rule_path+"?pattern_name="+pattern)
				.header("X-Requested-With", "XMLHttpRequest")
				.header("Content-Type", "application/json")
				.post(null, callback);
		};
		this.graphFromRule = function graphFromRule(graph_path,src_gr,rule_n,data,callback){
			d3.request(srv+"/graph/apply"+graph_path+"?target_graph="+src_gr+"&rule_name="+rule_n)
				.header("X-Requested-With", "XMLHttpRequest")
				.header("Content-Type", "application/json")
				.post(data, callback);
		};
		this.delGraph = function delGraph(gr_path,callback){
			request("DELETE",
				"/graph",
				gr_path,
				null,
				"text/html",
				callback,
				null,
				null);
		};
		this.addNode = function addNode(g_path,n_id,n_type,callback){
			request("PUT",
				"/graph/add_node",
				g_path,
				[{id:"node_id",val:n_id},{id:"node_type",val:n_type}],
				"text/html",
				callback,
				null,
				null);
		};
		this.rmNode = function rmNode(g_path,n_id,force,callback){
			request("PUT",
				"/graph/rm_node",
				g_path,
				[{id:"node_id",val:n_id},{id:"force",val:force}],
				"text/html",
				callback,
				null,
				null);
		};
		this.mergeNode = function mergeNode(g_path,n_id1,n_id2,new_id,force,callback){
			request("PUT",
				"/graph/merge_node",
				g_path,
				[{id:"force",val:force},{id:"node1",val:n_id1},{id:"node2",val:n_id2},{id:"new_node_id",val:new_id}],
				"text/html",
				callback,
				null,
				null);
		};
		this.cloneNode = function cloneNode(g_path,n_id,new_id,callback){
			request("PUT",
				"/graph/clone_node",
				g_path,
				[{id:"node_id",val:n_id},{id:"new_node_id",val:new_id}],
				"text/html",
				callback,
				null,
				null);
		};
		this.addEdge = function addEdge(g_path,src,trg,callback){
			request("PUT",
				"/graph/add_edge",
				g_path,
				[{id:"source_node",val:src},{id:"target_node",val:trg}],
				"text/html",
				callback,
				null,
				null);
		};
		this.rmEdge = function rmEdge(g_path,src,trg,force,callback){
			request("PUT",
				"/graph/rm_edge",
				g_path,
				[{id:"source_node",val:src},{id:"target_node",val:trg},{id:"force",val:force}],
				"text/html",
				callback,
				null,
				null);
		};
		this.rnGraph = function rnGraph(g_path,name,callback){
			request("PUT",
				"/graph/rename_graph",
				g_path,
				[{id:"new_name",val:name}],
				"text/html",
				callback,
				null,
				null);
		};
		this.addGraph = function addGraph(gr_path,callback){
			d3.request(srv+"/graph"+gr_path)
				.header("X-Requested-With", "XMLHttpRequest")
				.post(null, callback);
		};
		this.ruleaddNode = function ruleaddNode(g_path,n_id,n_type,callback){
			request("PUT",
				"/rule/add_node",
				g_path,
				[{id:"node_id",val:n_id},{id:"node_type",val:n_type}],
				"text/html",
				callback,
				null,
				null);
		};
		this.rulermNode = function rulermNode(g_path,n_id,force,callback){
			request("PUT",
				"/rule/rm_node",
				g_path,
				[{id:"node_id",val:n_id},{id:"force",val:force}],
				"text/html",
				callback,
				null,
				null);
		};
		this.rulemergeNode = function rulemergeNode(g_path,n_id1,n_id2,new_id,force,callback){
			request("PUT",
				"/rule/merge_node",
				g_path,
				[{id:"node1",val:n_id1},{id:"node2",val:n_id2},{id:"new_node_id",val:new_id},{id:"force",val:force}],
				"text/html",
				callback,
				null,
				null);
		};
		this.rulecloneNode = function rulecloneNode(g_path,n_id,new_id,callback){
			request("PUT",
				"/rule/clone_node",
				g_path,
				[{id:"node_id",val:n_id},{id:"new_node_id",val:new_id}],
				"text/html",
				callback,
				null,
				null);
		};
		this.ruleaddEdge = function ruleaddEdge(g_path,src,trg,callback){
			request("PUT",
				"/rule/add_edge",
				g_path,
				[{id:"source_node",val:src},{id:"target_node",val:trg}],
				"text/html",
				callback,
				null,
				null);
		};
		this.rulermEdge = function rulermEdge(g_path,src,trg,force,callback){
			request("PUT",
				"/rule/rm_edge",
				g_path,
				[{id:"source_node",val:src},{id:"target_node",val:trg},{id:"force",val:force}],
				"text/html",
				callback,
				null,
				null);
		};
		this.rnRule = function rnRule(g_path,name,callback){
			request("PUT",
				"/rule/rename_graph",
				g_path,
				[{id:"new_name",val:name}],
				"text/html",
				callback,
				null,
				null);
		};
		this.addConstraint = function addConstraint(g_path,n_id,e_type,cstr,bnd,order,callback){
			request("PUT",
				"/graph/add_constraint",
				g_path,
				[{id:"node_id",val:n_id},
				{id:"input_or_output",val:e_type},
				{id:"constraint_node",val:cstr},{id:"bound",val:bnd},{id:"le_or_ge",val:order}],
				"text/html",
				callback,
				null,
				null);
		};
		this.rmConstraint = function rmConstraint(g_path,n_id,e_type,cstr,bnd,order,callback){
			request("PUT",
				"/graph/delete_constraint",
				g_path,
				[{id:"node_id",val:n_id},
				{id:"input_or_output",val:e_type},
				{id:"constraint_node",val:cstr},{id:"bound",val:bnd},{id:"le_or_ge",val:order}],
				"text/html",
				callback,
				null,
				null);
		};
		this.validate = function validate(g_path,callback){
			request("PUT",
				"/graph/validate_constraint",
				g_path,
				null,
				"text/html",
				callback,
				null,
				null);
		};
		
		
		
	}
});