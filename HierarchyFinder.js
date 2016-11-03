define(["ressources/d3/d3.js","ressources/simpleTree.js"],function(d3,Tree){return function HierarchyFinder(container_id,server_url,dispatch){
	var disp = dispatch;
	var container = d3.select("#"+container_id).append("div").attr("id","hierarchy");
	var hierarchy = new Tree();
	var h_select = container.append("select").attr("id","h_select");
	var h_list = container.append("ul").attr("id","h_list");
	var current_node = null;
	var self=this;
	if(!server_url) throw new Error("server url undefined");
	var srv_url = server_url;
	this.init = function init(root){
		h_select.selectAll("*").remove();
		h_list.selectAll("*").remove();
		hierarchy = new Tree();
		loadHierarchy(root);
	};
	function loadHierarchy (root){
		var request = d3.json(srv_url+"hierarchy"+root+"?include_graphs=false&rules=false",function(response){
				hierarchy.importTree(response,{"id":"name","sons":"children"},null);
				if(current_node){
					root=current_node;
					current_node = null;
				}
				update(root);
				dispatch.call("load",this,[root]);
			});
	};
	this.log = function log(){
		hierarchy.log();
		console.log("current node : "+current_node);
	};
	function update(new_node){
		console.log("update : "+new_node);
		if(new_node == current_node) return;
		current_node = new_node;
		h_select.selectAll("*").remove();
		h_list.selectAll("*").remove();
		//.on("click",function(d){console.log("hierarchy clicked : "+d);disp.call("statechange",this,hierarchy.getAbsPath(d));return update(d)})
		h_select.selectAll("option")
			.data(hierarchy.getAbsPath(current_node))
			.enter().append("option")
				.text(function(d){return d})
				.attr("selected",function(d){return d==current_node});
		h_select.on("change",function(){ 
			var si   = h_select.property('selectedIndex'),
			s    = h_select.selectAll("option").filter(function (d, i) { return i === si }),
			data = s.datum();
			disp.call("statechange",this,hierarchy.getAbsPath(data));return update(data)
		});
		h_list.selectAll("li")
			.data(hierarchy.getSons(current_node))
			.enter().append("li")
				.text(function(d){return d})
				.on("click",function(d){disp.call("statechange",this,hierarchy.getAbsPath(d));return update(d)});		
	};
	this.getCNode = function getCNode(){
		return hierarchy.getAbsPath(current_node);
	};
}});