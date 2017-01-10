/* Load the configuration menu
 * add the configuration menu to the top menu (gear on top right).
 * @ Author Adrien Basso blandin
 * This module is part of regraphGui project
 * this project is under AGPL Licence
*/
define([
	"ressources/d3/d3.js",
	"ressources/requestFactory.js"
	],
	function(d3,Rfactory){
	
	return function(container,dispatch,srv){
		// d3.select("#"+container).append("div")//add a gear button
		// 	.classed("config_icon",true)
		// 	.on("click",configShow)
		// 	.html("&#x2699;")
		// 	.classed("unselectable",true);
		//var config_container;
		var hieShape ={};
		var server_url="";
		this.init = function init(){
			hieShape = {};
			server_url=srv;
			// config_container=d3.select("body").append("div")
			// 	.attr("id","config_menu")
			// 	.property("disabled",true)
			// 	.style("display","none");
			// config_container.append("div")
			// 	.classed("close_side_menu",true)
			// 	.on("click",configShow)
			// 	.html("&#x274c;")
			// 	.classed("unselectable",true);//add a close button
		}
		this.update = function update(graph_name){
			//delete hieShape[graph_name];
			Rfactory.getConfig(graph_name,configDisplay(ret));
		}
		function configDisplay(req){
			//hieShape[req.name]=
			
		}
		this.loadGraphConf = function loadGraphConf(graph_name){
			console.log(graph_name);
		};
		function configShow(){
			if(config_container.property("disabled")){
				config_container.property("disabled",false)
					.style("display","initial");
			}else{
				config_container.property("disabled",true)
					.style("display","none");
			}
		}
	};
});