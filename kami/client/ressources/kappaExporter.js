define([
    "ressources/d3/d3.js"
],
    function (d3) {

        //Interface allowing to define relations between nodes of different graphs
        return function kappaExporter(fatherElem, modalId, dispatch, request) {
            let nuggets = [];
            let savedModels = {};
            let selected_nuggets = [];
            let compos = {};
            let graph_path = "";
            let modal = fatherElem
                .append("div")
                // .insert("div",":first-child")
                .attr("id", modalId)
                .classed("modal", true)
                .classed("fade", true)
                .classed("row", true)
                .html(`
                    <div class="modal-content">
                        <div class="modal-header">
                            <button type="button" class="close hide-if-modified" data-dismiss="modal">&times;</button>
                            <h4 class="modal-title">Kappa Generator</h4>
                        </div>
                        <div id="exporterBody" class="modal-body row">
                            <div class="col col-sm-10">
                                <div class="row" id="unselected_parts">
                                    <div class="col col-sm-6">
                                        <h4>Nuggets</h4>
                                        <div id="expNugList" class="partList"></div>
                                    </div>
                                    <div class="col col-sm-6">
                                        <h4>Hypotheses</h4>
                                        <div id="expCompList" class="partList"></div>
                                    </div>
                                </div>
                                <h4>Selected</h4>
                                <div id="selected_parts"></div>
                            </div>
                            <div class="col col-sm-2">
                                <h4>Models</h4>
                                <div id="existing_models"></div>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button id="selectAll" type="button" class="btn btn-default">Select All</button>
                            <button id="deselectAll" type="button" class="btn btn-default">Deselect All</button>
                            <button id="saveModel" type="button" class="btn btn-default">Save Model</button>
                            <button id="getKappaButton" type="button" class="btn btn-default">Get Kappa</button>
                        </div>
                    </div>
                `);

            modal.select("#getKappaButton")
              .on("click", toKappa);

            modal.select("#saveModel")
              .on("click", saveModel);

            modal.select("#deselectAll")
              .on("click", deselectAll);

            modal.select("#selectAll")
              .on("click", selectAll);


            function drawKappaExporter() {

                let [selectedCompos, unselectedCompos] = Object.keys(compos).reduce(
                    function (acc, compo) {
                        if (compos[compo]["selected"]) {
                            acc[0].push(compo);
                        }
                        else {
                            acc[1].push(compo);
                        }
                        return acc;
                    }, [[], []]);
                
                d3.select("#expNugList")
                    .selectAll("a")
                    .remove();
                let list = d3.select("#expNugList")
                    .selectAll("a")
                    .data(nuggets);
                list.enter()
                    .append("a")
                    .classed("btn btn-default", true)
                    .on("click", selectNug)
                    .text(function (d, _i) { return d + "\xa0" })
                    .append("span")
                    .classed("glyphicon", true)
                    .classed("pull-right", true)
                    .classed("glyphicon-eye-open", true)
                    .on("click", () => console.log("view"));


                d3.select("#expCompList")
                    .selectAll("a")
                    .remove();
                list = d3.select("#expCompList")
                    .selectAll("a")
                    .data(unselectedCompos);
                list.enter()
                    .append("a")
                    .classed("btn btn-primary", true)
                    .on("click", selectComp)
                    .text(function (d, _i) { return d + "\xa0" })
                    .append("span")
                    .classed("glyphicon", true)
                    .classed("pull-right", true)
                    .classed("glyphicon-eye-open", true)
                    .on("click", () => console.log("view"));


                d3.select("#selected_parts")
                    .selectAll("a")
                    .remove();
                let selected_list = d3.select("#selected_parts")
                    .selectAll("a")
                    .data(selected_nuggets);
                selected_list.enter()
                    .append("a")
                    .classed("btn btn-default", true)
                    .on("click", unselectNug)
                    .text(function (d, _i) { return d + "\xa0" })
                    .append("span")
                    .classed("glyphicon", true)
                    .classed("pull-right", true)
                    .classed("glyphicon-eye-open", true)
                    .on("click", () => console.log("view"));
                let all_selected = d3.select("#selected_parts").selectAll("a");
                all_selected = all_selected.data(selected_nuggets.concat(selectedCompos));
                all_selected.enter()
                    .append("a")
                    .classed("btn btn-primary", true)
                    .on("click", unselectCompos)
                    .text(function (d, _i) { return d + "\xa0" })
                    .append("span")
                    .classed("glyphicon", true)
                    .classed("pull-right", true)
                    .classed("glyphicon-eye-open", true)
                    .on("click", () => console.log("view"));
                
                d3.select("#existing_models")
                  .selectAll("a")
                  .remove();

                let models_list = d3.select("#existing_models")
                  .selectAll("a")
                  .data(savedModels);
                models_list.enter()
                    .append("a")  
                    .classed("btn btn-default", true)
                    .on("click", addModel)
                    .text(function (d, _i) { return d["name"] + "\xa0" })
                    .append("span")
                    //.insert("span",":first-child")
                    .classed("glyphicon", true)
                    .classed("pull-right", true)
                    .classed("glyphicon-trash", true)
                    .on("click", deleteModel);

                d3.selectAll("#selected_parts, #expNugList, #expCompList, #existing_models")
                    .selectAll("a")
                    .classed("kappaPart", true);
            }

            function selectNug(d, i) {
                nuggets.splice(i, 1);
                selected_nuggets.push(d);
                drawKappaExporter();
            }
            function selectComp(d, _i) {
                compos[d]["selected"] = true;
                drawKappaExporter();
            }
            function unselectNug(d, i) {
                selected_nuggets.splice(i, 1);
                nuggets.push(d);
                drawKappaExporter();
            }
            function unselectCompos(d, _i) {
                compos[d]["selected"] = false;
                drawKappaExporter();
            }

            this.update = function update(path, parts, selected) {
                graph_path = path;
                nuggets = parts.nuggets;
                savedModels = Object.keys(parts.savedModels).reduce(
                    function (acc, key) {
                        parts.savedModels[key]
                        acc.push({"name": key, "nuggets": parts.savedModels[key]["nuggets"]})
                        return acc;
                    }, []);
                if (selected !== undefined){
                    selected_nuggets = selected;
                    nuggets = nuggets.filter(nug => selected.indexOf(nug) === -1);
                }
                else{
                selected_nuggets = [];
                }

                compos = {};
                parts.compositions.forEach(
                    comp => { compos[comp.id] = { "selected": false } })
                drawKappaExporter();
                d3.selectAll(".hide-if-modified")
                    .style("display", "inline");
                d3.selectAll(".show-if-modified")
                    .style("display", "none");
            };

            function toKappa() {
                var callback = function (error, response) {
                    d3.select("body")
                        .style("cursor", "default");
                    if (error) {
                        alert(error.currentTarget.response);
                        return false;
                    }
                    d3.select("#json_link")
                        .attr("href",
                        'data:text/json;charset=utf-8,'
                        + encodeURIComponent(JSON.parse(response.response)["kappa_code"]));
                    document.getElementById('json_link').click();
                };
                let path = graph_path
                path = (path == "//") ? "/" : path
                d3.select("body")
                    .style("cursor", "progress");
                let compositionList = Object.keys(compos).reduce(
                    function (acc, compo) {
                        if (compos[compo]["selected"]) {
                            acc.push(compo);
                        }
                        return acc;
                    }, []);

                request.getKappa(path, JSON.stringify({
                    "names": selected_nuggets,
                    "compositions": compositionList}), callback)
                return false;
            }
            
            function saveModel(){
                let name = prompt("Model name:");
                if (!name){return false;}
                if (Object.keys(savedModels).findIndex(m => savedModels[m].name === name) !== -1){
                    if (!confirm(`Overwrite model ${name} ?`)){
                        return false
                    }
                }
                let compositionList = Object.keys(compos).reduce(
                    function (acc, compo) {
                        if (compos[compo]["selected"]) {
                            acc.push(compo);
                        }
                        return acc;
                    }, []);

                request.promSaveModel(graph_path, JSON.stringify({
                    "names": selected_nuggets,
                    "compositions": compositionList,
                    "modelName": name
                }))
                    .then(()=> dispatch.call("loadKappaExporter", this, graph_path, selected_nuggets));
                return false;
            }

            function addModel(d, _i){
                d.nuggets.forEach(nugName => {
                    let index =  nuggets.indexOf(nugName);
                    if (index > -1){
                        nuggets.splice(index, 1);
                    }
                    index = selected_nuggets.indexOf(nugName);
                    if (index === -1){
                        selected_nuggets.push(nugName);
                    }
                });
                drawKappaExporter();
            }

            function deselectAll(){
                nuggets = nuggets.concat(selected_nuggets);
                selected_nuggets = [];
                drawKappaExporter();
            }

            function selectAll(){
                selected_nuggets = nuggets.concat(selected_nuggets);
                nuggets = [];
                drawKappaExporter();
            }
            
            function deleteModel(d, _i){
                d3.event.stopPropagation();
                request.promRemoveModel(graph_path, d.name)
                .then(()=> dispatch.call("loadKappaExporter", this, graph_path, selected_nuggets));
            }
        }
    });
    