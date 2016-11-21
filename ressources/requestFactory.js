define(["ressources/d3/d3.js"],function(d3){
	return function RequestFactory(url){
		var self = this;
		var srv = url;
		function request(type,loc,path,urlparam,content_type,callback,data,rsp_pars){
			var url_param_string = "" ;
			if(url_param_string && url_param_string.length>0){
				urlparam.reduce(function(accu,e,i){
					accu+=e.id+"="+e.val+(i<urlparam.length-1?"&":"?");
				},url_param_string);
			}
			var rq = d3.request(srv+loc+path+url_param_string)
				.mimeType(content_type)
				.header("Content-Type", content_type)
				.response(function(xhr){return rsp_pars?rsp_pars(xhr.responseText):xhr.responseText;})
				.on("error", function(error) { errorCb(error); })
			//if(type == "GET")	
				if(type == "POST") 
					rq.header("X-Requested-With", "XMLHttpRequest")
				rq.on("load", function(xhr) { callback(null, xhr); });
				rq.send(type,data);
			/*else
				rq.on("load", function(xhr) { selfCallback(null, xhr,loc); })
				.send(type,data);	*/	
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
				function(err,resp){console.log(resp);return self.getHierarchy("/",callback)},
				null,
				null);
		};
		this.addHierarchy = function addHierarchy(hie_path,data,callback){
			d3.request(srv+"/hierarchy"+hie_path)
				.header("X-Requested-With", "XMLHttpRequest")
				.header("Content-Type", "application/json")
				.post(data, function(err,resp){console.log(resp);return self.getHierarchy("/",callback)});
		};
		this.mergeHierarchy = function mergeHierarchy(hie_path,data,callback){
			console.log("this is useless");
		};
		this.addRule = function addRule(rule_path,pattern,callback){
			d3.request(srv+"/rule"+rule_path+"?pattern_name="+pattern)
				.header("X-Requested-With", "XMLHttpRequest")
				.header("Content-Type", "application/json")
				.post(null, function(err,resp){console.log(err);console.log(resp);return self.getHierarchy("/",callback)});
		};
		this.graphFromRule = function graphFromRule(graph_path,src_gr,rule_n,data,callback){
			d3.request(srv+"/graph/apply"+graph_path+"?target_graph="+src_gr+"&rule_name="+rule_n)
				.header("X-Requested-With", "XMLHttpRequest")
				.header("Content-Type", "application/json")
				.post(data, function(err,resp){console.log(err);console.log(resp);return self.getHierarchy("/",callback)});
		};
		
	}
});