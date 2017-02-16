define([
    "ressources/kamiRequestFactory.js"

], function (kamiFactory) {
    return function InterractiveGraph(dispatch, url) {
        var kamiRequest = new kamiFactory(url);

        /*
        creates loci, bnd and brk nodes if shift is pressed when linking two components
        callback updates the graph if operation is successful
        */
        this.shiftLeftDragEndHandler = function (g_id, d1, d2) {
            let components = new Set(["agent", "region"])
            if (components.has(d1.type) && components.has(d2.type)) {
                let callback = function(err, ret){
                    if(!err){
                        dispatch.call("graphUpdate", this, g_id, true)
                    }
                };
                kamiRequest.linkComponents(g_id, d1.id, d2.id, callback);
            }
        };

    };
});
