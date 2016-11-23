define([],function(){return function Tree(){
	var nodesHash = {};
	var NODE_ID = 0;
	this.load = function load(json_hie){
		importTree(json_hie);
	}
	function importTree(json_hie,ctx,fth){
		if(!ctx) ctx ="";
		if(!fth) fth = "n_-1";
		var id = "n_"+(NODE_ID++);
		nodesHash[id] = {name:json_hie.name,path:ctx,father:fth,children:[]};
		if(fth!="n_-1"){nodesHash[fth].children.push(id);}
		json_hie.children.forEach(function(e){
			var is_slash = ctx==""||ctx=="/"?"":"/";
			importTree(e,ctx+is_slash+json_hie.name,id);
		});
	};
	this.getFather = function getFather(n_id){
		return nodesHash[n_id].father;
	};
	this.getSons = function getSons(n_id){
		return nodesHash[n_id].children.concat();
	};
	this.getName = function getName(n_id){
		return nodesHash[n_id].name;
	};
	this.getPath = function getPath(n_id){
		return nodesHash[n_id].path;
	};
	this.getAbsPath = function getAbsPath(n_id){
		let is_slash = nodesHash[n_id].path==""||nodesHash[n_id].path=="/"?"":"/";
		return nodesHash[n_id].path+is_slash+nodesHash[n_id].name;
	};
	this.log = function log(){
		console.log(nodesHash);
	};
	this.getRoot = function getRoot(){
		return "n_0";
	};
	this.getTreePath = function getTreePath(n_id){
		var ret=[];
		while(n_id!="n_-1"){
			ret.unshift(n_id);
			n_id=nodesHash[n_id].father;
		};
		return ret;
	};
}});