define(["ressources/d3/d3.js","ressources/converter.js","ressources/requestFactory.js"],function(d3,converter,rqFactory){
	return function InputFileReader(container_id,dispatch,server_url){
		if(!server_url) throw new Error("server url undefined");
		var srv_url = server_url;//the current url of the server
		var disp = dispatch;//global dispatcher for events
		var container = d3.select("#"+container_id).append("div").attr("id","mod_menu").classed("mod_menu",true);
		var selector;
		(function init(){
			container.append("div")
				.attr("id","export")
				.classed("mod_el",true)
				.classed("mod_div",true)
				.on("click",exportFile)
				.html("Export")
				.classed("unselectable",true);
			container.append("input")
				.classed("mod_el",true)
				.attr("type","file")
				.attr("id","import_f")
				.property("multiple",true);
			selector=container.append("select")
				.attr("id","file_type")
				.classed("mod_el",true);
			selector.selectAll("option")
				.data(["Hierarchy","Graph","Rule"])
				.enter()
				.append("option")
					.text(function(d){return d})
					.attr("selected",function(d,i){return i==0});
			container.append("div")
				.classed("mod_el",true)
				.classed("mod_div",true)
				.on("click",importFile)
				.html("Import")
				.classed("unselectable",true);	
		}());
		function importFile(){
			var file=document.getElementById("import_f").files;
			if(typeof(file)!="undefined" && file !=null && file.length>0){
				for(var i=0;i<file.length;i++){
					loadFile(file[i]);
				}
			}else alert("No input file.");
		};
		function exportFile(){
			dispatch.call("graphExprt",this,null);
		};
		function loadFile(data){
			var ka = new FileReader();
			ka.readAsDataURL(data);
			ka.onloadend = function(e){
				var si   = selector.property('selectedIndex'),
				s    = selector.selectAll("option").filter(function (d, i) { return i === si }),
				type = s.datum();
				if(data.name.split(".")[1]=="json")
					converter.kamiToRegraph(e.target.result,dispatch,type);
				else if(file.name.split(".")[1]=="coord")
					converter.loadCoord(e.target.result,main_graph);
			}
			
		};
	}
});