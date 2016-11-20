define(["ressources/d3/d3.js","ressources/simpleTree.js"],function(d3,Tree){
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
			d3.json(srv_url+"hierarchy"+root+"?include_graphs=false&rules=false",function(response){
				hierarchy = new Tree();
				hierarchy.importTree(response);
				if(node) {
					if(node!=current_node) disp.call("graphUpdate",this,node);
					current_node = node;
				}
				else if(!hierarchy.exist(current_node)){
					current_node = hierarchy.getRoot();
					disp.call("graphUpdate",this,current_node);
				}
				selectUpdate();
				h_listUpdate();	
			});
		};
		function selectUpdate(){
			h_select.selectAll("*").remove();
			h_select.selectAll("option")
			.data(hierarchy.getAbsPath(hierarchy.getFather(current_node)))
			.enter().append("option")
				.text(function(d){return d})
				.attr("selected",function(d){return d==hierarchy.getFather(current_node)});
			h_select.on("change",function(){ 
				var si = h_select.property('selectedIndex'),
					s = h_select.selectAll("option").filter(function (d, i) { return i === si }),
					data = s.datum();
					var new_path=hierarchy.getAbsPath(hierarchy.getFather(current_node)).splice(0,si+1);
					
			};
		function h_listUpdate(){
			
		};
		
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	}
});