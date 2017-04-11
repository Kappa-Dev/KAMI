define([
    "ressources/d3/d3.js"
],
    function (d3) {

        //Interface allowing to define relations between nodes of different graphs
        return function kappaExporter(fatherElem, modalId, dispatch, request) {
            let nuggets = []
            let selected_nuggets = []
            let compos = {}
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
                        <div class="modal-body row">
                            <div class="col col-sm-10">
                                <div class="row" id="unselected_parts">
                                    <div class="col col-sm-6">
                                        <h4>Nuggets</h4>
                                        <div id="expNugList" class="partList"></div>
                                    </div>
                                    <div class="col col-sm-6">
                                        <h4>Compositions</h4>
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
                            <button id="saveModel" type="button" class="btn btn-default">Save Model</button>
                            <button id="getKappaButton" type="button" class="btn btn-default">Get Kappa</button>
                        </div>
                    </div>
                `);

            modal.select("#getKappaButton")
              .on("click", toKappa);


            // d3.select("#saveButton")
            //     .on("click", function () {
            //         let new_formula = d3.select("#formulaTextArea")
            //             .property("value");
            //         formulae_data[active_formula]["formula"] = new_formula;
            //         let callback = function (err, _ret) {
            //             if (err) { console.log(err) }
            //             else {
            //                 d3.selectAll(".hide-if-modified")
            //                     .style("display", "inline");
            //                 d3.selectAll(".show-if-modified")
            //                     .style("display", "none");
            //                 active_modified = false;
            //                 d3.select("#formulaeList")
            //                     .selectAll("a")
            //                     .on("click", formulaClickHandler)
            //                     .classed("disabled", false);
            //             }
            //         }
            //         request.addAttr(graph_path + "/", JSON.stringify({ formulae: formulae_data }), callback)
            //     });


            // function drawFormulae() {
            //     d3.select("#formulaeList")
            //         .selectAll("a")
            //         .remove();
            //     let list = d3.select("#formulaeList")
            //         .selectAll("a")
            //         .data(formulae_data);
            //     list.enter()
            //         .append("a")
            //         .classed("list-group-item", true)
            //         .classed("active", (d, i) => i === active_formula)
            //         .on("click", formulaClickHandler)
            //         .text(function (d, _i) { return d.id })
            //         .append("span")
            //         //.insert("span",":first-child")
            //         .classed("glyphicon", true)
            //         .classed("pull-right", true)
            //         .classed("glyphicon-trash", true)
            //         .on("click", deleteFormula);

            //     if (active_formula !== -1) {
            //         d3.select("#formulaTextArea")
            //             .property("value", formulae_data[active_formula].formula);
            //     }
            //     else {
            //         d3.select("#formulaTextArea")
            //             .property("value", "");
            //     }
            //     // list.exit()
            //     //     .remove();

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

                d3.selectAll("#selected_parts, #expNugList, #expCompList")
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

            this.update = function update(path, parts) {
                graph_path = path;
                nuggets = parts.nuggets
                selected_nuggets = []
                compos = {}
                if ("compositions" in parts) {
                    parts.compositions.forEach(
                        comp => { compos[comp.id] = { "selected": false } })
                }
                // parts.compositions.forEach(comp => compos[comp] = { "selected": false });
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

        }
    });
	