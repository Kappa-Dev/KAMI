define([],function(){return function Node(i,t,l){//generic definition of a node in a hierarchycal graph
	if(typeof i=='undefined' || i==null) throw new Error("undefined id : "+i);
	var id=i;//unique identifier of a node
	var labels=l || {};
	if(!t) throw new Error("undefined type : "+t);
	var type=t;
	var input_nodes={};
	var output_nodes={};
	this.getId = function getId(){// return the node id O(1)
		return id;
	};
	this.getType = function getType(){//return the node type : O(1)
		return type;
	};
	this.setType = function setType(u){//change the node type : O(1)
		if(typeof u=='undefined' || u==null) throw new Error("undefined type : "+u);
		type=u;
	};
	this.getLabels = function getLabels(){//return the node labels (new array) : O(l) 
		return Object.keys(labels);
	};
	this.addLabels = function addLabels(l){//add all new labels from l to the node labels : O(l) : max labels size
		if(l)
			l.forEach(function(e){labels[e]=true});
	};
	this.rmLabels = function rmLabels(l){//remove the specified label from the node node labels (only the element of l in the node label are removed) : O(l) : max list size : if l is null/undefined, remove all the labels
		if(l)
			l.forEach(function(e){delete labels[l]});
		else
			labels={};
	};
	this.getInputNodesCt = function getInputNodesCt(i_n){//return the constrainte for the specific node id : O(1), no nodes are specified return the full min and max arrity of this node
		if(i_n){
			if(!input_nodes[i_n]) return {min:null,max:null};
			return {min:input_nodes[i_n].min,max:input_nodes[i_n].max};
		}
		else
			Object.keys(input_nodes).reduce(function(accu,e){
				accu.min=null?input_nodes[e].min:accu.min+input_nodes[e].min;
				accu.max=null?input_nodes[e].max:accu.max+input_nodes[e].max;
				return accu;
			},{min:null,max:null});
	};
	this.addInputNodesCt = function addInputNodesCt(v, i_n,sign){//add an input node constrainte, if v is undefined/null, remove constrainte
		if(!i_n) throw new Error("undefined node : "+i_n);
		if(!input_nodes[e_t])input_nodes[e_t]={min:null,max:null};
		if(!v) v = null;
		input_nodes[i_n][sign]=v;
	};
	this.getOutputNodesCt = function getOutputNodesCt(i_n){//return the constrainte for the specific node id : O(1), no nodes are specified return the full min and max arrity of this node
		if(i_n){
			if(!output_nodes[i_n]) return {min:null,max:null};
			return {min:output_nodes[i_n].min,max:output_nodes[i_n].max};
		}
		else
			Object.keys(output_nodes).reduce(function(accu,e){
				accu.min=null?output_nodes[e].min:accu.min+output_nodes[e].min;
				accu.max=null?output_nodes[e].max:accu.max+output_nodes[e].max;
				return accu;
			},{min:null,max:null});
	};
	this.addOutputNodesCt = function addOutputNodesCt(v, i_n,sign){//add an input node constrainte, if v is undefined/null, remove constrainte
		if(!i_n) throw new Error("undefined node : "+i_n);
		if(!output_nodes[e_t])output_nodes[e_t]={min:null,max:null};
		if(!v) v = null;
		output_nodes[i_n][sign]=v;
	};
	this.hasLabel = function hasLabel(l){//verify if a node has a specified label : O(1) : double hashtable
		return labels[l]==true;
	};
	this.log = function log(){//log the whole node information O(k) : k=max size(l,v,s)
		console.log('==== ' + id + ' ====');
		console.log('type : '+type);
		console.log('graph : '+graph);
		console.log('labels : '+Object.keys(labels).join(", "));
		console.log('input nodes : ');
		Object.keys(input_nodes).forEach(function(e){console.log(e+" : <="+input_nodes[e].min+" >="+input_nodes[e].max)});
		console.log('output nodes : ');
		Object.keys(output_nodes).forEach(function(e){console.log(e+" : <="+output_nodes[e].min+" >="+output_nodes[e].max)});
		console.log('______________');
	};
	this.saveState = function saveState(){//create a new node witch is a copy of this node : O(k) : k=max size(l,v,s)
		return this.copy(id);
	};
	this.copy = function copy(i){//create a new node witch is a copy of this node with a different id : O(k) : k=max size(l,v,s)
		if(!i) throw new Error("id isn't defined");
		return new Node(i,type,this.getLabels());
	};
}});