define([
    "ressources/d3/d3.js"
],
    function (d3) {

        //Interface allowing to define relations between nodes of different graphs
        return function formulaResult(fatherElem, modalId) {
            let modal = fatherElem
                .append("div")
                .attr("id", modalId)
                .classed("modal", true)
                .classed("fade", true)
                .html(`
                    <div class="modal-content">
                        <div class="modal-header">
                            <button type="button" class="close hide-if-modified" data-dismiss="modal">&times;</button>
                            <h4 class="modal-title">Results</h4>
                        </div>
                        <div class="modal-body" id="responsesDiv">
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-default" data-dismiss="modal">Close</button>
                        </div>
                    </div>
                `);

            this.update = function update(results) {
                let list = d3.select("#responsesDiv");
                list.selectAll("div").remove();
                for (let graphName of Object.keys(results)){
                    for (let formulaName of Object.keys(results[graphName])){
                        let wrongNodes = results[graphName][formulaName];
                        if (wrongNodes === "[]"){
                            list.append("div")
                                .classed("panel", true)
                                .classed("panel-success", true)
                                .append("div")
                                .classed("panel-heading", true)
                                .html(graphName + " : " + formulaName)
                        }
                        else if (wrongNodes.charAt(0) === '[') {
                            let pan = list.append("div")
                                .classed("panel", true)
                                .classed("panel-danger", true);
                            pan.append("div")
                                .classed("panel-heading", true)
                                .html(graphName + " : " + formulaName);
                            pan.append("div")
                                .classed("panel-body", true)
                                .html(wrongNodes);

                        }
                        else{
                            let pan = list.append("div")
                                .classed("panel", true)
                                .classed("panel-warning", true);
                            pan.append("div")
                                .classed("panel-heading", true)
                                .html(graphName + " : " + formulaName);
                            pan.append("div")
                                .classed("panel-body", true)
                                .html(wrongNodes);
                        }

                    }
                }

            };

        }
    });
	