/* This module add the "modification" menu to the UI
 * This module add a div containing the export, import and new graph button
 * this module add the file type selector and file input
 * this module trigger addGraph and graphExprt event
 * @ Author Adrien Basso blandin
 * This module is part of regraphGui project
 * this project is under AGPL Licence
*/
define([
	"ressources/d3/d3.js",
	"ressources/converter.js",
	"ressources/requestFactory.js"
	],
	function(d3,converter,rqFactory){
	/* Create a new inputFile module
	 * @input : container_id : the container to bind this hierarchy
	 * @input : dispatch : the dispatch event object
	 * @input : server_url : the regraph server url
	 * @return : a new InputFileReader object
	 */
	return function InputFileReader(container_id,dispatch,server_url){
		if(!server_url) throw new Error("server url undefined");
		var srv_url = server_url;//the current url of the server
        var request = new rqFactory(server_url);
		var disp = dispatch;//global dispatcher for events
		var container = d3.select("#"+container_id)
			.append("div")
			.attr("id","mod_menu")
			.classed("mod_menu",true);
		var selector;//object type selector
		/* initialize all the HTML objects
		 * this function is self called at instanciation
		 */
		(function init(){
			container.append("div")//add the export button
				.attr("id","export")
				.classed("mod_el",true)
				.classed("mod_div",true)
				.on("click",exportFile)
				.html("Export")
				.classed("unselectable",true);
			container.append("input")//add the file input
				.classed("mod_el",true)
				.attr("type","file")
				.attr("id","import_f")
				.property("multiple",true);
			selector=container.append("select")//add the selector
				.attr("id","file_type")
				.classed("mod_el",true);
			selector.selectAll("option")
				.data(["Hierarchy","Graph","Rule","Snip"])
				.enter()
				.append("option")
					.text(function(d){return d})
					.attr("selected",function(d,i){return i==0});
			container.append("div")//add the inport button
				.classed("mod_el",true)
				.classed("mod_div",true)
				.on("click",importFile)
				.html("Import")
				.classed("unselectable",true);
			container.append("div")//add the new graph button
				.attr("id","add")
				.classed("mod_el",true)
				.classed("mod_div",true)
				.on("click",addThing)
				.html("New graph")
				.classed("unselectable",true);
            container.append("a")
                .attr("id","json_link")
                .attr("download","model.kappa")
                .attr("href","#");
			// container.append("div")//add the to Kappa button
			// 	.attr("id","kappa")
			// 	.classed("mod_el",true)
			// 	.classed("mod_div",true)
			// 	.html("To Kappa")
			// 	.classed("unselectable",true)
			// 	.on("click",toKappa);
		}());
		/* Add a new object to the current hierarchy
		 * this object depends of the selector : Graph, Rule or hierarchy
		 * @call : this function trigger addGraph event with the type of the selector
		 */
		function addThing(){
			var si   = selector.property('selectedIndex'),
				s    = selector.selectAll("option").filter(function (d, i) { return i === si }),
				type = s.datum();
			disp.call("addGraph",this,type);
		}
		/* Import all the files from the input file 
		 */
		function importFile(){
			var file=document.getElementById("import_f").files;
			if(typeof(file)!="undefined" && file !=null && file.length>0){
				for(var i=0;i<file.length;i++){
					loadFile(file[i]);
				}
			}else alert("No input file.");
		};
		/* export the require object : graph, rule or hierarchy
		 * @call : graphExprt event with the type of the selector
		 */
		function exportFile(){
			var si   = selector.property('selectedIndex'),
				s    = selector.selectAll("option").filter(function (d, i) { return i === si }),
				type = s.datum();
			disp.call("graphExprt",this,type);
		};
		/* Load a file from user hard-drive
		 * this file can be a .json or a .coord file for configuration purpose
		 * this file will be parsed depending of its content to fit the regraph structure.
		 * @input : data : the file path
		 */
		function loadFile(data){
			var ka = new FileReader();
			ka.readAsDataURL(data);
			ka.onloadend = function(e){
				var si   = selector.property('selectedIndex'),
				s    = selector.selectAll("option").filter(function (d, i) { return i === si }),
				type = s.datum();
				if(data.name.split(".")[1]=="json"){
					if(type == "Snip")
						converter.snipToRegraph(e.target.result,dispatch,"Hierarchy");
					else
						converter.kamiToRegraph(e.target.result,dispatch,type);
				}
				else if(file.name.split(".")[1]=="coord")
					converter.loadCoord(e.target.result,main_graph);
			}
			
		};
	}
});
