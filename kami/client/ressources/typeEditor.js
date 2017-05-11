define([
    "ressources/d3/d3.js"
],
    function (d3) {

        //Interface allowing to define relations between nodes of different graphs
        return function typesEditor(fatherElem, modalId, dispatch, request) {
            let typesDict = {}
            let graph_path = "";
            let node_id = "";
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
                            <h4 class="modal-title">Types</h4>
                        </div>
                        <div class="modal-body row">
                            <div class="col-sm-12">
                                <form id="typesForm" class="form-horizontal">
                                </form>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button id="saveButton" type="button" class="show-if-modified btn btn-default">Save</button>
                            <button id="cancelButton" type="button" class="show-if-modified btn btn-default">Cancel</button>
                        </div>
                    </div>
                `);

            // modal.select("#newFormulaButton")
            //   .on("click", addFormula);

            // modal.select("#formulaTextArea")  
            //   .on("input", function(){
            //         if (!active_modified && active_formula !== -1) {
            //             active_modified = true;
            //             modal.selectAll(".hide-if-modified")
            //                 .style("display", "none");
            //             modal.selectAll(".show-if-modified")
            //                 .style("display", "inline");
            //             modal.select("#formulaeList")
            //                 .selectAll("a")
            //                 .on("click", null)
            //                 .classed("disabled", true);

            //         }
            //     });

            function drawTypes() {
                let typesList = Object.keys(typesDict).reduce(
                    function (acc, typingGraph) {
                        acc.push({
                            "typing_graph": typingGraph,
                            "type": typesDict[typingGraph]
                        });
                        return acc
                    }
                    , []);

                modal.select("#typesForm")
                    .selectAll(".formTypeField")
                    .remove();

                let fieldList = modal.select("#typesForm")
                    .selectAll(".formTypeField")
                    .data(typesList);

                fieldList = fieldList.enter()
                    .append("div")
                    .classed("formTypeField", true)
                    .classed("form-group", true);
                fieldList.append("label")
                    .classed("control-label", true)
                    .attr("for", d => {console.log(d);return d.typing_graph})
                    .text(d => d.typing_graph);
                fieldList.append("input")
                    .classed("form-control", true)
                    .attr("id", d => d.typing_graph)
                    .attr("type", "text")
                    .property("value", d => d.typing_graph);
            }

            this.update = function update(path, nodeId, types) {
                console.log(types)
                graph_path = path;
                node_id = nodeId;
                typesDict = types;
                drawTypes();
            }

        }
    });
	