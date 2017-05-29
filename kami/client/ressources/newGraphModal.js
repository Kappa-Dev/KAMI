define([
    "ressources/d3/d3.js"
],
    function (d3) {

        //Interface allowing to define relations between nodes of different graphs
        return function newGraphModal(fatherElem, modalId, dispatch, factory) {
            let formSelectedType = null;
            let children_types = null;
            let selected_nodes = null;
            let parent_path = null;
            let new_graph_form = fatherElem
                .append("div")
                .attr("id", modalId)
                .classed("modal", true)
                .classed("fade", true)
                .classed("row", true)
                .html(`
                    <div class="modal-content">
                        <div class="modal-header">
                            <button type="button" class="close" data-dismiss="modal">&times;</button>
                            <h4 class="modal-title">New child</h4>
                        </div>
                        <div class="modal-body row">
                            <div class="col-sm-6"><div id="typesList" class="list-group"></div></div>
                            <div class="col-sm-6"><textarea id="newGraphTextArea" rows="1"></textarea></div>
                        </div>
                        <div class="modal-footer">
                            <button id="newGraphSubmit" type="button" class="btn btn-default">Create Graph</button>
                        </div>
                    </div>
                `);

            new_graph_form.select("#newGraphSubmit")
                .on("click", newChild);

            this.update = function (path, types, nodes) {
                parent_path = path;
                children_types = types;
                selected_nodes = nodes;
                drawNewGraphForm(0);
                $('#' + modalId).modal({ backdrop: 'static', keyboard: false });
            };

            function drawNewGraphForm(selectedType) {
                if (selectedType !== undefined) {
                    formSelectedType = selectedType;
                }
                new_graph_form.select("#typesList").selectAll("a").remove();
                let list = new_graph_form.select("#typesList").selectAll("a")
                    .data(children_types);
                list.enter()
                    .append("a")
                    .classed("list-group-item", true)
                    .classed("active", (d, i) => i === formSelectedType)
                    .classed("disabled", d => d === "rule" && selected_nodes === null)
                    .on("click", (d, i) => {
                        if (d !== "rule" || selected_nodes !== null)
                        { formClickOnTypeHandler(i) }
                    })
                    .text(d => d);
                new_graph_form.select("#newGraphSubmit")
                    .text("Create " + children_types[formSelectedType]);
            }

            function formClickOnTypeHandler(i) {
                formSelectedType = i;
                drawNewGraphForm();
            }

            function newChild() {
                let name = new_graph_form.select("#newGraphTextArea")
                    .property("value");
                if (!name) { return 0 }
                let type = children_types[formSelectedType];
                if (type !== "rule") {
                    if (selected_nodes === null) {
                        factory.promAddGraph(parent_path + "/" + name + "/")
                            .then(factory.promAddAttr(parent_path + "/" + name + "/", JSON.stringify({ "type": type })))
                            .then(dispatch.call("hieUpdate", this, parent_path, type));
                    }
                    else {
                        factory.promNewGraphFromNodes(parent_path, name, selected_nodes)
                            .then(factory.promAddAttr(parent_path + "/" + name + "/", JSON.stringify({ "type": type })))
                            .then(dispatch.call("hieUpdate", this, parent_path, type));
                    }
                }
                else {
                    if (selected_nodes === null) {
                        console.log("selected_node is null should not happen");
                    }
                    else {
                        factory.promChildRuleFromNodes(parent_path, name, selected_nodes)
                            .then(dispatch.call("hieUpdate", this, parent_path, type));
                    }
                }
                $("#" + modalId + " .close").click();

            }
        }
    });
	