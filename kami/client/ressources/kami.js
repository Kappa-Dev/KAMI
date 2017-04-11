define([
    "ressources/kamiRequestFactory.js",
    "ressources/requestFactory.js",
    "ressources/IGraphUtils.js"

], function (kamiFactory, requestFactory, iGraphUtils) {
    return function Kami(dispatch, url) {
        var kamiRequest = new kamiFactory(url);
        var factory = new requestFactory(url)
        var graphUtils = new iGraphUtils(dispatch, factory);

        /*
        creates loci, bnd and brk nodes if shift is pressed when linking two components
        callback updates the graph if operation is successful
        */
        this.shiftLeftDragEndHandler = function (g_id, d1, d2) {
            let components = new Set(["agent", "region"])
            if (components.has(d1.type) && components.has(d2.type)) {
                let callback = function(err, _ret){
                    if(!err){
                        dispatch.call("graphUpdate", this, g_id, true)
                    }
                };
                kamiRequest.linkComponents(g_id, d1.id, d2.id, callback);
            }
        };

		this.kamiAncestors = function(path){
			var path2 = path.split("/");
			path2 = path2.slice(3);
			var degree = path2.length;
            return factory.promAncestors(path, degree);
		};



    };
});
