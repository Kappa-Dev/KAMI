define([],function(){return function Edge(ii,t,i,o){//generic definition of an edge in a hierarchical graph
	if(!ii) throw new Error("undefined id : "+ii);
	var id=ii;
	if(!t) throw new Error("unknown type : "+t);
	var type=t;
	if(!i)throw new Error("undefined source : "+i);
	var source=i;//for parenting : source is the son
	if(!o)throw new Error("undefined target : "+o);
	var target=o;
	this.getId = function getId(){//return the edge id O(1)
		return id;
	};
	this.getType = function getType(){//return the edge type (new array) : O(t) : t=type size : constant
		return type.concat();
	};
	this.setType = function setType(t){//change the edge type
		if(!t) throw new Error("Undefined type");
		type=t;
	}
	this.getSource = function getSource(){//return the edge source : O(1)
		return source;
	};
	this.getTarget = function getTarget(){//return the edge target : O(1)
		return target;
	};
	this.setSource = function setSource(i) {//change the edge source : O(1)
		if(!i) throw new Error("id isn't defined");
		source=i;
	};
	this.setTarget = function setTarget(o){//change the edge target : O(1)
		if(!o) throw new Error("id isn't defined");
		target=o;
	};
	this.log = function log(){//log the whole edge informations O(1)
		console.log('==== ' + id + ' ====');
		console.log('type : '+type);
		console.log('source : '+source);
		console.log('target : '+target);
		console.log('______________');
	};
	this.saveState = function saveState(){//create a exact copy of the edge : O(1)
		return this.copy(id);
	};
	this.copy = function copy(i){//create a copy of the edge with a new id : O(1)
		return new Edge(i,type,source,target);
	};
}});