/*
An autonomous multi layer graph with optimized modification actions (all in O(1))
 except removal/merge in O(Max(node arity)) and undo redo stack with similar time optimizations
 A layergraph is defined as an oriented graph with clustered nodes.
 relation between node of the same cluster are hierarchicaly ordered using "parent" link,
 interaction between node of different cluster are defined as simple link.
due to this proposition, "parent" become a reserved link name, other link can be typed as wanted
*/
define(["LGEdge.js","LGNode.js","Tools.js"],function(Edge,Node,Tools){return function LayerGraph(){
	var nodes = {};//hashtable of nodes objects, key:id, value:node
	var edges = {};//hashtable of edges objects, key:id, value:edge
	var nodesByLabel = {};//hashtable of nodes, key:label, value :nodes id list
	var nodesByType = {};//hashtable of nodes, key:uid, value: nodes id list
	var edgesBySource={};//hashtable of edges, key:node input id, values: edges id list
	var edgesByTarget={};//hashtable of edges, key:node output id, values:edges id list
	var edgesByType={}//hashable of edges, key:edge type, values: edges id list
	var self=this;
	this.isEmpty = function isEmpty(){
		return Object.keys(nodes)==0;
	};
	this.nodeExist = function nodeExist(id){
		return typeof nodes[id]!='undefined' && nodes[id]!=null;
	};
	this.edgeExist = function edgeExist(id){
		return typeof edges[id]!='undefined' && edges[id]!=null;
	};
	var getNode = function(id){//return a specific node for a specific id
		if(typeof(nodes[id])!=undefined && nodes[id]!=null)
			return nodes[id];
		else return null;
	};
	this.getNodes = function getNodes(){//return the whole nodes as a list of id
		return Object.keys(nodes);
	};
	var getEdge = function(id){//return a specific edge for an id
		if(typeof(edges[id])!=undefined && edges[id]!=null)
			return edges[id];
		else return null;
	};
	this.getEdges = function getEdges(){//return the whole edges as a list of id
		return Object.keys(edges);
	};
	this.addNode = function addNode(id,t,l){//add a new node in the graph
		var delta={enter:{nodes:{},edges:{}},exit:{nodes:{},edges:{}}};
		var tmp_l={};l.forEach(function(e){tmp_l[e]=true;});
		nodes[id]=new Node(id,t,tmp_l);
		if(l)//if this node have some labels, add it to the nodesbylabel hashtable
			l.forEach(function(e){
				if(!nodesByLabel[e]) nodesByLabel[e]={};
				nodesByLabel[e][id]=true;
			});
		if(!nodesByType[t]) nodesByType[t]={};//add the node in the nodesBytype hashtable
		nodesByType[t][id]=true;
		delta.enter.nodes[id]=getNode(id).saveState();//return the delta object
		return delta;
	};
	this.addEdge = function addEdge(id,t,i,o){//add a new edge to the graph
		var delta={enter:{nodes:{},edges:{}},exit:{nodes:{},edges:{}}};
		if(!nodes[i]) throw new Error("this node doesn't exist : "+i);
		if(!nodes[o]) throw new Error("this node doesn't exist : "+o);
		edges[id] = new Edge(id,t,i,o);
		if(!edgesByType[t]) edgesByType[t]={};//add it to the type hashtable
		edgesByType[t][id]=true;
		if(!edgesBySource[i])edgesBySource[i]={};//add it to the source hashtable
		edgesBySource[i][id]=true;
		if(!edgesByTarget[o])edgesByTarget[o]={};//add it to the target hashtable
		edgesByTarget[o][id]=true;
		nodes[i].addOutputNodes(o,t);//update nodes input/ouput table
		nodes[o].addInputNodes(i,t);
		delta.enter.edges[id]=getEdge(id).saveState();
		return delta;
	};
	this.rmNode = function rmNode(n_id){//reove a node from the graph
		if(!nodes[n_id]) throw new Error("this node doesn't exist : "+n_id);
		var delta={enter:{nodes:{},edges:{}},exit:{nodes:{},edges:{}}};
		delta.exit.nodes[n_id]=getNode(n_id).saveState();//save the node for undo redo
		var linked_edges = Tools.Tools.union(this.getEdgeBySource(n_id),this.getEdgeByTarget(n_id));//get all linked edges
		linked_edges.reduce(function(accu,e){
			accu[e]=self.rmEdge(e).exit.edges[e];	//remove all linked edges and save them
		},delta.exit.edges);
		getNode(n_id).getLabels().forEach(function(e){//remove the node from the label hashtable
			delete nodesByLabel[e][n_id];
			if(Object.keys(nodesByLabel[e]).length==0) delete nodesByLabel[e];
		});
		delete nodesByType[getNode(n_id).getType()][n_id];//remove the node from the type hashtable
		if(Object.keys(nodesByType[getNode(n_id).getType()]).length==0)//remove this type if there is no nodes left
			delete nodesByType[getNode(n_id).getType()];
		delete nodes[n_id];//finally remove the node
		return delta;
	};
	this.rmEdge = function rmEdge(e_id){
		if(!edges[e_id]) throw new Error("this edge doesn't exist : "+e_id);
		var delta={enter:{nodes:{},edges:{}},exit:{nodes:{},edges:{}}};
		delta.exit.edges[e_id]=getEdge(e_id).saveState();//save the edge for undo redo
		delete edgesByType[getEdge(e_id).getType()][e_id];//remove the edge from the type hashtable
		if(Object.keys(edgesByType[getEdge(e_id).getType()]).length==0)
			delete edgesByType[getEdge(e_id).getType()];
		delete edgesBySource[getEdge(e_id).getSource()][e_id];//remove the edge from the source hashtable
		if(Object.keys(edgesBySource[getEdge(e_id).getSource()]).length==0)
			delete edgesBySource[getEdge(e_id).getSource()];
		delete edgesByTarget[getEdge(e_id).getTarget()][e_id];//remove the edge from the target hashtable
		if(Object.keys(edgesByTarget[getEdge(e_id).getTarget()]).length==0)
			delete edgesByTarget[getEdge(e_id).getTarget()];
		getNode(getEdge(e_id).getTarget()).rmInputNodes(getEdge(e_id).getSource());//update nodes input/output hashtable
		getNode(getEdge(e_id).getSource()).rmOutputNodes(getEdge(e_id).getTarget());
		delete edges[e_id];//finally remove the edge
		return delta;
	};
	var setTarget =function(e_id,trg){
		getNode(getEdge(e_id).getTarget()).rmInputNodes(getEdge(e_id).getSource());
		getNode(getEdge(e_id).getSource()).rmOutputNodes(getEdge(e_id).getTarget());
		getNode(getEdge(e_id).getSource()).addOutputNodes(trg);
		getNode(trg).addInputNodes(getEdge(e_id).getSource());
		delete edgesByTarget[getEdge(e_id).getTarget()][e_id];
		if(Object.keys(edgesByTarget[getEdge(e_id).getTarget()]).length==0)
			delete edgesByTarget[getEdge(e_id).getTarget()];
		if(!edgesByTarget[trg]) edgesByTarget[trg]={};
			edgesByTarget[trg][e_id]=true;
		getEdge(e_id).setTarget(trg);
	};
	var setSource =function(e_id,src){
		getNode(getEdge(e_id).getSource()).rmOutputNodes(getEdge(e_id).getTarget());
		getNode(getEdge(e_id).getTarget()).rmInputNodes(getEdge(e_id).getSource());
		getNode(getEdge(e_id).getTarget()).addInputNodes(src);
		getNode(src).addOutputNodes(getEdge(e_id).getTarget());
		delete edgesBySource[getEdge(e_id).getSource()][e_id];
		if(Object.keys(edgesBySource[getEdge(e_id).getSource()]).length==0)
			delete edgesBySource[getEdge(e_id).getSource()];
		if(!edgesBySource[src]) edgesBySource[src]={};
			edgesBySource[src][e_id]=true;
		getEdge(e_id).setSource(src);
	};
	var mergeDelta = function(d1,d2){//accumulateur à gauche pour delta
		Object.keys(d2.enter.nodes).forEach(function(e){//merge entering nodes
			if(!d1.enter.nodes[e])d1.enter.nodes[e]=d2.enter.nodes[e];
			else throw new Error("this element has already been defined : "+e);
		});
		Object.keys(d2.enter.edges).forEach(function(e){//merge entering edges
			if(!d1.enter.edges[e])d1.enter.edges[e]=d2.enter.edges[e];
			else throw new Error("this element has already been defined : "+e);
		});
		Object.keys(d2.exit.nodes).forEach(function(e){//merge exiting nodes
			if(!d1.exit.nodes[e])d1.exit.nodes[e]=d2.exit.nodes[e];
			else throw new Error("this element has already been defined : "+e);
		});
		Object.keys(d2.exit.edges).forEach(function(e){//merge exiting edges
			if(!d1.exit.edges[e])d1.exit.edges[e]=d2.exit.edges[e];
			else throw new Error("this element has already been defined : "+e);
		});
	}
	this.mergeNode = function mergeNode(n_id1,n_id2,new_id){//merge two nodes of the same type
		if(!nodes[n_id1]) throw new Error("this node isn't defined : "+n_id1);//check if both node exist
		if(!nodes[n_id2]) throw new Error("this node isn't defined : "+n_id2);
		if(getNode(n_id1).getType()!=getNode(n_id2).getType()) //nodes need to be of the same type
			throw new Error("both nodes have not the same type : "+getNode(n_id1).getType()+" , "+getNode(n_id2).getType());
		var delta={enter:{nodes:{},edges:{}},exit:{nodes:{},edges:{}}};
		if(n_id1==n_id2) return delta;
		delta.enter.nodes=this.addNode(new_id,getNode(n_id1).getType(),Tools.union(getNode(n_id1).getLabels(),getNode(n_id2).getLabels())).enter.nodes;
		var new_id=Object.keys(delta.enter.nodes)[0]; //get the id of the new node
		Tools.union(this.getEdgeBySource(n_id1),this.getEdgeBySource(n_id2)).reduce(function(accu,e){//change the target of all output edges
			accu.exit.edges[e]=getEdge(e).saveState();
			setSource(e,new_id);
			accu.enter.edges[e]=getEdge(e).saveState();
		},delta);
		Tools.union(this.getEdgeByTarget(n_id1),this.getEdgeByTarget(n_id2)).reduce(function(accu,e){//change the source of all input edges
			accu.exit.edges[e]=getEdge(e).saveState();
			setTarget(e,new_id);
			accu.enter.edges[e]=getEdge(e).saveState();
		},delta);
		mergeDelta(delta,this.rmNode(n_id1));//remove both nodes
		mergeDelta(delta,this.rmNode(n_id2));
		return delta;
	}
	this.cloneNode = function cloneNode(n_id){//clone a specific node.
		if(!nodes[n_id]) throw new Error("this node doesn't exist : "+n_id);
		var delta={enter:{nodes:{},edges:{}},exit:{nodes:{},edges:{}}};
		delta=this.addNode(getNode(n_id).getType(),getNode(n_id).getLabels());//add a copy of the node
		var new_id=Object.keys(delta.enter.nodes)[0]; //get the id of the new node
		this.getEdgeBySource(n_id).reduce(function(accu,e){//add all entering edges to the clone
			mergeDelta(accu,self.addEdge(getEdge(e).getType(),new_id,getEdge(e).getTarget()));
		},delta);
		this.getEdgeByTarget(n_id).reduce(function(accu,e){//add all output edges to the clone
			mergeDelta(accu,self.addEdge(getEdge(e).getType(),getEdge(e).getSource(),new_id));
		},delta);
		return delta;
	};
	this.addNodeLabels = function addNodeLabels(n_id,l){//add some labels to a node, return an enter/exit object
		if(!nodes[n_id]) throw new Error("this node doesn't exist : "+n_id);
		var delta={enter:{nodes:{},edges:{}},exit:{nodes:{},edges:{}}};
		if(Tools.intersection(l,getNode(n_id).getLabels()).length==l.length) return delta;
		delta.exit.nodes[n_id]=getNode(n_id).saveState();
		getNode(n_id).addLabels(l);
		delta.enter.nodes[n_id]=getNode(n_id).saveState();
		if(l)//if this node have some labels, add it to the nodesbylabel hashtable
			l.forEach(function(e){
				if(!nodesByLabel[e]) nodesByLabel[e]={};
				nodesByLabel[e][n_id]=true;
			});
		return delta;
	};
	this.rmNodeLabels = function rmNodeLabels(n_id,l){//remove labels from a node if l is null or [], remove all the labels, return an enter/exit object
		if(!nodes[n_id]) throw new Error("this node doesn't exist : "+n_id);
		var delta={enter:{nodes:{},edges:{}},exit:{nodes:{},edges:{}}};
		delta.exit.nodes[n_id]=getNode(n_id).saveState();
		if(l){
			l.forEach(function(e){//remove the node from the label hashtable
				delete nodesByLabel[e][n_id];
			});
		}else{
			getNode(n_id).getLabels().forEach(function(e){//remove the node from the label hashtable
			delete nodesByLabel[e][n_id];
		});
		}
		getNode(n_id).rmLabels(l);
		delta.enter.nodes[n_id]=getNode(n_id).saveState();
		return delta;
	};
	this.setType = function setType(n_id,t){
		if(!nodes[n_id]) throw new Error("this node doesn't exist : "+n_id);
		var delta={enter:{nodes:{},edges:{}},exit:{nodes:{},edges:{}}};
		if(!t) throw new Error("calling setType on "+n_id+" with undefined type");
		if(idT(n_id)=="n"){
			delta.exit.nodes[n_id]=getNode(n_id).saveState();
			getNode(n_id).setType(t);
			delta.enter.nodes[n_id]=getNode(n_id).saveState();
		}else if(idT(n_id)=="e"){
			delta.exit.edges[n_id]=getEdge(n_id).saveState();
			getEdge(n_id).setType(t);
			delta.enter.edges[n_id]=getEdge(n_id).saveState();
		}else throw new Error("Unexpected id : "+n_id);
	};
	this.getNodeByLabels = function getNodeByLabels(labels){//return a nodes id list corresponding to the specific labels
		var nodes_lists = [];
		if(!labels)return nodes_lists;
		labels.reduce(function(accu,e){
			var tmp_lb=nodesByLabel[e]?Object.keys(nodesByLabel[e]):[];
			accu.push(tmp_lb);
		},nodes_lists);
		return Tools.multiIntersection(nodes_lists);
	};
	this.getNodeByType = function getNodeByType(t){//return all nodes of a specific type
		if(!t) return this.getNodes();
		if(!nodesByType[t]) return [];
		return Object.keys(nodesByType[t]);
	}
	this.getEdgeByType = function getEdgeByType(t){//return all edges of a specific type
		if(!edgesByType[t]) return [];
		if(!t) return this.getEdges();
		return Object.keys(edgesByType[t]);
	}
	this.getEdgeBySource = function getEdgeBySource(i_id){//return all the edges corresponding to a specific input (id list)
		if(!i_id) return this.getEdges();
		if(!edgesBySource[i_id]) return [];
		return Object.keys(edgesBySource[i_id]);
	};
	this.getEdgeByTarget = function getEdgeByTarget(o_id){//return all the edges corresponding to a specific output (id list)
		if(!o_id) return this.getEdges();
		if(!edgesByTarget[o_id]) return [];
		return Object.keys(edgesByTarget[o_id]);
	};
	this.log = function log() {//log the whole layer graph object
		var n_keys = Object.keys(nodes);
		var e_keys = Object.keys(edges);
		console.log("NODES : ===================>");
		for (var i = 0; i < n_keys.length; i++)
			nodes[n_keys[i]].log();
		console.log("EDGES : ===================>");
		for (var i = 0; i < e_keys.length; i++)
			edges[e_keys[i]].log();
		console.log("nodesByType : ===================>");
		console.log(nodesByType);
		console.log("nodesByLabel : ===================>");
		console.log(nodesByLabel);
		console.log("edgesByType : ===================>");
		console.log(edgesByType);
		console.log("edgesBySource : ===================>");
		console.log(edgesBySource);
		console.log("edgesByTarget : ===================>");
		console.log(edgesByTarget);
	};
	this.getLabels = function getLabels(id){//return the labels of a node
        if(!getNode(id)) throw new Error("unexisting node : "+id);
		return getNode(id).getLabels();
    };
    this.getType = function getType(id){//return the type of a node or an edge
        if(!id)
			return {nodes:Object.keys(nodesByType),edges:Object.keys(edgesByType)};
		if(idT(id)=='e'){
			if(!getEdge(id)) throw new Error("unexisting node : "+id);
            return getEdge(id).getType();
        }else{
			if(!getNode(id)) throw new Error("unexisting node : "+id);
            return getNode(id).getType();
		}
    };
    this.getOutputNodes = function getOutputNodes(id,e_t){//return al the nodes from an input edge (or a specific type of edges)
        if(!getNode(id)) throw new Error("unexisting node : "+id);
		return getNode(id).getOutputNodes(e_t);
    };
    this.getInputNodes = function getInputNodes(id,e_t){//return al the nodes from an output edge (or a specific type of edges)
        if(!getNode(id)) throw new Error("unexisting node : "+id);
		return getNode(id).getInputNodes(e_t);
    };
    this.getSource = function getSource(id){//return the source of an edge
        if(!getEdge(id)) throw new Error("unexisting node : "+id);
		return getEdge(id).getSource();
    };
    this.getTarget = function getTarget(id){//return the target of an edge
        if(!getEdge(id)) throw new Error("unexisting node : "+id);
		return getEdge(id).getTarget();
    };
    this.getLastNodeId = function getLastNodeId(){//return the id of the last node created
        return 'n_'+(NODE_ID-1);
    };
    this.getLastEdgeId = function getLastEdgeId(){//return the id of the last edge created
        return 'e_'+(EDGE_ID-1);
    };
	this.hasLabel = function hasLabel(id,l){
		if(!getNode(id)) throw new Error("unexisting node : "+id);
		return getNode(id).hasLabel(l);
	};
	this.hasInputNode = function hasInputNode(id,n,e_t){
		if(!getNode(id)) throw new Error("unexisting node : "+id);
		return getNode(id).hasInputNode(n,e_t);
	};
	this.hasOutputNode = function hasOutputNode(id,n,e_t){
		if(!getNode(id)) throw new Error("unexisting node : "+id);
		return getNode(id).hasOutputNode(n,e_t);
	};
	this.saveState = function saveState(){
		var ret=new LayerGraph();
		Object.keys(nodes).forEach(function(e){
			ret.addNode(getNode(e).getType(),getNode(e).getLabel());
		});
		Object.keys(edges).forEach(function(e){
			ret.addEdge(getEdge(e).getType(),getEdge(e).getSource(),getEdge(e).getTarget());
		});
		return ret;
	};
	this.searchPattern = function searchPattern(pattern){//search a specific patern in the graph
		if(pattern.isEmpty()){
			console.error("Empty pattern !");
			return [];
		}
		var potential=[];
		var p_nodes=pattern.getNodes();
		this.getNodesByType(p_nodes[0]).forEach(function(e){potential.push({nodes:{e:true},edges:{}})});
		var t_node=p_nodes.splice(0,1);
		while(p_nodes.length>0){
			var srcs=pattern.getEdgeBySource(t_node);
			var trgs=pattern.getEdgeByTarget(t_node);
			for(var i=potential.lenght-1;i>=0;i--){
				var correctEdges=0;
			}
		}
		return potential;
	};
}