define(["ressources/d3/d3.js","ressources/simpleTree.js","ressources/requestFactory.js"],function(d3,Tree,RFactory){
	return function Hierarchy(container_id,dispatch,server_url){
		if(!server_url) throw new Error("server url undefined");
		var srv_url = server_url;//the current url of the server
		var disp = dispatch;//global dispatcher for events
		var container = d3.select("#"+container_id).append("div").attr("id","hierarchy");//the hierarchy container
		var hierarchy;//a tree containing the whole hierarchy
		var h_select = container.append("select").attr("id","h_select");//the hierarchy selector
		var h_list = container.append("ul").attr("id","h_list");//the list of son of the specified node
		var current_node = null;//the current selected node
		var self=this;
		
		this.update = function update(root,node){
			/*d3.request(srv_url+"hierarchy"+root+"?include_graphs=false&rules=false")
				.mimeType("application/json")
				.response(function(xhr) { return JSON.parse(xhr.responseText); })
				.on("error", function(error) { callback1(error); })
				.on("load", function(xhr) { callback2(null, xhr); })
				.send("GET");
			
			*/
			var fac=new RFactory(srv_url);
			//fac.getHierarchy(root,callback2);
			var data = {"name":"Seb-test","rules":[],"top_graph":{"nodes":[],"edges":[]},"children":[]};
			fac.graphFromRule("/MetaKami_2016_11_10/MetaModel/ActionGraph/new_g","EGFR internal unbinding_13","myrule",JSON.stringify(data,null,"\t"),callback2);
			function callback2 (err,response){
				console.log(response);	
			}
		};
		
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	}
});