define([
    "ressources/d3/d3.js"
],
    function (d3) {

        //Interface allowing to define relations between nodes of different graphs
        return function formulaEditor(fatherElem, modalId, dispatch, request) {
            let formulae_data = [];
            let graph_path = "";
            let active_formula = -1;
            let old_active = -1;
            let active_modified = false;
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
                            <h4 class="modal-title">Graph formulas</h4>
                        </div>
                        <div class="modal-body row">
                            <div class="col-sm-3"><div id="formulaeList" class="list-group"></div></div>
                            <div class="col-sm-9"><textarea id="formulaTextArea" rows="3"></textarea></div>
                        </div>
                        <div class="modal-footer">
                            <button id="saveButton" type="button" class="show-if-modified btn btn-default">Save</button>
                            <button id="cancelButton" type="button" class="show-if-modified btn btn-default">Cancel</button>
                            <button id="newFormulaButton" type="button" class="hide-if-modified btn btn-default">New formula</button>
                            <button type="button" class="hide-if-modified btn btn-default" data-dismiss="modal">Close</button>
                        </div>
                    </div>
                `);

            d3.select("#newFormulaButton")
              .on("click", addFormula);

            d3.select("#formulaTextArea")  
              .on("input", function(){
                    if (!active_modified && active_formula !== -1) {
                        active_modified = true;
                        d3.selectAll(".hide-if-modified")
                            .style("display", "none");
                        d3.selectAll(".show-if-modified")
                            .style("display", "inline");
                        d3.select("#formulaeList")
                            .selectAll("a")
                            .on("click", null)
                            .classed("disabled", true);

                    }
                });

            d3.select("#saveButton")
                .on("click", function () {
                    let new_formula = d3.select("#formulaTextArea")
                        .property("value");
                    formulae_data[active_formula]["formula"] = new_formula;
                    let callback = function (err, _ret) {
                        if (err) { console.log(err) }
                        else {
                            d3.selectAll(".hide-if-modified")
                                .style("display", "inline");
                            d3.selectAll(".show-if-modified")
                                .style("display", "none");
                            active_modified = false;
                            d3.select("#formulaeList")
                                .selectAll("a")
                                .on("click", formulaClickHandler)
                                .classed("disabled", false);
                        }
                    }
                    request.addAttr(graph_path + "/", JSON.stringify({ formulae: formulae_data }), callback)
                });

            d3.select("#cancelButton")
                .on("click", function () {
                    d3.select("#formulaTextArea")
                        .property("value", formulae_data[active_formula].formula);
                    d3.selectAll(".hide-if-modified")
                        .style("display", "inline");
                    d3.selectAll(".show-if-modified")
                        .style("display", "none");
                    active_modified = false;
                    d3.select("#formulaeList")
                        .selectAll("a")
                        .on("click", formulaClickHandler)
                        .classed("disabled", false);
                });

            function addFormula() {
                let name = prompt("Formula name?", "").trim();
                if (-1 !== formulae_data.findIndex(f => f.id == name)) {
                    alert("Name already exists");
                    return false;
                }
                formulae_data.push({ id: name, formula: "" });
                active_formula = formulae_data.length - 1;
                drawFormulae();
            }

            function deleteFormula() {
                let d = d3.select(this.parentNode).datum();
                if (confirm(`Delete formula ${d.id}?`)){
                    let i = formulae_data.indexOf(d);
                    let new_formulae_data = formulae_data.slice(0);
                    new_formulae_data.splice(i, 1);
                    let callback = function (err, _ret) {
                        if (err) { console.log(err) }
                        else {
                            formulae_data = new_formulae_data;
                            if (old_active >= i) {
                                active_formula = old_active - 1;
                            }
                            drawFormulae();
                        }
                    }
                    request.addAttr(graph_path + "/", JSON.stringify({ formulae: new_formulae_data }), callback)
                }
            }

            function formulaClickHandler(d, i) {
                old_active = active_formula;
                active_formula = i;
                drawFormulae();

            }
            function drawFormulae() {
                d3.select("#formulaeList")
                    .selectAll("a")
                    .remove();
                let list = d3.select("#formulaeList")
                    .selectAll("a")
                    .data(formulae_data);
                list.enter()
                    .append("a")
                    .classed("list-group-item", true)
                    .classed("active", (d, i) => i === active_formula)
                    .on("click", formulaClickHandler)
                    .text(function (d, _i) { return d.id })
                    .append("span")
                    //.insert("span",":first-child")
                    .classed("glyphicon", true)
                    .classed("pull-right", true)
                    .classed("glyphicon-trash", true)
                    .on("click", deleteFormula);

                if (active_formula !== -1) {
                    d3.select("#formulaTextArea")
                        .property("value", formulae_data[active_formula].formula);
                }
                else {
                    d3.select("#formulaTextArea")
                        .property("value", "");
                }
                // list.exit()
                //     .remove();
            }

            this.update = function update(path, formulae) {
                graph_path = path;
                formulae_data = formulae;
                active_formula = (formulae.length > 0) ? 0 : -1;
                active_modified = false;
                drawFormulae();
                d3.selectAll(".hide-if-modified")
                    .style("display", "inline");
                d3.selectAll(".show-if-modified")
                    .style("display", "none");
            };

        }
    });
	