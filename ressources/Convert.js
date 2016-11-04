define([],function(){return {
	absPath : function absPath(p){
		var path = p.concat();
		path[0]="";
		path.push("");
		return path.join("/");	
	}
}});