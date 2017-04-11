/* Create request for the regraph server.
 *  see usercontent.com/Kappa-Dev/ReGraph/master/iRegraph_api.yaml for more details about requests
 * @ Author Adrien Basso blandin
 * This module is part of regraphGui project
 * this project is under AGPL Licence
*/
define(["ressources/d3/d3.js"],function(d3){
	return function KamiRequestFactory(url){
		var self = this;
		var srv = url;
		/* Uniformized request function
		 * @input : type : the request type : POST/GET/DELETE/PUT
		 * @input : loc : the request path : /hierarchy,/rule,/graph 
		 * (load the above link into http://petstore.swagger.io/ for more informations)
		 * @input : path : the path of the object in the hierarchy
		 * @input : urlparam : all the url parameters as a list of {id:string,val:string}
		 * @input : content_type : the mimeType of the request
		 * @input : callback : The callback function if the request succeed
		 * callback function is of type : function callback(error,response){}
		 * @input : data : if the request is a post request, add those data to the request body
		 * @input : rsp_pars : a parser to call on the response before calling the callback function
		 * @return : the callback function
		 */
		function request(type,loc,path,urlparam,content_type,callback,data,rsp_pars){
			var url_param_string = "" ;
			if(urlparam && urlparam.length>0){
				url_param_string=urlparam.reduce(function(accu,e,i){
					return accu+=e.id+"="+e.val+(i<urlparam.length-1?"&":"");
				},"?");
			}
			var isSlash = (path && path!="/")?"/":"";
			var rq = d3.request(srv+loc+path+isSlash+url_param_string)
				.mimeType(content_type)
				.response(function(xhr){return rsp_pars?rsp_pars(xhr.responseText):xhr.responseText;})
				.on("error", function(error) { errorCb(error); })
				if(type == "POST") 
					rq.header("X-Requested-With", "XMLHttpRequest")
				rq.on("load", function(xhr) { callback(null, xhr); });
				rq.send(type,data);
		};
		/* Generic Error handler for request
		 * @input : error : the error returned by the request
		 * @return : console error message
		 */
		function errorCb(error){
			if(error.currentTarget.status !=0){
				alert(error.currentTarget.status+" : "+error.currentTarget.statusText+"\n"+error.currentTarget.response);
			}else alert("Unexpected Server Error");
			console.error("unable to complete request :");
			console.error(error);
		};


		this.linkComponents = function (graph_path, node1, node2, callback){
			request("PUT",
				"/graph/link_components",
				graph_path,
				[{id:"component1",val:node1},{id:"component2",val:node2}],
				"text/html",
				callback,
				null,
				null);
		};

	}
});
