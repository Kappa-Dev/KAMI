/* This module create a simple tree structure
 * This module can be used independantly from regraphGui
 * this module return a Tree Object
 * @ Author Adrien Basso blandin
 * This module is part of regraphGui project
 * this project is under AGPL Licence
*/
define([],function(){return function Tree(){
	var nodesHash = {};//hashtable of nodes
	var NODE_ID = 0;//id count
	/* load a new tree from a json hierarchy fileCreatedDate
	 * @input : json_hie : the json hierarchy
	 */
	this.load = function load(json_hie){
		nodesHash = {};
		NODE_ID = 0;
		importTree(json_hie);
	}
	/* internal recursive function building a tree
	 * @input : json_hie : the json hierarchy structure
	 * @input : ctx : the string path of the current nodeName
	 * @input : fth : the father id of the current node
	 */
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
	/* return the id of the father of a node
	 * @input : n_id : the node id
	 * @return : the node father id
	 */
	this.getFather = function getFather(n_id){
		return nodesHash[n_id].father;
	};
	/* return the id list of sons of a node
	 * @input : n_id : the node id
	 * @return : the node sons id list
	 */
	this.getSons = function getSons(n_id){
		return nodesHash[n_id].children.concat();
	};
	/* return the name of a node
	 * @input : n_id : the node id
	 * @return : the node name
	 */
	this.getName = function getName(n_id){
		return nodesHash[n_id].name;
	};
	/* return the path of a node
	 * @input : n_id : the node id
	 * @return : the node path
	 */
	this.getPath = function getPath(n_id){
		return nodesHash[n_id].path;
	};
	/* return the absolute path of a node
	 * @input : n_id : the node id
	 * @return : the node absolute path
	 */
	this.getAbsPath = function getAbsPath(n_id){
		let is_slash = nodesHash[n_id].path==""||nodesHash[n_id].path=="/"?"":"/";
		return nodesHash[n_id].path+is_slash+nodesHash[n_id].name;
	};
	/* log the current tree
	 *  for dev purpose
	 */
	this.log = function log(){
		console.log(nodesHash);
	};
	/* return the id of the root of the tree
	 * @return : the id of the root
	 */
	this.getRoot = function getRoot(){
		return "n_0";
	};
	/* return the path of a node as an id list
	 * @input : n_id : the node id
	 * @return : the node path
	 */
	this.getTreePath = function getTreePath(n_id){
		var ret=[];
		while(n_id!="n_-1"){
			ret.unshift(n_id);
			n_id=nodesHash[n_id].father;
		};
		return ret;
	};
}});