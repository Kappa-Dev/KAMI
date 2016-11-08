define([],function(){return {
union:function(s1,s2){//union of two sets view as lists : O(n) where n = max list size
	if(!fullListCheck(s1) && !fullListCheck(s2)) return [];
	//else if(!fullListCheck(s1)) return s2.concat();
	//else if(!fullListCheck(s2)) return s1.concat();
	var obj1={};
	if(fullListCheck(s1)){
		for(var i=0;i<s1.length;i++)
			obj1[s1[i]]=1;
	}if(fullListCheck(s2)){
		for(var i=0;i<s2.length;i++)
			obj1[s2[i]]=1;
	}
	return Object.keys(obj1);
},
multiUnion:function(s_l){//union over multi sets : O(n²) where n = max list size
	if(!fullListCheck(s_l))
		return [];
	var obj1={};
	for(var i=0;i<s_l.length;i++){
		if(fullListCheck(s_l[i])){
			for(var j=0;j<s_l[i].length;j++)
				obj1[s_l[i][j]]=1;
		}
	}
	return Object.keys(obj1);
},
intersection:function(s1,s2){//intersection of two sets see as lists : O(n) where n = max list size
	var obj1={};
	if(!fullListCheck(s1) || !fullListCheck(s2)) return [];
	for(var i=0;i<s1.length;i++)
		obj1[s1[i]]=0;
	for(var i=0;i<s2.length;i++){
		if(typeof obj1[s2[i]]!='undefined' && obj1[s2[i]]==0)
			obj1[s2[i]]=1;
	}
	var keys=Object.keys(obj1);
	var ret=[];
	for(var i=0;i<keys.length;i++){
		if(obj1[keys[i]]==1)
			ret.push(keys[i]);
	}
	return ret;
},
multiIntersection:function(s_l){//intersection over multi sets : O(n²) where n = max list size
	var obj1={};
	if(!fullListCheck(s_l)) return [];
	var sll=s_l.length;
	for(var i=0;i<sll;i++){
		if(!fullListCheck(s_l[i])) return [];
		var obj2={};
		for(var j=0;j<s_l[i].length;j++){
			if(typeof obj1[s_l[i][j]] =='undefined') obj1[s_l[i][j]]=0;
			if(typeof obj2[s_l[i][j]]=='undefined'){
				obj1[s_l[i][j]]++;
				obj2[s_l[i][j]]=0;
			}
		}
	}
	var keys=Object.keys(obj1);
	var ret=[];
	for(var i=0;i<keys.length;i++){
		if(obj1[keys[i]]==sll)
			ret.push(keys[i]);
	}
	return ret;
},
rmElements:function(s1,s2){//remove all element from the intersection of s2/s1 in s1 : O(n) where n = max list size
	var obj_1={};
	if(!fullListCheck(s1))return [];
	if(!fullListCheck(s2))return union(s1,null);
	for(var i=0;i<s1.length;i++)
		obj_1[s1[i]]=1;
	for(var i=0;i<s2.length;i++){
		if(typeof obj_1[s2[i]] != 'undefined')
		obj_1[s2[i]]=0;
	}
	var obj_k=Object.keys(obj_1);
	var ret=[];
	for(var i=0;i<obj_k.length;i++){
		if(obj_1[obj_k[i]]==1)
			ret.push(obj_k[i]);
	}
	return ret;
},
fullListCheck:function(l){//verify if a list is defined and not empty : O(1)
	return typeof l!='undefined' && l!=null && l.length>0;
},
min:function(a,b){//-1 code for infiny, [null,null] code for empty set
	if(a==-1 || b==-1)return a+b+1;
	if(a==null || b==null) return null;
	return a < b ? a : b;
},
max:function(a,b){//same as min, but for max
	if(a==-1 || b==-1) return -1;
	if(a==null || b==null) return a+b;
	return a > b ? a : b;
}
}});