define([],function(){return function Tree(){
	var nodes ={}
	var root = null;
	var self=this;
	this.addNode = function addNode(id,fth){
		if(!id) throw new Error("addNode need to be call with a node id");
		if(fth && !nodes[fth]) throw new Error("Unable to find this node father : "+fth);
		nodes[id]={"fth":fth?fth:null,sons:{}};
		if(fth) nodes[fth].sons[id]=true;
		if(!fth && root) throw Error("There is already a root node");
		if(!fth && !root) root = id;
		return id;
	};
	this.rmNode = function rmNode(id){
		if(!id) throw new Error("rmNode need to be call with a node id");
		if(!nodes[id]) throw new Error("Unable to find this node : "+id);
		delete nodes[nodes[id].fth].sons[id];
		Object.keys(nodes[id].sons).forEach(function(e){
			rmNode(e);
		});
		delete nodes[id];		
		return id;
	};
	this.getRoot = function getRoot(){
		return root;
	};
	this.getFather = function getFather(id){
		if(!id) throw new Error("getFather need to be call with a node id");
		if(!nodes[id]) throw new Error("Unable to find this node : "+id);
		return nodes[id].fth;
	};
	this.getSons = function getSons(id){
		if(!id) throw new Error("getSons need to be call with a node id");
		if(!nodes[id]) throw new Error("Unable to find this node : "+id);
		return Object.keys(nodes[id].sons);
	};
	this.getAbsPath = function getAbsPath(id){
		if(!id) throw new Error("getAbsPath need to be call with a node id");
		if(!nodes[id]) throw new Error("Unable to find this node : "+id);
		if(id == root) return [id];
		else return getAbsPath(nodes[id].fth).concat([id]);
	};
	this.log = function log(){
		console.log("root : "+root);
		console.log(nodes);
	};
	this.importTree = function importTree(tree,id_map,fth){
		self.addNode(tree[id_map.id],fth);
		tree[id_map.sons].forEach(function(e){
			importTree(e,id_map,tree[id_map.id]);
		});
	};
}});