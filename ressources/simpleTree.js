define([],function(){return function Tree(){
	
	function s: fullpath(node) -> return the full path of a node in the hierarchy
	
	
	var nodes ={}
	var p = {};
	var root = null;
	var self=this;
	this.addNode = function addNode(path,ctx){
		if(!path) throw new Error("undefined path");
		if(ctx) path = p2l(ctx).concat([path]);
		else path = p2l(path);
		path.reduce(function(accu,val,idx){
			if(idx == path.length-1) accu[val]={};
			if(idx<path.length-1 && !accu[val]) throw new Error("unable to complet path : "+path+" from "+val);
			return accu[val];
		},nodes);
    if(!root) root = Object.keys(nodes)[0];
    else if(Object.keys(nodes)[0]!=root) throw new Error("Multiple root names are not allowed !");
	};
	this.rmNode = function rmNode(path,ctx){
		if(!path) throw new Error("undefined path");
		if(ctx) path = p2l(ctx).concat([path]);
		else path = p2l(path);
		path.reduce(function(accu,val,idx){
			if(!accu[val]) throw new Error("unable to complet path : "+path+" from "+val);
			if(idx == path.length-1){
				delete accu[val];
				return;
			}
			return accu[val];
		},nodes);
		if(Object.keys(nodes).length == 0) root = null;
	};
	this.getRoot = function getRoot(){
		return root;
	};
	this.getFather = function getFather(path){
		var fth = p2l(path);
		fth.pop();
		return {str:l2p(fth),l:fth};
	};
	function p2l(path){
		if(!path) throw new Error("empty path");
		if(typeof path != "string") return path;
		if(path =="/") return ["/"];
		var ret = path.split("/");
		ret[0] = "/";
		return ret;
	};
	function l2p(l){
		if(!l) throw new Error("empty path");
		if(typeof l == "string") return l;
		if(l.length==1) return "/";
		var ret = l.concat();
		ret[0]="";
		return ret.join("/");
	};
	this.getSons = function getSons(path){
		var npath = p2l(path);
		var ret =[];
		npath.reduce(function(accu,val,idx){
			if(!accu[val]) throw new Error("unable to complet path : "+npath+" from "+val);
			if(idx == npath.length-1){
				ret = Object.keys(accu[val]);
				return;
			}
			return accu[val];
		},nodes);
		return ret;
	};
	this.log = function log(){
		console.log("root : "+root);
		console.log(nodes);
	};
	 this.importTree = function importTree(tree,ctx){
		self.addNode(tree.name,ctx);
		tree.children.forEach(function(e){
    	if(!ctx) ctx ="";
			importTree(e,ctx+tree.name);
		});
	};
}});