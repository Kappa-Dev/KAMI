define(["ressources/LayerGraph.js"],function(Graph){ return {
	rootGraph:function(){
		var g = new Graph();
		g.addNode("_node","_node");
		g.addEdge("_edge","_node","_node");
		//g.log();
		return g;
	}
}});