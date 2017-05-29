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

		// var container = d3.select("#"+container_id)
		// 	.append("div")
		// 	.attr("id","mod_menu")
		// 	.classed("mod_menu",true);

		// d3.select("#" + container_id)
		// 	.append("div")
		// 	.attr("id", "exportInput")
		// 	.classed("menuInput", true)
		// 	.style("display", "none");

		var selector;//object type selector
		/* initialize all the HTML objects
		 * this function is self called at instanciation
		 */
		(function init(){
			var container = d3.select("#" + container_id)
				.append("div")
				.attr("id", "test_menu")
				.html(`
					 <nav class="navbar navbar-default" id="myNavBar" role="navigation">
            <!-- Brand and toggle get grouped for better mobile display -->
            <div class="navbar-header custom-header">
               <button type="button" class="navbar-toggle" id="navbarButton" data-toggle="collapse" data-target="#hamMenu1">
			   <div class="menubtn">
               <span class="sr-only">Toggle navigation</span>
               <span class="icon-bar"></span>
               <span class="icon-bar"></span>
               <span class="icon-bar"></span>
			   </div>
               </button>
               <button type="button" class="navbar-toggle"  id="newGraphBtn"><i class="newGraph-icon"></i></button>
               <a class="navbar-brand" href="#"></a>
            </div>
            <!-- Collect the nav links, forms, and other content for toggling -->
            <div class="collapse navbar-collapse custom-menu" id="hamMenu1">
               <ul class="nav navbar-nav navbar-right">
                  <li class="dropdown">
                     <a href="#" class="dropdown-toggle" data-toggle="dropdown">Import <b class="caret"></b></a>
                     <ul class="dropdown-menu" style="padding: 15px;min-width: 250px;">
                        <li>
                           <div class="row">
                              <div class="col-md-12">
                                 <form class="form" role="form" method="" action="" accept-charset="UTF-8" id="form-import">
                                    <div class="form-group">
                                       <input type="text" class="form-control" id="graphPathInput" placeholder="" required="true">
                                    </div>
                                    <div class="checkbox">
                                       <label>
                                       <input type="checkbox" id="mergeCheckBox"> Indra 
                                       </label>
                                    </div>
                                    <div class="checkbox">
                                       <label>
                                       <input type="checkbox" id="OldFormatCheckBox"> Old format
                                       </label>
                                    </div>
                                    <div class="form-group">
                                      <input type="file" class="form-control inputfile" id="ImportfileInput" placeholder="" required="true">
									  <label for="ImportfileInput" class="btn btn-success btn-block">Import</label>
                                    </div>
                                 </form>
                              </div>
                           </div>
                        </li>
                     </ul>
                  </li>
				  <li class="divider"></li>
                  <li class="dropdown">
                     <a href="#" class="dropdown-toggle" data-toggle="dropdown">Export <b class="caret"></b></a>
                     <ul class="dropdown-menu" style="padding: 15px;min-width: 250px;">
                        <li>
                           <div class="row">
                              <div class="col-md-12">
                                 <form class="form" role="form" method="" action="" accept-charset="UTF-8" id="form-export">
                                    <div class="form-group">
                                       <label class="sr-only" for="exampleInputEmail2">Email address</label>
                                       <input type="text" class="form-control" id="graphPathInput-export" placeholder="" required="true">
                                    </div>
                                    <div class="form-group">
                                       <button type="submit" class="btn btn-success btn-block">Export</button>
                                    </div>
                                 </form>
                              </div>
                           </div>
                        </li>
                     </ul>
                  </li>
               </ul>
            </div>
            <!-- /.navbar-collapse -->
         </nav>
					 `);


            container.selectAll(".dropdown-menu")
			         .on("click",function(){d3.event.stopPropagation()});


            d3.select("#ImportfileInput")
			  .on("change",importFile2);

            d3.select("#form-export")
			  .on("submit",exportFile2);

			d3.select("#newGraphBtn")
			  .on("click",() => disp.call("addGraphFileLoader",this));


            container.append("a")
                .attr("id","json_link")
                .attr("download","model.ka")
                .attr("href","#");
            container.append("a")
                .attr("id","json_hierarchy_link")
                .attr("download","hierarchy.json")
                .attr("href","#");



			// container.append("div")//add the export button
			// 	.attr("id","export")
			// 	.classed("mod_el",true)
			// 	.classed("mod_div",true)
			// 	.on("click",exportFile)
			// 	.html("Export")
			// 	.classed("unselectable",true);
			// container.append("input")//add the file input
			// 	.classed("mod_el",true)
			// 	.attr("type","file")
			// 	.attr("id","import_f")
			// 	.property("multiple",true);
			// selector=container.append("select")//add the selector
			// 	.attr("id","file_type")
			// 	.classed("mod_el",true);
			// selector.selectAll("option")
			// 	.data(["Hierarchy","Graph","Rule","Snip"])
			// 	.enter()
			// 	.append("option")
			// 		.text(function(d){return d})
			// 		.attr("selected",function(d,i){return i==0});
			// container.append("div")//add the inport button
			// 	.classed("mod_el",true)
			// 	.classed("mod_div",true)
			// 	.on("click",importFile)
			// 	.html("Import")
			// 	.classed("unselectable",true);


			// container.append("div")//add the new graph button
			// 	.attr("id","add")
			// 	.classed("mod_el",true)
			// 	.classed("mod_div",true)
			// 	.on("click",addThing)
			// 	.html("New graph")
			// 	.classed("unselectable",true);




			// container.append("div")//add the to Kappa button
			// 	.attr("id","kappa")
			// 	.classed("mod_el",true)
			// 	.classed("mod_div",true)
			// 	.html("To Kappa")
			// 	.classed("unselectable",true)
			// 	.on("click",toKappa);
		}());


		function afterImport(err, ret) {
			if (!err) {
				dispatch.call("hieUpdate", this, null);
			}
			else console.error(err);
		};

		function importFile2() {
			let input_files = d3.select("#ImportfileInput").node().files;
			let merge = d3.select("#mergeCheckBox").property("checked");
			let oldFormat = d3.select("#OldFormatCheckBox").property("checked");
			let top_graph = d3.select("#graphPathInput").property("value");
			if (top_graph === "" && !oldFormat) { alert("the new hierarchy position is empty"); return 0; }
			if (input_files.length > 0) {
				let file = input_files[0];
				let ka = new FileReader();
				ka.onloadend = function (e) {
					if (oldFormat) {
						converter.kamiToRegraph(e.target.result, dispatch, "Graph");
					}
					else {
						d3.json(e.target.result, function (rep) {
							if (merge) {
								request.mergeHierarchy2(
									top_graph,
									JSON.stringify(rep, null, "\t"),
									afterImport);
							}
							else {
								request.mergeHierarchy(
									top_graph,
									JSON.stringify(rep, null, "\t"),
									afterImport);
								// request.addHierarchy(
								// 	top_graph,
								// 	JSON.stringify(rep, null, "\t"),
								// 	afterImport);
							}

						})
					}
				};
				ka.readAsDataURL(file);
			}

		}
		/* Import all the files from the input file 
		 */
		function importFile() {
			var file = document.getElementById("import_f").files;
			if (typeof (file) != "undefined" && file != null && file.length > 0) {
				for (var i = 0; i < file.length; i++) {
					loadFile(file[i]);
				}
			} else alert("No input file.");
		};
		/* export the require object : graph, rule or hierarchy
		 * @call : graphExprt event with the type of the selector
		 */
		function exportFile() {
			var si = selector.property('selectedIndex'),
				s = selector.selectAll("option").filter(function (d, i) { return i === si }),
				type = s.datum();
			disp.call("graphExprt", this, type);
		};

		function exportFile2() {
			d3.event.preventDefault();
			let graphPath = d3.select("#graphPathInput-export")
				.property("value");
			request.getHierarchyWithGraphs(
				graphPath,
				function (err, ret) {
					converter.downloadGraph(ret);
				}
			);


		};
		/* Load a file from user hard-drive
		 * this file can be a .json or a .coord file for configuration purpose
		 * this file will be parsed depending of its content to fit the regraph structure.
		 * @input : data : the file path
		 */
		function loadFile(data) {
			var ka = new FileReader();
			ka.readAsDataURL(data);
			ka.onloadend = function (e) {
				var si = selector.property('selectedIndex'),
					s = selector.selectAll("option").filter(function (d, i) { return i === si }),
					type = s.datum();
				// if(data.name.split(".")[1]=="json"){
				if (data.name.split(".")[1] == "coord")
					converter.loadCoord(e.target.result, main_graph);
				else if (type == "Snip")
					converter.snipToRegraph(e.target.result, dispatch, "Hierarchy");
				else
					converter.kamiToRegraph(e.target.result, dispatch, type);
				// }
			}

		};
		}
	});
