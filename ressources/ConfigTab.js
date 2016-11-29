/* Load the configuration menu
 * add the configuration menu to the top menu (gear on top right).
 * @ Author Adrien Basso blandin
 * This module is part of regraphGui project
 * this project is under AGPL Licence
*/
define([
	"ressources/d3/d3.js"
	],
	function(d3){
	
	return function(container,dispatch){
		var config_container = d3.select("#"+container).append("div")//add a gear button
			.classed("config_icon",true)
			.on("click",configShow)
			.html("&#x2699;")
			.classed("unselectable",true);
		var hieShape ={};
		var server_url="";
		this.init = function init(){
			hieShape = {};
			server_url="https://api.executableknowledge.org/iregraph";
		}
		this.update = function update(graph_name){
			delete hieShape[graph_name];
		}
		function configShow(){
			//d3.select("body").append("div")
				//.attr("id","config_menu");
		}
	};
});